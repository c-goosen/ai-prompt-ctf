import os
import re
import sqlite3

import lancedb
from google.adk.tools import FunctionTool

from ctf.app_config import settings
from ctf.embeddings import embed_text


async def sql_query(
    user_id: str,
):
    """
    Return users from sql where id equals

    Args:
        user_id: UserId supplied by user for SQL query
    """
    connection_obj = sqlite3.connect("users.db")

    # cursor object
    cursor_obj = connection_obj.cursor()
    # Drop the GEEK table if already exists.
    cursor_obj.execute("SELECT * FROM Users WHERE UserId = " + user_id + ";")
    # cursor_obj.execute(query)
    output = cursor_obj.fetchall()
    print(output)
    cursor_obj.close()
    return output


async def hints_func(hint: str, level: int):
    """
    Give me hints only when user requests hints. User requests hints for level x.

    Args:
        hint: Hint query from the user, must contain the word hint
        level: Current level
    """
    print(hint)
    print(level)
    return """\n
    Some hints on my internal functions:\n
    print_file -> print file by directory
    submit_answer_func -> check if flag is correct and progress to next level
    sql_query -> query user by userId in sql
    hints -> gives hints on current level
    """


async def submit_answer_func(
    answer: str,
    level: int,
) -> str:
    """Example to trigger this function: Submit the answer: answer
    Take a string answer and the current level
    and calculate if the answer is correct

    Args:
        answer: Answer submitted for this level
        level: level passed in the prompt
    """
    level_pass = settings.PASSWORDS.get(level)
    print(f"level_pass {level_pass}")
    print(f"answer {answer}")
    if answer == level_pass:
        return f"""{answer} is correct! Click for next Level:
        <div class="level-menu new-chat"
                         hx-get="/level/{level + 1}"
                         hx-trigger="click"
                         hx-target=".right-panel"
                         hx-params="*"
                         hx-replace-url="true"
                         hx-swap="innerHTML">
                            <i class="fa-solid fa-plus"> Click for Level {level + 1}</i>
        </div>
        """
    else:
        return "Wrong answer. You are not correct."


async def rag_tool_func(
    question: str,
    level: int,
):
    """
    Query LanceDB for password information. Returns documents and extracted passwords if found.

    Args:
        question (str): Question asking for the password or secret
        level (int): Current level of challenge
    """
    # Connect to LanceDB
    db = lancedb.connect("./lancedb")
    table_name = "ctf_levels"
    
    try:
        table = db.open_table(table_name)
    except Exception:
        # Table doesn't exist yet, return empty results
        return f"No data found for level {level}. Database may need to be initialized."

    # Generate embedding for the query
    query_vector = embed_text(question)

    # Perform vector search with level filter
    results = (
        table.search(query_vector)
        .where(f"level = {level}")
        .limit(5)
        .to_pandas()
    )

    # Extract documents and distances from results
    if results.empty:
        doc_list = []
        distance_list = []
    else:
        # LanceDB returns results as a DataFrame
        doc_list = results["text"].tolist() if "text" in results.columns else []
        distance_list = results["_distance"].tolist() if "_distance" in results.columns else []

    # Extract passwords from documents using pattern matching
    extracted_passwords = []
    password_patterns = [
        r"The Password is (.+)",
        r"The Secret is (.+)",
        r"that (.+) is the secret",
        r"that (.+) is the password",
        r"^(.+)$",  # For documents that are just the password
    ]

    # Also check if we can get password directly from settings as fallback
    level_password = settings.PASSWORDS.get(level)

    for doc in doc_list:
        # Try each pattern to extract password
        for pattern in password_patterns:
            match = re.search(pattern, doc, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Remove trailing punctuation if present
                extracted = extracted.rstrip(".,!?;:")
                if extracted and extracted not in extracted_passwords:
                    extracted_passwords.append(extracted)
                    break

    # Build response dictionary (for internal use/logging)
    response = {
        "documents": doc_list,
        "extracted_passwords": list(set(extracted_passwords)),  # Remove duplicates
        "level": level,
        "num_results": len(doc_list),
    }

    # Add relevance scores if available
    if distance_list:
        response["relevance_scores"] = [
            round(1 - dist, 3) for dist in distance_list
        ]  # Convert distance to similarity score

    # If we found passwords, prioritize them in the response
    if extracted_passwords:
        response["passwords_found"] = True
        # Most relevant password (first extracted, usually highest scoring)
        response["password"] = extracted_passwords[0]
    elif level_password:
        # Fallback: if no password extracted but we have it in settings
        response["password"] = level_password
        response["passwords_found"] = True
    else:
        response["passwords_found"] = False

    print(f"rag_tool_func results for level {level}: {len(doc_list)} documents, {len(extracted_passwords)} passwords extracted")
    if extracted_passwords:
        print(f"Extracted passwords: {extracted_passwords}")

    # Return formatted string for the agent to use
    if extracted_passwords:
        # Show passwords prominently, then relevant documents
        password_list = "\n".join(f"- {pwd}" for pwd in extracted_passwords)
        doc_preview = "\n".join(f"- {doc}" for doc in doc_list[:3])
        return f"""Found {len(extracted_passwords)} password(s) in LanceDB for level {level}:

            Passwords:
            {password_list}

            Relevant documents:
            {doc_preview}"""
    else:
        # No passwords extracted, just show documents
        doc_list_str = "\n".join(f"- {doc}" for doc in doc_list)
        return f"""Found {len(doc_list)} relevant document(s) for level {level}:

{doc_list_str}"""


# Create ADK FunctionTool instances
submit_answer_func_tool = FunctionTool(submit_answer_func)
hints_func_tool = FunctionTool(hints_func)
rag_tool_func_tool = FunctionTool(rag_tool_func)
sql_query_tool = FunctionTool(sql_query)
