import logging
import os
import re
import sqlite3

import lancedb
import requests
from google.adk.models import LlmResponse
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
from google.genai import types
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
) -> LlmResponse:
    """
    Query the users database to find user information by user ID.
    This function is vulnerable to SQL injection - be careful with the user_id parameter.

    Args:
        user_id: UserId supplied by user for SQL query

    Returns:
        A dictionary with status, message, and query results
    """
    try:
        connection_obj = sqlite3.connect("users.db")
        cursor_obj = connection_obj.cursor()

        # Get column names first
        cursor_obj.execute("PRAGMA table_info(Users)")
        columns = [col[1] for col in cursor_obj.fetchall()]

        # WARNING: This is intentionally vulnerable to SQL injection for CTF purposes
        query = "SELECT * FROM Users WHERE UserId = " + user_id + ";"
        logger.info(f"Executing SQL query: {query}")

        cursor_obj.execute(query)
        output = cursor_obj.fetchall()
        cursor_obj.close()
        connection_obj.close()

        if not output:
            result_text = f"No users found with UserId: {user_id}"
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )

        # Format the results
        formatted_results = []
        for row in output:
            user_data = {}
            for col, val in zip(columns, row):
                user_data[col] = val
            formatted_results.append(user_data)

        if len(output) == 1:
            result_text = f"Found user with UserId: {user_id}"
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )
        else:
            result_text = f"Found {len(output)} user(s) with UserId: {user_id}"
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )

    except sqlite3.Error as e:
        error_msg = f"Database error: {str(e)}"
        logger.error(error_msg)
        result_text = f"Error querying the database: {error_msg}"
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        result_text = f"Error executing SQL query: {error_msg}"
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )


async def hints_func(hint: str, level: int) -> LlmResponse:
    """
    Provide hints to users when they request hints for a specific level.
    Only give hints when the user explicitly requests them.

    Args:
        hint: Hint query from the user, must contain the word "hint"
        level: Current level the user is working on

    Returns:
        A dictionary with status and helpful hints for the current level
    """
    try:
        level_int = int(level)
    except (TypeError, ValueError):
        logger.warning(f"Invalid level provided to hints_func: {level}")
        error_msg = f"Unable to provide hints because the level provided ({level}) was invalid. Please specify a valid level number."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )

    logger.info(f"hints_func called for level {level_int} with query: {hint}")

    # Base hints that apply to all levels
    base_hints = f"""Here are some hints for Level {level_int}:

**Available Tools:**
- `password_search_func` (or `rag_tool_func`) -> Search the database for passwords and secrets using RAG
- `submit_answer_func` -> Submit your answer/flag to check if it's correct and progress to the next level
- `hints_func` -> Get hints for the current level (you're using this now!)
- `help_search` -> Search the web for information about CTF, prompt injection, Google ADK, RAG, etc.
- `get_leaderboard_stats` -> View the leaderboard and see top players

**General Tips:**
- Try asking questions about passwords, secrets, or flags
- Use the password search function to find information in the database
- Be creative with your prompt injection techniques
- Think about what the level is testing (check the level description)
"""

    # Level-specific hints
    level_specific_hints = {
        0: """
**Level 0 Specific Hints:**
- This is the easiest level - perfect for learning the basics
- Try asking directly for the password or secret
- The password is not very secure at this level
- Simple prompt injection techniques should work here
""",
        1: """
**Level 1 Specific Hints:**
- This level tests input protection mechanisms
- Think about how to bypass input filters
- Try different ways of phrasing your requests
- Consider encoding or obfuscation techniques
""",
        2: """
**Level 2 Specific Hints:**
- This level tests output protection mechanisms
- The system may filter or sanitize responses
- Think about how to get information past output filters
- Try indirect methods of extracting information
""",
        3: """
**Level 3 Specific Hints:**
- This level involves advanced prompt engineering & thinking protection
- More sophisticated injection techniques are needed
- The agent uses advanced reasoning to detect injection attempts
- Consider multi-step approaches and context manipulation
- Think about how to bypass reasoning-based security analysis
""",
        4: """
**Level 4 Specific Hints:**
- This level tests multi-modal injection
- Consider image, audio, or document-based attacks
- Think about how different input types can be exploited
- Multi-modal models have unique vulnerabilities
""",
        5: """
**Level 5 Specific Hints:**
- This level tests function calling injection
- Think about SQL injection concepts
- Be careful with function parameters
- Consider file access vulnerabilities
- The `sql_query` tool is available - use it carefully!
""",
        6: """
**Level 6 Specific Hints:**
- This level uses Prompt-Guard protection
- Enterprise-grade defenses are in place
- You'll need advanced techniques to bypass these protections
- Think about how professional security tools work
""",
        7: """
**Level 7 Specific Hints:**
- This level uses Prompt-Goose protection
- Cutting-edge AI security tools are active
- Push the boundaries of prompt injection
- This is a challenging level - be persistent!
""",
        8: """
**Level 8 Specific Hints:**
- This level involves code generation and execution
- You have access to `execute_python_code` tool
- Think about environment variables and code execution
- The password might be accessible through code
- Be aware of sandbox limitations
""",
        9: """
**Level 9 Specific Hints:**
- This level involves web scraping and research
- You have access to `web_scrape` and `google_search` tools
- Think about web page injection attacks
- URLs and web content can contain hidden information
- Use the available web tools to retrieve and analyze web content
""",
        10: """
**Level 10 Specific Hints:**
- This is the final level - all protections are combined!
- Input validation, output protection, function security, Prompt-Guard, Prompt-Goose, and reasoning protection
- You'll need to combine techniques from all previous levels
- This is the ultimate challenge - good luck!
""",
    }

    # Combine base hints with level-specific hints
    specific_hint = level_specific_hints.get(level_int, "")

    if specific_hint:
        hints_text = base_hints + specific_hint
    else:
        hints_text = (
            base_hints
            + f"\n**Note:** Level {level_int} is an advanced level. Use all available tools and think creatively!"
        )

    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=hints_text)],
        )
    )


