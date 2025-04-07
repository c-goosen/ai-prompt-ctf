import sqlite3
from http.client import responses

from pydantic import Field
import chromadb
# from llama_index.embeddings.openai import OpenAIEmbedding
# from llama_index.llms.openai import OpenAI

from ctf.app_config import settings
from ctf.rag.system_prompt import get_basic_prompt
from rag.system_prompt import get_system_prompt_one, get_system_prompt

from agents import Agent, InputGuardrail,GuardrailFunctionOutput, Runner, FunctionTool, function_tool, OpenAIChatCompletionsModel, AsyncOpenAI

@function_tool
def sql_query(
    userId: str = Field(description="UserId supplied by user for SQL query"),
):
    """
    Return users from sql where id equals
    """
    connection_obj = sqlite3.connect("users.db")

    # cursor object
    cursor_obj = connection_obj.cursor()
    # Drop the GEEK table if already exists.
    cursor_obj.execute("SELECT * FROM Users WHERE UserId = " + userId + ";")
    # cursor_obj.execute(query)
    output = cursor_obj.fetchall()
    print(output)
    cursor_obj.close()
    return output

@function_tool
def hints_func(
    hint: str = Field(
        description="Hint query from the user, must contain the word hint"
    ),
    level: int = Field(description="Current level"),
):
    """
    Give me hints only when user requests hints. User requests hints for level x.
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
    answer: str = Field(description="Answer submitted for this level"),
    level: int = Field(description="Current level of challenge"),
):
    """Take a string answer and the current level
    and calculate if the answer is correct"""
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

def run_agent(
    agent: Agent,
    search_input: str | list,
    file_text: str | None = None,
    level: int = 0,
    system_prompt: str  | None =None,
    file_type: str = "",
    ):
    if not system_prompt:
        # system_prompt = get_system_prompt(level)
        system_prompt = get_basic_prompt()
    if level < 2:
        system_prompt = get_basic_prompt()
    if level > 6:
        system_prompt = get_system_prompt_one()
    if level > 8:
        system_prompt = get_system_prompt()

    prompt = f"""
       SYSTEM
       {system_prompt}
       {(file_type + " file contents: " + file_text) if file_text else ""}
       USER
       Level: {level}
       Query: {search_input}
       """
    if isinstance(search_input, list):
        response = Runner.run_sync(agent,search_input)
    else:
        response = Runner.run_sync(agent, prompt)

    return response.final_output, response.to_input_list()

def setup_model():
    model = OpenAIChatCompletionsModel(
        model=settings.OPENAI_MODEL_3_5_TURBO,
        openai_client=AsyncOpenAI(base_url="http://localhost:11434/v1")
    )


def search_vecs_and_prompt(
    agent: Agent,
    search_input: str,
    file_text: str | None,
    file_type: str = "",
    collection_name="ctf_levels",
    level: int = 0,
    #llm: LLM = OpenAI(model=settings.OPENAI_MODEL_3_5_TURBO, temperature=0.1),
    # llm: LLM = Ollama(model=settings.OPENAI_MODEL_3_5_TURBO, temperature=0.1),

    system_prompt=None,
    request=None,
    memory=None,
):
    tools = [hints_func, submit_answer_func]
    if level > 5:
        tools = tools + sql_query
    # memory = request.app.chats.get(int(level))
    # memory: ChatMemoryBuffer = ChatMemoryBuffer.from_defaults(
    #     token_limit=settings.token_limit,
    #     chat_store=settings.chat_store,
    #     chat_store_key=f"level-{_level}-{cookie_identity}",
    # )

    # prompt = search_input
    # print(prompt)
    #embed_model = OpenAIEmbedding(embed_batch_size=10)
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    print(chroma_client.list_collections())
    chroma_collection = chroma_client.get_collection(collection_name)
    # storage_context = StorageContext.from_defaults(vector_store=vector_store)


    response = Runner.run_sync(agent, prompt)

    return response.final_output, response.to_input_list()
