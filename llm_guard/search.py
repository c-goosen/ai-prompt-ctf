
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from app_config import settings
from llm_guard.system_prompt import get_system_prompt
from llama_index.llms.openai import OpenAI

def search_vecs_and_prompt(
    search_input: str,
    collection_name: str = "ctf-secrets",
    level: int = 0,
    model: str = OpenAI(model="gpt-3.5-turbo", temperature=0.1),
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
        vector_store=vector_store, llm=model,
    )
    query_engine = index.as_query_engine(similarity_top_k=5)
    response = query_engine.query(prompt)
    return response.response
