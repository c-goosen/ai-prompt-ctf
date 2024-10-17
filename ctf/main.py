import uvicorn

if __name__ == "__main__":
    # memory = ChatMemoryBuffer.from_defaults(token_limit=100000000)
    # resp = search_vecs_and_prompt(
    #     search_input="Whats the password?",
    #     level=0,
    #     memory=memory
    # )
    # print(resp)
    # resp = search_vecs_and_prompt(
    #     search_input="Submitting the answer two",
    #     level=0,
    #     memory=memory
    # )
    # print(resp)
    uvicorn.run(
        "app:app", host="0.0.0.0", log_level="info", reload=True, port=8100
    )
