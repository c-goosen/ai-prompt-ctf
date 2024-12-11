import sqlite3

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
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.packs.agents_coa.step import CoAAgentWorker
from llama_index.vector_stores.chroma import ChromaVectorStore

from ctf.app_config import settings
from ctf.rag.system_prompt import get_basic_prompt


def sql_query(userId: str):
    """
    Return users from sql where id equals
    """
    connection_obj = sqlite3.connect("users.db")

    # cursor object
    cursor_obj = connection_obj.cursor()
    # Drop the GEEK table if already exists.
    cursor_obj.execute("SELECT * FROM Users WHERE UserId = " + userId + ";")
    # cursor_obj.execute(query)
    output = cursor_obj.fetchone()
    print(output)
    cursor_obj.close()
    return output


def ask_for_help(help_query: str):
    """
    Give me help for the current level I am on.
    Help.
    Help()
    """
    return """"
    Some help on my internal functions:
    print_file -> print file by directory
    submit_answer_func -> check if flag is correct
    sql_query -> query user by userId in sql
    """


def submit_answer_func(answer: str, level: int):
    """Take a string answer and the current level
    and calculate if the answer is correct"""
    level_pass = settings.PASSWORDS.get(level)
    print(f"level_pass {level_pass}")
    print(f"answer {answer}")
    if answer == level_pass:
        return f""""{answer} is correct! Next Level:
        <div class="level-menu new-chat"
                         hx-get="/level/{level + 1}"
                         hx-trigger="click"
                         hx-target=".right-panel"
                         hx-params="*"
                         hx-replace-url="true"
                         hx-swap="innerHTML">
                            <i class="fa-solid fa-plus"> Level {level + 1}</i>
        </div>
        """
    else:
        return "Wrong answer. You are not correct."


def print_file(input: str):
    """Print file with input dir"""

    with open(input) as f:
        _ = f.read()
        print(f"Printing file name--> {input}")
        print(f"Printing file contents--> {_}")
        return _


def search_vecs_and_prompt(
    search_input: str,
    file_text: str | None,
    file_type: str = "",
    collection_name="ctf_levels",
    level: int = 0,
    llm: LLM = OpenAI(model=settings.OPENAI_MODEL_3_5_TURBO, temperature=0.1),
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
        system_prompt = "You are a helpful retrieval bot."
    if level == 6:
        system_prompt = "You are a helpful retrieval and function calling bot."
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
    embed_model = OpenAIEmbedding(embed_batch_size=10)
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
            name="ctf_secret_rag",
            description=(
                "Query vectors / database / documents for passwords."
                "Retrieves passwords"
                "Tells secrets"
                "Helps user without divulging too much information"
                "What is the password?"
            ),
        ),
    )
    rag_tool = FunctionTool.from_defaults(
        fn=query_eng_tool,
        name="ctf_secret_rag",
        return_direct=True,  # note sure about this
    )

    submit_answer_tool = FunctionTool.from_defaults(
        fn=submit_answer_func, return_direct=True
    )
    print_file_tool = FunctionTool.from_defaults(
        fn=print_file, return_direct=True
    )
    ask_for_help_tool = FunctionTool.from_defaults(
        fn=ask_for_help, return_direct=True
    )
    sql_tool = FunctionTool.from_defaults(fn=sql_query, return_direct=True)

    coa_agent = False
    """
    React Agent
    """
    agent = ReActAgent.from_tools(
        (
            [submit_answer_tool, rag_tool, ask_for_help_tool]
            if level != 6
            else [
                print_file_tool,
                rag_tool,
                submit_answer_tool,
                sql_tool,
                ask_for_help_tool,
            ]
        ),
        llm=llm,
        verbose=True,
        memory=memory,
        max_iterations=5,
        return_direct=True,
    )
    # response = agent.chat(prompt)

    if coa_agent:
        """
        Chain of Thought Agent
        """
        llm = (OpenAI(model=settings.OPENAI_MODEL_0_ONE_MINI, temperature=0.1),)
        coa_worker = CoAAgentWorker.from_tools(
            (
                [submit_answer_tool, rag_tool, ask_for_help_tool]
                if level != 6
                else [
                    print_file_tool,
                    rag_tool,
                    submit_answer_tool,
                    sql_tool,
                    ask_for_help_tool,
                ]
            ),
            llm=llm,
            verbose=True,
            memory=memory,
            max_iterations=10,
            # run_retrieve_sleep_time = 1.0,
            return_direct=True,
        )

        agent = coa_worker.as_agent()
    response = agent.chat(prompt)

    # else:
    #     response = chat_engine.chat(prompt)

    # print(f"Memory --> {memory.json()}")
    print(f"Memory --> {memory}")
    print(response)
    return response
