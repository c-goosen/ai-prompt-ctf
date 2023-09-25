from llama_index import VectorStoreIndex, ServiceContext
from llama_index.vector_stores import QdrantVectorStore


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
