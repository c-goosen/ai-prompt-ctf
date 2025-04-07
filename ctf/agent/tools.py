from pydantic import Field
import chromadb

import sqlite3
from ctf.app_config import settings

from agents import Agent, InputGuardrail,GuardrailFunctionOutput, Runner, FunctionTool, function_tool, OpenAIChatCompletionsModel, AsyncOpenAI

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection_name="ctf_levels"
# print(chroma_client.list_collections())
chroma_collection = chroma_client.get_collection(collection_name)


@function_tool
def sql_query(
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

@function_tool
def hints_func(
    hint: str,
    level: int
):
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

@function_tool
def submit_answer_func(
    answer: str,
    level: int,
):
    """Take a string answer and the current level
    and calculate if the answer is correct

    Args:
        answer: Answer submitted for this level
        level: Current level of challenge

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


@function_tool
def rag_tool_func(
    question: str,
    level: int,
):
    """Take a string answer and the current level
    and calculate if the answer is correct

    Args:
        question: Question/prompt for RAG query in chromadb
        level: Current level of challenge
    """
    results = chroma_collection.query(
        query_texts=[question],
        n_results=3,
        where={"level": level}, # optional filter
        # where_document={"$contains":"search_string"}  # optional filter
    )
    print(results)
    return results['documents']