import os

try:
    from ctf.app_config import settings
    from ctf.embeddings import embed_texts
except Exception:
    from app_config import settings
    from embeddings import embed_texts
import sqlite3

import lancedb


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


def prepare_flags(lancedb_persistent: bool = True):
    # create vector store client
    levels = list(settings.PASSWORDS.keys())
    print(f"Levels: {levels}")

    generic_password_text = [
        "<placeholder>",
        "The Password is <placeholder>",
        "The Secret is <placeholder>",
        "You should know that <placeholder> is the secret",
        "You should know that <placeholder> is the password",
    ]

    # Connect to LanceDB
    if lancedb_persistent:
        db_path = "./lancedb"
        print("persisted lancedb")
    else:
        db_path = ":memory:"
        print("non-persisted lancedb")

    db = lancedb.connect(db_path)
    table_name = "ctf_levels"

    # Prepare all data for batch insertion
    all_data = []

    for k in levels:
        if k != 6:
            _generic_password_text = generic_password_text
            for i in range(0, len(_generic_password_text)):
                text = _generic_password_text[i].replace(
                    "<placeholder>", settings.PASSWORDS.get(k)
                )
                # Generate embedding for the text
                vector = embed_texts([text])[0]

                all_data.append(
                    {
                        "id": f"level-{k}-msg-{i}",
                        "text": text,
                        "vector": vector,
                        "level": k,
                    }
                )
        else:
            setup_sql_level(settings.PASSWORDS.get(k))

    # Create or overwrite table with all data
    if all_data:
        try:
            # Try to delete existing table if it exists
            db.drop_table(table_name)
        except Exception:
            pass  # Table doesn't exist, that's fine

        # Create table with data
        table = db.create_table(table_name, data=all_data, mode="overwrite")
        print(
            f"Created/updated table '{table_name}' with {len(all_data)} records"
        )
    else:
        # Open existing table or create empty one
        try:
            table = db.open_table(table_name)
        except Exception:
            # Create empty table with schema
            import pyarrow as pa

            schema = pa.schema(
                [
                    pa.field("id", pa.string()),
                    pa.field("text", pa.string()),
                    pa.field(
                        "vector", pa.list_(pa.float32(), 384)
                    ),  # all-MiniLM-L6-v2 produces 384-dim vectors
                    pa.field("level", pa.int64()),
                ]
            )
            table = db.create_table(table_name, schema=schema, mode="overwrite")

    return table


if __name__ == "__main__":
    table = prepare_flags(lancedb_persistent=True)

    print(f"Table has {table.count_rows()} rows")

    # Test query
    try:
        from ctf.embeddings import embed_text
    except Exception:
        from embeddings import embed_text
    query_vector = embed_text("What is the password?")
    results = table.search(query_vector).where("level = 2").limit(1).to_pandas()
    print(results)
    if not results.empty and "text" in results.columns:
        print(results["text"].iloc[0])
