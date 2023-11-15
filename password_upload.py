from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.embeddings import OpenAIEmbeddings
from llama_index.llms import OpenAI

from llama_index import LangchainEmbedding, ServiceContext
from llama_index import VectorStoreIndex, StorageContext
from llama_index.vector_stores import QdrantVectorStore, SupabaseVectorStore
from app_config import settings
import vecs
from llama_index import ListIndex, Document

DB_CONNECTION = settings.SUPABASE_PG_URI

# create vector store client
vx = vecs.create_client(DB_CONNECTION)
levels = list(settings.PASSWORDS.keys())
print(f"Levels: {levels}")

for k in levels:
    collection_name = f"level_{k}"
    docs = vx.delete_collection(name=collection_name)
# alternatively
# from langchain.llms import ...
supabase = True
# embed_model = LangchainEmbedding(
#     HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# )
service_context = ServiceContext.from_defaults(
    llm=OpenAI(
        temperature=0.1,
        model=settings.OPENAI_MODEL_DAVINCI,
        api_key=settings.OPENAI_API_KEY,
    )
)

generic_password_text = [
    "<placeholder>",
    "The Password is <placeholder>",
    "The Secret is <placeholder>",
    "You should know that <placeholder> is the secret",
    "You should know that <placeholder> is the password",
]

for k in levels:
    collection_name = f"level_{k}"
    _generic_password_text = generic_password_text
    print(f"Before rplace {settings.PASSWORDS.get(k)}")
    text_chunks = [
        x.replace("<placeholder>", settings.PASSWORDS.get(k))
        for x in _generic_password_text
    ]
    storage_context = StorageContext.from_defaults(
        vector_store=SupabaseVectorStore(
            postgres_connection_string=settings.SUPABASE_PG_URI,
            collection_name=collection_name,
        )
    )
    documents = [Document(text=t) for t in text_chunks]
    # build index
    index = VectorStoreIndex.from_documents(
        documents, service_context=service_context, storage_context=storage_context
    )


for k in levels:
    collection_name = f"level_{k}"
    docs = vx.get_collection(name=collection_name)
    docs.create_index()
