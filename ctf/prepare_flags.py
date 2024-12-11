import chromadb
from chromadb.config import Settings
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

try:
    from ctf.app_config import settings
except Exception:
    from app_config import settings
import sqlite3


def setup_sql_level(PASSWORD: str):

    # Connecting to sqlite
    # connection object
    connection_obj = sqlite3.connect("users.db")

    # cursor object
    cursor_obj = connection_obj.cursor()

    # Drop the GEEK table if already exists.
    cursor_obj.execute("DROP TABLE IF EXISTS USERS")

    # Creating table
    table = """ CREATE TABLE USERS (
                UserId INT NOT NULL,
                FirstName CHAR(25) NOT NULL,
                LastName CHAR(25),
                TokenCount INT
            ); """

    cursor_obj.execute(table)
    cursor_obj.execute(
        f"""INSERT INTO USERS (UserId,FirstName,LastName,TokenCount) VALUES (33, '{PASSWORD}', '{PASSWORD}', 190)"""  # noqa
    )
    cursor_obj.execute(
        """INSERT INTO USERS (UserId,FirstName,LastName,TokenCount) VALUES (2, 'Cryptic', 'Goose', 190)"""  # noqa
    )
    cursor_obj.execute(
        """INSERT INTO USERS (UserId,FirstName,LastName,TokenCount) VALUES (3, 'Test', 'Tube', 50)"""  # noqa
    )
    cursor_obj.execute(
        """INSERT INTO USERS (UserId,FirstName,LastName,TokenCount) VALUES (4, 'l33t', 'hacker', 20)"""  # noqa
    )
    cursor_obj.execute(
        """INSERT INTO USERS (UserId,FirstName,LastName,TokenCount) VALUES (5, 'Michael', 'Office', 5)"""  # noqa
    )
    cursor_obj.execute(
        """INSERT INTO USERS (UserId,FirstName,LastName,TokenCount) VALUES (5, 'SQL', 'Injection', 1000)"""  # noqa
    )
    connection_obj.commit()
    print("Table & data is Ready")
    statement = """SELECT * FROM USERS;"""

    cursor_obj.execute(statement)

    print("All the data")
    _ = cursor_obj.fetchall()
    # for row in _:
    #     print(row)

    # Close the connection
    connection_obj.close()


def prepare_flags():
    # create vector store client
    levels = list(settings.PASSWORDS.keys())
    print(f"Levels: {levels}")

    embed_model = OpenAIEmbedding(embed_batch_size=10)

    nodes = []

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

    vector_store = ChromaVectorStore(
        chroma_collection=chroma_collection, embed_model=embed_model
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    for k in levels:
        if k != 6:
            _generic_password_text = generic_password_text
            for x in _generic_password_text:
                nodes.append(
                    TextNode(
                        text=x.replace(
                            "<placeholder>", settings.PASSWORDS.get(k)
                        ),
                        metadata={
                            "level": k,
                        },
                    )
                )
        else:
            setup_sql_level(settings.PASSWORDS.get(k))

        # build index
    index = VectorStoreIndex(
        nodes,
        vector_store=vector_store,
        storage_context=storage_context,  # critical for persisting
    )

    for k in levels:
        filters = MetadataFilters(
            filters=[
                MetadataFilter(
                    key="level", operator=FilterOperator.EQ, value=k
                ),
            ]
        )
        _ = index.as_retriever(filters=filters)


if __name__ == "__main__":
    prepare_flags()
