from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import LangchainEmbedding, ServiceContext
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.llms import OpenAI
from llama_index.vector_stores import QdrantVectorStore
import qdrant_client
from app_config import settings

# alternatively
# from langchain.llms import ...
embed_model = LangchainEmbedding(
    HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
)
# llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo-16k", api_key=settings.OPENAI_API_KEY)
service_context = ServiceContext.from_defaults(embed_model=embed_model)

client = qdrant_client.QdrantClient(
    f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
    api_key=settings.QDRANT_API_KEY,  # For Qdrant Cloud, None for local instance
)
levels = [1, 2, 3, 4, 5]
for k in levels:
    storage_context = StorageContext.from_defaults(
        vector_store=QdrantVectorStore(client=client, collection_name=f"level-{k}")
    )

    documents = SimpleDirectoryReader(f"passwords/{k}").load_data()
    # print(documents)

    # define LLM

    index = GPTVectorStoreIndex.from_documents(
        documents, storage_context=storage_context, service_context=service_context
    )
