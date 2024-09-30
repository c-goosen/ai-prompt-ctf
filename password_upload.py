from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.storage.storage_context import StorageContext

from app_config import settings

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

from chromadb.config import  Settings
import chromadb
# create vector store client
levels = list(settings.PASSWORDS.keys())
print(f"Levels: {levels}")

from llama_index.core.schema import TextNode
embed_model = OpenAIEmbedding(embed_batch_size=10)

nodes =[]

Settings.llm = OpenAI(
        temperature=0.1,
        model=settings.OPENAI_MODEL_DAVINCI,
        api_key=settings.OPENAI_API_KEY,
    )

generic_password_text = [
    "<placeholder>",
    "The Password is <placeholder>",
    "The Secret is <placeholder>",
    "You should know that <placeholder> is the secret",
    "You should know that <placeholder> is the password",
]

chroma_client = chromadb.PersistentClient()
try:
    chroma_client.delete_collection("ctf_levels")
except Exception as e:
    print(e)

chroma_client = chromadb.PersistentClient(path="./chroma_db")

chroma_collection = chroma_client.get_or_create_collection("ctf_levels")


vector_store = ChromaVectorStore(chroma_collection=chroma_collection, embed_model=embed_model)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

for k in levels:
    collection_name = f"level_{k}"
    _generic_password_text = generic_password_text
    print(f"Before rplace {settings.PASSWORDS.get(k)}")
    for x in _generic_password_text:
        nodes.append(TextNode(
            text=x.replace("<placeholder>", settings.PASSWORDS.get(k)),
            metadata={
                "level": k,
            },
        ))

    # build index
index = VectorStoreIndex(
    nodes,
    vector_store=vector_store,
    storage_context=storage_context # critical for persisting
)

for k in levels:
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key="level", operator=FilterOperator.EQ, value=k),
        ]
    )
    retriever = index.as_retriever(filters=filters)
    print(retriever.retrieve("What is the password?"))

print(f"chroma_collection-->{chroma_collection} nr={chroma_collection.count()}")
print(chroma_collection.peek())