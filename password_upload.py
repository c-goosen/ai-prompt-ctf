from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.embeddings import OpenAIEmbeddings

from llama_index import LangchainEmbedding, ServiceContext
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores import QdrantVectorStore, SupabaseVectorStore
import qdrant_client
from app_config import settings
import vecs

DB_CONNECTION = settings.SUPABASE_PG_URI

# create vector store client
vx = vecs.create_client(DB_CONNECTION)



# alternatively
# from langchain.llms import ...
supabase = True
# embed_model = LangchainEmbedding(
#     HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# )
embed_model = LangchainEmbedding(
    OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
)
# llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo-16k", api_key=settings.OPENAI_API_KEY)
service_context = ServiceContext.from_defaults(
    embed_model=embed_model,
llm=settings.llm_openai_davinci
)

if not supabase:
    client = qdrant_client.QdrantClient(
        f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
        api_key=settings.QDRANT_API_KEY,  # For Qdrant Cloud, None for local instance
    )


levels = [1, 2, 3, 4, 5, 6]
for k in levels:
    collection_name = f"level_{k}"
    try:
        vx.delete_collection(collection_name)
    except Exception as e:
        print(e)
    if not supabase:
        storage_context = StorageContext.from_defaults(
            vector_store=QdrantVectorStore(
                client=client, collection_name=collection_name
            )
        )
    else:
        storage_context = StorageContext.from_defaults(
            vector_store=SupabaseVectorStore(
                postgres_connection_string=(settings.SUPABASE_PG_URI),
                collection_name=collection_name,
            )
        )

    documents = SimpleDirectoryReader(f"passwords/{k}").load_data()
    # print(documents)

    # define LLM

    index = GPTVectorStoreIndex.from_documents(
        documents, storage_context=storage_context, service_context=service_context
    )



for k in levels:
    collection_name = f"level_{k}"
    docs = vx.get_collection(name=collection_name)
    docs.create_index()

