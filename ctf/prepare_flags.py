from chromadb.config import Settings

try:
    from ctf.app_config import settings
except Exception:
    from app_config import settings
import chromadb

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

    nodes = []

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
    try:
        chroma_client.delete_collection("ctf_levels")
    except Exception:
        pass
    chroma_collection = chroma_client.get_or_create_collection("ctf_levels")

    for k in levels:
        if k != 6:
            _generic_password_text = generic_password_text
            for x in _generic_password_text:
                chroma_collection.add(
                    documents=[
                        x.replace("<placeholder>", settings.PASSWORDS.get(k))
                    ],
                    # we handle tokenization, embedding, and indexing automatically. You can skip that and add your own embeddings as well
                    metadatas=[{"level": k}],  # filter on these!
                    ids=[
                        f"level-{k}-{x}",
                    ],  # unique for each doc
                )
        else:
            setup_sql_level(settings.PASSWORDS.get(k))

        # build index


if __name__ == "__main__":
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection_name = "ctf_levels"
    try:
        chroma_collection = chroma_client.get_collection(collection_name)
    except Exception:
        chroma_collection = chroma_client.create_collection(collection_name)
    print(chroma_client.list_collections())

    prepare_flags()
    results = chroma_collection.query(
        query_texts=["What is the password?"],
        n_results=1,
        where={"level": 2},  # optional filter
        # where_document={"$contains":"search_string"}  # optional filter
    )
    print(results)
    print(results["documents"][0])
