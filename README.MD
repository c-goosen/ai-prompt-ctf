# Project  BSIDES CTF

Base on a combination of Vector Searching and LLMs.

This project is an exploration of what it would take to build a Gandalf LLM prompt injection challenge as well as 
train an LLM to protect various levels.

Tools
* LLamaindex
* RAG (Retrieval Augmented Generation)
* QDrant vector DB
* GPT3.5/GPT4 or LLama2 to ask questions
* Python 3.11+
* FastAPI  (async REST API framework)
* Pydantic (types)

## API Docs
API docs are located at ${URI}/docs
http://127.0.0.1:8000/docs#


## Install depedencies
Install poetry package manager
Then run
```bash
poetry install
```

## Loading documents into QDrant
Add files to directories with passwords for various levels. Repeat passwords with words like secret.
```bash
python password_upload.py
```

## Run
```bash

```