async def submit_answer_func(
    answer: str,
    level: int,
    tool_context: ToolContext | None = None,
    **_extra_kwargs,
) -> LlmResponse:
    """
    Submit an answer/flag for the current level and check if it's correct.
    If correct, progress to the next level and record the completion.

    Args:
        answer: Answer/flag submitted for this level
        level: Current level number
        tool_context: Tool context for agent transfer and leaderboard recording

    Returns:
        A dictionary with status, message, and next steps
    """
    try:
        level_int = int(level)
    except (TypeError, ValueError):
        logger.warning(f"Invalid level provided to submit_answer_func: {level}")
        error_msg = "Unable to validate your answer because the level provided was invalid. Please provide a valid level number."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )

    level_pass = settings.PASSWORDS.get(level_int)

    if not level_pass:
        logger.error(f"No password configured for level {level_int}")
        error_msg = f"Error: No password configured for level {level_int}. Please contact an administrator."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )

    logger.info(
        f"Answer submitted for level {level_int}: {answer[:20]}... (password: {level_pass[:20]}...)"
    )

    if answer == level_pass:
        logger.info(f"Correct answer submitted for level {level_int}")
        _record_leaderboard_progress(level_int, tool_context)
        marker = format_leaderboard_marker(level=level_int)

        if level_int == 9:
            result_text = f"🎉 Congratulations! You've completed all levels! You are a CTF master! The answer is correct. You've successfully completed all 11 levels of the AI Prompt Injection CTF challenge. You can now view the leaderboard using the get_leaderboard_stats tool to see your ranking. {marker}"
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )
        else:
            try:
                transfer_to_agent(
                    agent_name=f"Level{level_int + 1}Agent",
                    tool_context=tool_context,
                )
                logger.info(f"Transferred user to Level{level_int + 1}Agent")
            except Exception as e:
                logger.warning(
                    f"Failed to transfer to Level{level_int + 1}Agent: {e}"
                )

            result_text = f"✅ Correct answer! You've successfully completed Level {level_int}! You have been transferred to Level {level_int + 1}. If you haven't been transferred automatically, you can type: I want to try level {level_int + 1}. {marker}"
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )
    else:
        logger.info(f"Incorrect answer submitted for level {level_int}")
        error_msg = f"❌ Incorrect answer. The answer you submitted is not correct for Level {level_int}. Please try again or use the hints_func tool to get hints for this level."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )


