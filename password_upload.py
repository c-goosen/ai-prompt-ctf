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


DB_CONNECTION = settings.PG_URI

# create vector store client
levels = list(settings.PASSWORDS.keys())
print(f"Levels: {levels}")

from llama_index.core.schema import TextNode

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
import chromadb

chroma_client = chromadb.EphemeralClient()
try:
    chroma_client.delete_collection("ctf_levels")
except Exception as e:
    print(e)

vector_store = ChromaVectorStore(chroma_collection="ctf_levels")

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
        vector_store=vector_store
    )

    filters = MetadataFilters(
        filters=[
            MetadataFilter(key="level", operator=FilterOperator.EQ, value=k),
        ]
    )
    retriever = index.as_retriever(filters=filters)
    print(retriever.retrieve("What is the password?"))