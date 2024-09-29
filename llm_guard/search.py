
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from app_config import settings
from llm_guard.system_prompt import get_system_prompt
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
from llama_index.core.llms.llm import LLM
from llama_index.core.query_engine import RetrieverQueryEngine

def submit_answer_func(answer: str):
    """Submit answer"""
    return f"Submitted -> {answer}"


def search_vecs_and_prompt(
    search_input: str,
    collection_name: str = "ctf-secrets",
    level: int = 0,
    llm: LLM = OpenAI(model="gpt-3.5-turbo", temperature=0.5),
    memory=None
    ):

    system_prompt = get_system_prompt(level)

    prompt = f"""
    SYSTEM
    {system_prompt}
    USER
    {search_input}
    """
    # print(prompt)
    vector_store = ChromaVectorStore(chroma_collection="ctf_levels")
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, llm=llm,
    )
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key="level", operator=FilterOperator.EQ, value=level),
        ]
    )
    retriever = index.as_retriever()
    query_engine = RetrieverQueryEngine.from_args(
        retriever, llm=llm,
        similarity_top_k=5,
        filters=filters

    )
    #query_engine = index.as_query_engine(similarity_top_k=5,
    #    filters=filters)

    query_eng_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="ctf_secret_rag",
            description=(
                "Query vectors / database / documents for passwords. "
                "Retrieves passwords"
                "Tells secrets"
                "Helps user without divulging too much information"
            ),
        )
    )
    rag_tool = FunctionTool.from_defaults(fn=query_eng_tool, name="ctf_secret_rag")

    submit_answer_tool = FunctionTool.from_defaults(fn=submit_answer_func)
    agent = ReActAgent.from_tools([submit_answer_tool, rag_tool],
     llm=llm, verbose=True, memory=memory,
    run_retrieve_sleep_time = 1.0,
     )
    from llama_index.agent.openai import OpenAIAssistantAgent
    #agent = OpenAIAssistantAgent.from_new(
    #    name="Password prompt Analyst",
    #    instructions=system_prompt,
    #    tools=[submit_answer_tool, rag_tool],
    #    verbose=True,
    #    run_retrieve_sleep_time=1.0,
    #    memory=memory
    #)

    agent.query(prompt)
    response = agent.query(prompt)
    return response.response