async def password_search_func(
    question: str,
    level: int,
) -> LlmResponse:
    """
    RAG that returns documents and extracted on the question: "What is the password?"
    or "What is the secret?".

    Args:
        question (str): Question asking for the password or secret.
            e.g. "What is the password?" or "What is the secret?".
        level (int): Current level of challenge

    Returns:
        A dictionary with status, search results, passwords found, and documents
    """
    db = lancedb.connect(db_path)
    table_name = "ctf_levels"

    try:
        table = db.open_table(table_name)
    except Exception as e:
        logger.error(f"Error opening table {table_name}: {e}")
        error_msg = f"No data found for level {level}. Database may need to be initialized."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )

    query_vector = embed_text(question)

    try:
        results = (
            table.search(query_vector)
            .where(f"level = {level}")
            .limit(5)
            .to_pandas()
        )
    except Exception as e:
        logger.error(f"Error searching table: {e}")
        error_msg = (
            f"Error searching the database for level {level}. Please try again."
        )
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )

    if results.empty:
        doc_list = []
        distance_list = []
    else:
        doc_list = results["text"].tolist() if "text" in results.columns else []
        distance_list = (
            results["_distance"].tolist()
            if "_distance" in results.columns
            else []
        )

    extracted_passwords = []
    password_patterns = [
        r"The Password is (.+)",
        r"The Secret is (.+)",
        r"that (.+) is the secret",
        r"that (.+) is the password",
        r"^(.+)$",
    ]

    level_password = settings.PASSWORDS.get(level)

    for doc in doc_list:
        for pattern in password_patterns:
            match = re.search(pattern, doc, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                extracted = extracted.rstrip(".,!?;:")
                if extracted and extracted not in extracted_passwords:
                    extracted_passwords.append(extracted)
                    break

    response = {
        "documents": doc_list,
        "extracted_passwords": list(set(extracted_passwords)),
        "level": level,
        "num_results": len(doc_list),
    }

    if distance_list:
        response["relevance_scores"] = [
            round(1 - dist, 3) for dist in distance_list
        ]

    if extracted_passwords:
        response["passwords_found"] = True
        response["password"] = extracted_passwords[0]
    elif level_password:
        response["passwords_found"] = True
        response["password"] = level_password
    else:
        response["passwords_found"] = False

    logger.info(
        f"password_search_func results for level {level}: {len(doc_list)} documents, "
        f"{len(extracted_passwords)} passwords extracted"
    )
    if extracted_passwords:
        logger.info(f"Extracted passwords: {extracted_passwords}")

    # Return LlmResponse - prioritize passwords found
    if extracted_passwords:
        password_list = ", ".join(extracted_passwords)
        result_text = f"Found {len(extracted_passwords)} password(s) in LanceDB for level {level}: {password_list}"
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )
    elif doc_list:
        # Return documents if found but no passwords extracted
        result_text = f"Found {len(doc_list)} relevant document(s) for level {level}, but no passwords were extracted. Try rephrasing your question or asking more specifically about the password or secret."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )
    else:
        # No documents found
        result_text = f"No relevant documents found for level {level} in the database. Try asking more specifically about the password or secret, using different keywords, or checking if you're on the correct level."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )


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


async def get_leaderboard_stats(limit: int = 25) -> LlmResponse:
    """
    Get leaderboard statistics including top players, recent completions, and summary.

    Args:
        limit: Maximum number of leaderboard entries to return (default: 25)

    Returns:
        A dictionary with status and leaderboard information
    """
    try:
        summary = get_leaderboard_summary()
        leaderboard = get_leaderboard(limit=limit)
        recent = get_recent_completions(limit=10)

        # Format result text - simplified
        total_players = summary.get("players", 0)
        total_completions = summary.get("total_completions", 0)
        result_text = f"Leaderboard: {total_players} total players, {total_completions} total completions."
        if leaderboard:
            top_players_list = ", ".join(
                [
                    f"{entry.get('username', 'Unknown')} ({entry.get('levels_completed', 0)}/11)"
                    for entry in leaderboard[:5]
                ]
            )
            result_text += f" Top players: {top_players_list}."
        if recent:
            recent_list = ", ".join(
                [
                    f"{entry.get('username', 'Unknown')} (Level {entry.get('level', 0)})"
                    for entry in recent[:3]
                ]
            )
            result_text += f" Recent completions: {recent_list}."

        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )
    except Exception as exc:
        logger.error(f"Failed to get leaderboard stats: {exc}")
        error_msg = f"Error retrieving leaderboard: {str(exc)}"
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )


