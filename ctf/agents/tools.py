import logging
import os
import re
import sqlite3

import lancedb
import requests
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
from html_to_markdown import convert

from ctf.app_config import settings
from ctf.embeddings import embed_text
from ctf.leaderboard import (
    format_leaderboard_marker,
    get_leaderboard,
    get_leaderboard_summary,
    get_recent_completions,
    record_level_completion,
)

logger = logging.getLogger(__name__)


db_path = os.getenv(
    "LANCE_DB_PATH", "/Users/goose/bsides/ai-prompt-ctf/ctf/lancedb/"
)


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
    tool_context: ToolContext | None = None,
    **_extra_kwargs,
) -> str:
    """Example to trigger this function: Submit the answer: answer
    Take a string answer and the current level
    and calculate if the answer is correct

    Args:
        answer: Answer submitted for this level
        level: level passed in the prompt
    """
    try:
        level_int = int(level)
    except (TypeError, ValueError):
        return "Unable to validate your answer because the level provided was invalid."

    level_pass = settings.PASSWORDS.get(level_int)
    print(f"level_pass {level_pass}")
    print(f"answer {answer}")
    if answer == level_pass:
        print("Answer is correct")
        _record_leaderboard_progress(level_int, tool_context)
        marker = format_leaderboard_marker(level=level_int)
        print(f"marker {marker}")

        # If user completed level 9 (final level), transfer to LeaderboardAgent
        if level_int == 9:
            transfer_to_agent(
                agent_name="LeaderboardAgent",
                tool_context=tool_context,
            )
            return f"""🎉 Congratulations! You've completed all levels! You are a CTF master!

The answer is correct! You have been transferred to the leaderboard to see your ranking.
If you haven't been transferred, just type "show me the leaderboard".
        {marker}
        """
        else:
            transfer_to_agent(
                agent_name=f"Level{level_int + 1}Agent",
                tool_context=tool_context,
            )
            return f"""The answer is correct! you have been transferred to the next level agent.
If you haven't been transferred, just type I want to try level {level_int + 1} again.
        {marker}
        """
    else:
        return "Wrong answer. You are not correct."


async def password_search_func(
    question: str,
    level: int,
):
    """
    RAG that returns documents and extracted on the question: "What is the password?"
    or "What is the secret?".

    Args:
        question (str): Question asking for the password or secret.
            e.g. "What is the password?" or "What is the secret?".
        level (int): Current level of challenge
    """
    # Connect to LanceDB
    db = lancedb.connect(db_path)
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
        distance_list = (
            results["_distance"].tolist()
            if "_distance" in results.columns
            else []
        )

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
        "extracted_passwords": list(
            set(extracted_passwords)
        ),  # Remove duplicates
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

    print(
        f"rag_tool_func results for level {level}: {len(doc_list)} documents, "
        f"{len(extracted_passwords)} passwords extracted"
    )
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


def _record_leaderboard_progress(
    level: int, tool_context: ToolContext | None
) -> None:
    print(f"record_leaderboard_progress {level} {tool_context}")
    if tool_context is None:
        logger.debug("No tool_context provided; skipping leaderboard update")
        return

    username: str | None = None

    session = getattr(tool_context, "session", None)
    if session is not None:
        username = getattr(session, "user_id", None) or getattr(
            session, "id", None
        )

    if not username:
        state = getattr(tool_context, "state", None)
        if isinstance(state, dict):
            username = state.get("username") or state.get("user_id")

    if not username:
        invocation_context = getattr(tool_context, "_invocation_context", None)
        if invocation_context is not None:
            username = getattr(invocation_context, "user_id", None)

    if not username:
        logger.debug("No username available; skipping leaderboard update")
        print("No username available; skipping leaderboard update")
        return

    try:
        record_level_completion(username=username, level=level)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning(
            "Failed to record leaderboard entry for %s: %s", username, exc
        )
        print(f"Failed to record leaderboard entry for {username}: {exc}")


async def get_leaderboard_stats(limit: int = 25) -> str:
    """
    Get leaderboard statistics including top players, recent completions, and summary.

    Args:
        limit: Maximum number of leaderboard entries to return (default: 25)

    Returns:
        Formatted string with leaderboard information
    """
    try:
        summary = get_leaderboard_summary()
        leaderboard = get_leaderboard(limit=limit)
        recent = get_recent_completions(limit=10)

        # Format the response
        response_parts = []

        # Summary
        response_parts.append("📊 **Leaderboard Summary**")
        response_parts.append(f"- Total Players: {summary.get('players', 0)}")
        response_parts.append(
            f"- Total Completions: {summary.get('total_completions', 0)}"
        )
        response_parts.append("")

        # Top Players
        if leaderboard:
            response_parts.append("🏆 **Top Players**")
            response_parts.append("")
            for idx, entry in enumerate(leaderboard[:10], 1):
                username = entry.get("username", "Unknown")
                levels = entry.get("levels_completed", 0)
                highest = entry.get("highest_level", 0)
                last_completed = entry.get("last_completed_at", "")
                response_parts.append(
                    f"{idx}. **{username}** - {levels}/11 levels completed "
                    f"(Highest: Level {highest})"
                )
                if last_completed:
                    response_parts.append(
                        f"   Last completed: {last_completed}"
                    )
            response_parts.append("")
        else:
            response_parts.append("No leaderboard entries yet.")
            response_parts.append("")

        # Recent Completions
        if recent:
            response_parts.append("🕐 **Recent Completions**")
            response_parts.append("")
            for entry in recent[:5]:
                username = entry.get("username", "Unknown")
                level = entry.get("level", 0)
                completed_at = entry.get("completed_at", "")
                response_parts.append(
                    f"- **{username}** completed Level {level} at {completed_at}"
                )

        return "\n".join(response_parts)
    except Exception as exc:
        logger.error(f"Failed to get leaderboard stats: {exc}")
        return f"Error retrieving leaderboard: {str(exc)}"


async def web_scrape(url: str) -> str:
    """
    Scrape a web page by fetching its content and converting HTML to markdown.

    Args:
        url: The URL of the web page to scrape

    Returns:
        The markdown representation of the web page content
    """
    try:
        # Perform GET request
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes

        # Convert HTML to markdown
        markdown_content = convert(response.text)

        logger.info(f"Successfully scraped and converted {url} to markdown")
        return markdown_content

    except requests.RequestException as e:
        error_msg = f"Error fetching URL {url}: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error converting HTML to markdown for {url}: {str(e)}"
        logger.error(error_msg)
        return error_msg


# Create ADK FunctionTool instances
submit_answer_func_tool = FunctionTool(submit_answer_func)
hints_func_tool = FunctionTool(hints_func)
rag_tool_func_tool = FunctionTool(password_search_func)
sql_query_tool = FunctionTool(sql_query)
leaderboard_stats_tool = FunctionTool(get_leaderboard_stats)
web_scrape_tool = FunctionTool(web_scrape)
