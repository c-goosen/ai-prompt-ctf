try:
    from ctf.app_config import settings
except Exception:
    from app_config import settings
import sqlite3

import chromadb
from chromadb import Settings


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
    # _ = cursor_obj.fetchall()
    # for row in _:
    #     print(row)

    # Close the connection
    print("Closing Connections")
    connection_obj.close()
    print("Connection closed")


def prepare_flags(chroma_client_persistent: bool=True):
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
    if chroma_client_persistent:
        chroma_client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))
        print("persisted chroma")
    else:
        chroma_client = chromadb.Client(settings=Settings(anonymized_telemetry=False))
        print("non-persisted chroma")


    # try:
    #     chroma_client.delete_collection("ctf_levels")
    # except Exception as e:
    #     print(e)

    chroma_collection = chroma_client.get_or_create_collection("ctf_levels")

    for k in levels:
        if k != 6:
            _generic_password_text = generic_password_text
            for i in range(0, len(_generic_password_text)):
                try:
                    chroma_collection.add(
                        documents=[
                            _generic_password_text[i].replace("<placeholder>", settings.PASSWORDS.get(k))
                        ],
                        # we handle tokenization, embedding, and indexing automatically
                        metadatas=[{"level": k}],  # filter on these!
                        ids=[f"level-{k}-msg-{i}"],  # unique for each doc
                    )
                except Exception as e:
                    print(f"Error adding to chroma collection for level {k}, index {i}: {e}")
        else:
            setup_sql_level(settings.PASSWORDS.get(k))

        # build index
    return chroma_collection

if __name__ == "__main__":
    chroma_collection = prepare_flags(chroma_client_persistent=True)

    print(chroma_collection.count())

    results = chroma_collection.query(
        query_texts=["What is the password?"],
        n_results=1,
        where={"level": 2},  # optional filter
        # where_document={"$contains":"search_string"}  # optional filter
    )
    print(results)
    print(results["documents"][0])