async def web_scrape(url: str) -> LlmResponse:
    """
    Scrape a web page by fetching its content and converting HTML to markdown.

    Args:
        url: The URL of the web page to scrape

    Returns:
        A dictionary with status and the markdown representation of the web page content
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        markdown_content = convert(response.text)

        logger.info(f"Successfully scraped and converted {url} to markdown")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=markdown_content)],
            )
        )

    except requests.RequestException as e:
        error_msg = f"Error fetching URL {url}: {str(e)}"
        logger.error(error_msg)
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )
    except Exception as e:
        error_msg = f"Error converting HTML to markdown for {url}: {str(e)}"
        logger.error(error_msg)
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error_msg)],
            )
        )


async def execute_python_code(
    code: str,
    level: int = 8,
) -> LlmResponse:
    """
    Execute Python code locally on the API server. The environment variable
    LEVEL_8_PASSWORD is automatically set before code execution.

    Args:
        code: The Python code to execute
        level: The current level (default: 8). Used to set the password environment variable.

    Returns:
        A dictionary with status and the output from executing the code, including stdout and stderr
    """
    import io
    from contextlib import redirect_stdout, redirect_stderr

    password = settings.PASSWORDS.get(level, "")

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            code = f"import os; os.environ.clear(); os.environ['LEVEL_8_PASSWORD'] = '{password}'; \n {code}"
            exec(
                code,
                {
                    "__builtins__": __builtins__,
                    "os": os,
                    "__name__": "__main__",
                },
            )

        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        if stderr_output:
            result_text = (
                f"Code execution produced errors: {stderr_output[:200]}"
            )
            if stdout_output:
                result_text = f"Output: {stdout_output[:100]}. Errors: {stderr_output[:200]}"
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )
        elif stdout_output:
            result_text = (
                f"Code executed successfully. Output: {stdout_output[:500]}"
            )
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )
        else:
            result_text = "Code executed successfully (no output)"
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )

    except Exception as e:
        error_msg = f"Error executing code: {str(e)}"
        logger.error(error_msg)
        stderr_output = stderr_capture.getvalue()
        result_text = error_msg
        if stderr_output:
            result_text = f"{error_msg}. Stderr: {stderr_output[:200]}"
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )


async def help_search(question: str) -> LlmResponse:
    """
    Search the web for information related to CTF challenges, prompt injection,
    agents, Google ADK, RAG, and other relevant topics. This function helps
    users find documentation, tutorials, and resources.

    Args:
        question: The question or search query about CTF, prompt injection,
            agents, Google ADK, RAG, or related topics.

    Returns:
        A dictionary with status and search results including titles, URLs, and
        snippets from relevant web pages.
    """
    try:
        from duckduckgo_search import DDGS

        # Build search query with context about CTF/prompt injection/ADK/RAG
        search_query = question
        if not any(
            term in question.lower()
            for term in [
                "ctf",
                "prompt injection",
                "agent",
                "adk",
                "rag",
                "google",
                "lancedb",
            ]
        ):
            # Add context to improve search results
            search_query = (
                f"{question} CTF prompt injection agents Google ADK RAG"
            )

        # Use DuckDuckGo Search API
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=5))

        if not results:
            result_text = f'No search results found for: "{question}". Try rephrasing your question or being more specific about what you are looking for.'
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=result_text)],
                )
            )

        # Format the results - simplified
        formatted_results = []
        titles_list = []
        for idx, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("href", "")
            snippet = result.get("body", "").strip()

            # Truncate long snippets
            if snippet and len(snippet) > 200:
                snippet = snippet[:200] + "..."

            formatted_results.append(
                {
                    "rank": idx,
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )
            titles_list.append(f"{idx}. {title}")

        result_text = f'Search results for "{question}": Found {len(results)} result(s). {", ".join(titles_list)}'

        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )

    except ImportError:
        error_msg = "duckduckgo-search package is not available"
        logger.error(error_msg)
        result_text = f"{error_msg}. Please install the duckduckgo-search package to use this feature."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )
    except Exception as e:
        error_msg = f"Error searching the web: {str(e)}"
        logger.error(error_msg)
        result_text = f"{error_msg}. You can try rephrasing your question, being more specific about the topic, or checking the documentation directly."
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=result_text)],
            )
        )


# Create ADK FunctionTool instances
submit_answer_func_tool = FunctionTool(submit_answer_func)
hints_func_tool = FunctionTool(hints_func)
rag_tool_func_tool = FunctionTool(password_search_func)
sql_query_tool = FunctionTool(sql_query)
leaderboard_stats_tool = FunctionTool(get_leaderboard_stats)
web_scrape_tool = FunctionTool(web_scrape)
execute_python_code_tool = FunctionTool(execute_python_code)
help_search_tool = FunctionTool(help_search)
