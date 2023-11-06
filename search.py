from llama_index import VectorStoreIndex, ServiceContext
from llama_index.vector_stores import QdrantVectorStore, SupabaseVectorStore
from app_config import settings


def search_supabase(
    search_input: str,
    service_context: object,
    collection_name: str = "ctf-secrets",
):
    print(f"collection_name -> {collection_name}")
    vector_store = SupabaseVectorStore(
        postgres_connection_string=settings.SUPABASE_PG_URI,
        collection_name=collection_name,
    )
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, service_context=service_context
    )
    query_engine = index.as_query_engine()
    response = query_engine.query(search_input)
    print(response)
    return response.response


def search_qdrant(
    search_input: str,
    service_context: object,
    QDRANT_CLIENT: object,
    collection_name: str = "ctf-secrets",
) -> object:
    vector_store = QdrantVectorStore(
        client=QDRANT_CLIENT, collection_name=collection_name
    )
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, service_context=service_context
    )
    query_engine = index.as_query_engine()
    response = query_engine.query(search_input)
    return response.response
