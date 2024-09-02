import contextlib
from app_config import settings
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from routes import auth, challenges

from database.db import (
    get_async_session,
)
from database.leaderboard import get_leaderboard_data
import logging
import httpx
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()


# get root logger
logger = logging.getLogger(__name__)
logging.getLogger('passlib').setLevel(logging.ERROR)
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
get_async_session_context = contextlib.asynccontextmanager(get_async_session)

if settings.DOCS_ON:
    app = FastAPI(lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    # Update with specific origins in production
    allow_origins=["localhost"],
    allow_methods=["GET", "POST"],
)

templates = Jinja2Templates(directory="templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)
app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(challenges.app)
app.include_router(auth.app)


@app.get("/start", include_in_schema=False)
async def start(request: Request):
    return templates.TemplateResponse(
        "start.html",
        {
            "request": request,
            "START_PASSWORD": settings.PASSWORDS.get(0, ""),
        },
    )


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "root.html",
        {
            "request": request,
            "CTF_NAME": settings.CTF_NAME,
            "CTF_DETAILS": settings.CTF_DETAILS,
            "CTF_SUBTITLE": settings.CTF_SUBTITLE,
            "RANDOM_IMG": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19]
        },
    )


@app.get("/health")
async def health():
    return {"health": "ok"}


@app.get("/leaderboard", include_in_schema=True)
async def leaderboard(request: Request):
    return templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "leaders": await get_leaderboard_data()},
    )

@app.get("/leaderboard/poll", include_in_schema=True)
async def leaderboard_poll(request: Request):
    return templates.TemplateResponse(
        "leaderboard_table.html",
        {"request": request, "leaders": await get_leaderboard_data()},
    )

# @app.get("/htmx/leaderboard", include_in_schema=True)
# async def htmx_leaderboard(request: Request):
#     leaders = await get_leaderboard_data()
