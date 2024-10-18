from http.client import responses

import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from app_config import settings
from rag.system_prompt import get_system_prompt, get_basic_prompt
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import FunctionTool
from llama_index.core.tools import QueryEngineTool
from llama_index.core.tools import ToolMetadata
from llama_index.core.agent import ReActAgent
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_index.core.llms.llm import LLM
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import StorageContext
from llama_index.packs.agents_coa.step import CoAAgentWorker

def ask_for_help():
    """
    Give me help for the current level I am on.
    """

def submit_answer_func(answer: str, level: int):
    """Take a string answer and the current level and calculate if the answer is correct"""
    level_pass = settings.PASSWORDS.get(level)
    if answer == level_pass:
        return f""""{answer} is correct! Next Level: 
        <div class="level-menu new-chat"
                         hx-get="/htmx/level/{level}"
                         hx-trigger="click"
                         hx-target=".right-panel"
                         hx-swap="innerHTML">
                            <i class="fa-solid fa-plus"> Level {level}</i>
                    </div>
        """
    else:
        return f"Wrong, try again please"


def print_file(input: str):
    """Print file with input dir"""
    import os

    with open(input) as f:
        _ = f.read()
        print(f"Printing file name--> {input}")
        print(f"Printing file contents--> {_}")
        return _


def search_vecs_and_prompt(
    search_input: str,
    collection_name: str = "ctf-secrets",
    level: int = 0,
    llm: LLM = OpenAI(model="gpt-3.5-turbo", temperature=0.5),
    memory=None,
    react_agent=True,
    system_prompt=None,
    coa_agent=False
):
    if not system_prompt:
        # system_prompt = get_system_prompt(level)
        system_prompt = get_basic_prompt()

    prompt = f"""
    SYSTEM
    {system_prompt}
    USER
    Level: {level}
    {search_input}
    """
    # prompt = search_input
    # print(prompt)
    embed_model = OpenAIEmbedding(embed_batch_size=10)
    Settings.embed_model = embed_model
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    print(chroma_client.list_collections())
    chroma_collection = chroma_client.get_collection("ctf_levels")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Re-initialize your VectorStoreIndex with the storage context and embedding model
    # This step is crucial for integrating your existing vector_index with ChromaDB
    # index = VectorStoreIndex(embed_model=Settings.embed_model, storage_context=storage_context)
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=Settings.embed_model,
    )
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="level", operator=FilterOperator.EQ, value=level
            ),
        ]
    )

    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    retriever = index.as_retriever(filters=filters)
    # query_engine = RetrieverQueryEngine.from_args(
    #    retriever, llm=llm,
    #    similarity_top_k=5,
    #    filters=filters

    # )
    retriever = index.as_retriever(similarity_top_k=5, filters=filters)
    # query_engine = index.as_query_engine(similarity_top_k=5,
    #    filters=filters
    # )
    query_engine = RetrieverQueryEngine.from_args(retriever, llm=llm)

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
        fn=query_eng_tool, name="ctf_secret_rag"
    )

    submit_answer_tool = FunctionTool.from_defaults(fn=submit_answer_func)
    print_file_tool = FunctionTool.from_defaults(fn=print_file)
    agent = ReActAgent.from_tools(
        [submit_answer_tool, rag_tool]
        if level != 6
        else [print_file_tool, rag_tool, submit_answer_tool],
        llm=llm,
        verbose=True,
        memory=memory,
        max_iterations=10,
        # run_retrieve_sleep_time = 1.0,
        return_direct=True,
    )
    coa_worker = CoAAgentWorker.from_tools(
        [submit_answer_tool, rag_tool]
        if level != 6
        else [print_file_tool, rag_tool, submit_answer_tool],
        llm=llm,
        verbose=True,
        memory=memory,
        max_iterations=10,
        # run_retrieve_sleep_time = 1.0,
        return_direct=True,
    )

    if react_agent:
        response = agent.query(prompt)
    elif coa_agent:
        agent = coa_worker.as_agent()
        response = agent.query(prompt)
    else:
        response = query_engine.query(prompt)
    print(response.__dict__)
    print(dir(response))
    print(response)
    return response
