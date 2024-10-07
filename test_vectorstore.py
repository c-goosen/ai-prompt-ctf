from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

from app_config import settings

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
import chromadb

from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding

# create vector store client
levels = list(settings.PASSWORDS.keys())
print(f"Levels: {levels}")

from llama_index.core.schema import TextNode

embed_model = OpenAIEmbedding(embed_batch_size=10)
nodes = []

Settings.llm = OpenAI(
    temperature=0.1,
    model=settings.OPENAI_MODEL_DAVINCI,
    api_key=settings.OPENAI_API_KEY,
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")

print(chroma_client.list_collections())
chroma_collection = chroma_client.get_collection("ctf_levels")

print(f"chroma_collection-->{chroma_collection} nr={chroma_collection.count()}")
print(chroma_collection.peek())

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
# storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir="./chroma/" ) # <- here you DO specify persist_dir

index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store, embed_model=embed_model
)
for k in levels:
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key="level", operator=FilterOperator.EQ, value=k),
        ]
    )
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    retriever = index.as_retriever(filters=filters)
    print(retriever.retrieve("What is the password?"))
