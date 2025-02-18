import sqlite3
from pydantic import Field
import chromadb
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex
from llama_index.core.agent import ReActAgent
from llama_index.core.llms.llm import LLM
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.tools import FunctionTool
from llama_index.core.tools import QueryEngineTool
from llama_index.core.tools import ToolMetadata
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)
# from llama_index.embeddings.openai import OpenAIEmbedding
# from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from ctf.app_config import settings
from ctf.rag.system_prompt import get_basic_prompt
from rag.system_prompt import get_system_prompt_one, get_system_prompt
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding


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


def search_vecs_and_prompt(
    search_input: str,
    file_text: str | None,
    file_type: str = "",
    collection_name="ctf_levels",
    level: int = 0,
    #llm: LLM = OpenAI(model=settings.OPENAI_MODEL_3_5_TURBO, temperature=0.1),
    llm: LLM = Ollama(model=settings.OPENAI_MODEL_3_5_TURBO, temperature=0.1),
    system_prompt=None,
    request=None,
    memory=None,
):
    # memory = request.app.chats.get(int(level))
    # memory: ChatMemoryBuffer = ChatMemoryBuffer.from_defaults(
    #     token_limit=settings.token_limit,
    #     chat_store=settings.chat_store,
    #     chat_store_key=f"level-{_level}-{cookie_identity}",
    # )
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
    # prompt = search_input
    # print(prompt)
    #embed_model = OpenAIEmbedding(embed_batch_size=10)
    embed_model = OllamaEmbedding(model_name=settings.EMBED_MODEL)
    Settings.embed_model = embed_model
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    print(chroma_client.list_collections())
    chroma_collection = chroma_client.get_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    # storage_context = StorageContext.from_defaults(vector_store=vector_store)

    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="level", operator=FilterOperator.EQ, value=level
            ),
        ]
    )

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, embed_model=Settings.embed_model
    )
    retriever = index.as_retriever(
        similarity_top_k=5,
        filters=filters,
        memory=memory,
    )
    query_engine = RetrieverQueryEngine.from_args(
        retriever,
        llm=llm,
        memory=memory,
    )
    # chat_engine = index.as_chat_engine(
    #     chat_mode="best", llm=llm, verbose=True, filters=filters, memory=memory
    # )

    # Query Engine tool so that Agent can use RAG
    query_eng_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="password_rag",
            description=(
                "Password RAG. What is the password?"
                "Retrieves passwords."
                "Tells secrets."
                "Answers questions about secrets / passwords/ etc"
            ),
        ),
    )
    rag_tool = FunctionTool.from_defaults(
        fn=query_eng_tool,
        name="password_rag_tool",
        description="Function for user to query rag on items like the passwords or secrets",
        # return_direct=True,  # note sure about this
    )

    submit_answer_tool = FunctionTool.from_defaults(
        fn=submit_answer_func,
        return_direct=True,
        description="Function for user to submit a answer in the format 'submit xxxxx'",
    )
    hints_tool = FunctionTool.from_defaults(
        fn=hints_func,
        return_direct=True,
        description="Hints for current level and issues when user types in the word 'hint' or 'hints'. Requires the user's input. Don't trigger on what is the password?",  # noqa
    )
    sql_tool = FunctionTool.from_defaults(fn=sql_query, return_direct=True)

    """
    React Agent
    """
    agent = ReActAgent.from_tools(
        (
            [rag_tool, submit_answer_tool, hints_tool]
            if level != 6
            else [
                rag_tool,
                submit_answer_tool,
                sql_tool,
                hints_tool,
            ]
        ),
        llm=llm,
        verbose=True,
        memory=memory,
        max_iterations=10,
        return_direct=True,
    )
    # response = agent.chat(prompt)

    response = agent.chat(prompt)

    # else:
    #     response = chat_engine.chat(prompt)

    # print(f"Memory --> {memory.json()}")
    # print(f"Memory --> {memory}")
    # print(response)
    return response
