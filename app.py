from app_config import settings
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

from app_config import settings
from routes import challenges
from routes import chat

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()


# get root logger
logger = logging.getLogger(__name__)
logging.getLogger("passlib").setLevel(logging.ERROR)
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
# get_async_session_context = contextlib.asynccontextmanager(get_async_session)

if settings.DOCS_ON:
    app = FastAPI(lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

# Rate limiting to keep AI costs low, naught H@xors
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

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
app.include_router(
    chat.app,
    prefix="/v1",
)


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
@limiter.limit("1/sec")
async def root(request: Request):
    return templates.TemplateResponse(
        "root.html",
        {
            "request": request,
            "CTF_NAME": settings.CTF_NAME,
            "CTF_DETAILS": settings.CTF_DETAILS,
            "CTF_SUBTITLE": settings.CTF_SUBTITLE,
            "RANDOM_IMG": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
            ],
            "SUBMIT_FLAGS_URL": settings.SUBMIT_FLAGS_URL,
            "DISCORD_URL": settings.DISCORD_URL,
        },
    )


@app.get("/health")
@limiter.limit("1/sec")
async def health():
    return {"health": "ok"}


@app.get("/faq")
@limiter.limit("5/sec")
def render_faq(request: Request):
    response = templates.TemplateResponse(
        f"faq.html",
        {
            "request": request,
            "RANDOM_IMG": [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
            ],
        },
    )
    return response
