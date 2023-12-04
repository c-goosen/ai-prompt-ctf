from app_config import settings
import vecs

DB_CONNECTION = settings.SUPABASE_PG_URI

# create vector store client
vx = vecs.create_client(DB_CONNECTION)
levels = list(settings.PASSWORDS.keys())
print(f"Levels: {levels}")

for k in levels:
    collection_name = f"level_{k}"
    docs = vx.get_collection(name=collection_name)
    docs.create_index()
