from llama_index.core import ServiceContext
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.supabase import SupabaseVectorStore
from app_config import settings
from llm_guard.system_prompt import get_system_prompt


def search_vecs_and_prompt(
    search_input: str,
    service_context: ServiceContext,
    collection_name: str = "ctf-secrets",
    level: int = 0,
):
    system_prompt = get_system_prompt(level)

    prompt = f"""
    SYSTEM
    {system_prompt}
    USER
    {search_input}
    """
    # print(prompt)
    vector_store = SupabaseVectorStore(
        postgres_connection_string=settings.PG_URI,
        collection_name=collection_name,
    )
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, service_context=service_context
    )
    query_engine = index.as_query_engine(similarity_top_k=5)
    response = query_engine.query(prompt)
    return response.response
