import contextlib

from fastapi import FastAPI, Request
from app_config import settings

# from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

from database.db import (
    create_db_and_tables,
    get_async_session,
)
from database.leaderboard import get_leaderboard_data
import logging

# get root logger
logger = logging.getLogger(
    __name__
)  # the __name__ resolve to "main" since we are at the root of the project.
# This will get the root logger since no logger in the configuration has this name.

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
get_async_session_context = contextlib.asynccontextmanager(get_async_session)


app = FastAPI()


templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

from routes import auth, challenges

app.include_router(challenges.app)
app.include_router(auth.app)


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "root.html",
        {
            "request": request,
            "CTF_NAME": settings.CTF_NAME,
            "CTF_DETAILS": settings.CTF_DETAILS,
        },
    )


@app.get("/leaderboard")
async def login(request: Request):
    return templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "leaders": await get_leaderboard_data()},
    )


@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
