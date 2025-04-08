import os
# from mem0 import MemoryClient
from mem0 import Memory
from pprint import pprint

# client = Memory() # get api_key from https://app.mem0.ai/

MEM0_CONFIG: dict = {
    "llm": {
            "provider": "ollama",
            "config": {
                "model": "deepseek-r1:1.5b",
                "temperature": 0,
                "max_tokens": 2000,
                "ollama_base_url": "http://localhost:11434",  # Ensure this URL is correct
            },
        },
        "embedder": {
                "provider": "ollama",
                "config": {
                    "model": "nomic-embed-text:latest",
                    # Alternatively, you can use "snowflake-arctic-embed:latest"
                    "ollama_base_url": "http://localhost:11434",
                },
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "memory",
                    "path": "chromdb",
                }
            }
        }
# Store messages


if __name__ == "__main__":
    client = Memory.from_config(MEM0_CONFIG)
    # client.delete_all()

    usr_msg =[{"role": "user", "content": "Hi, I'm Alex. I'm a vegetarian and I'm allergic to nuts."}]
    agent_msg = [
        {"role": "assistant",
         "content": "Hello Alex! I've noted that you're a vegetarian and have a nut allergy. I'll keep this in mind for any food-related recommendations or discussions."}
    ]

    result = client.add(usr_msg,  infer=False, run_id="chat-1", metadata={"level":1, "role":"user"},prompt=usr_msg[0]['content'])
    print(result)
    result = client.add(agent_msg, infer=False, run_id="chat-1", metadata={"level":1, "role":"agent"},prompt=agent_msg[0]['content'])
    print(result)

    # Retrieve memories
    all_memories = client.get_all(run_id="chat-1")#, metadata={"level":1})
    print("all_memories")
    pprint(all_memories)

    # Search memories
    query = "What do you know about me?"
    related_memories = client.search(query,run_id="chat-1")#, metadata={"level":1})
    print("related_memories")
    pprint(related_memories)

    # Get memory history
    history = client.history(memory_id="b816e525-6c8e-4fbc-a0e8-b8b0c5397a6a")
    print("history")
    pprint(history)