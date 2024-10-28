import logging
import os
import random
from contextlib import asynccontextmanager

import httpx
import nest_asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.storage.chat_store import SimpleChatStore
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_ipaddr
from starlette.middleware.cors import CORSMiddleware

from ctf.app_config import settings
from ctf.routes import challenges
from ctf.routes import chat
from ctf.prepare_flags import prepare_flags

nest_asyncio.apply()


limiter = Limiter(key_func=get_ipaddr, default_limits=["15/minute"])

FAQ_MARKDOWN = open('ctf/FAQ.MD', 'r').read()
CHALLANGES_MARKDOWN = open('ctf/CHALLENGES.MD', 'r').read()


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

prepare_flags()
if settings.DOCS_ON:
    app = FastAPI(lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

# Rate limiting to keep AI costs low, naught H@xors
app.chat_store = SimpleChatStore()

app.chat_memory = ChatMemoryBuffer.from_defaults(
    token_limit=100000000,
    chat_store=app.chat_store,
    chat_store_key="user1",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    # Update with specific origins in production
    allow_origins=["localhost"],
    allow_methods=["GET", "POST"],
)

templates = Jinja2Templates(directory="ctf/templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)
app.mount("/static", StaticFiles(directory="ctf/static"), name="static")


app.include_router(challenges.router)
app.include_router(
    chat.router,
    prefix="/v1",
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
            "IMG_FILENAME": app.url_path_for(
                "static",
                path=f"/images/ai_image_banner/ai-challenge_{random.randint(1,18)}.webp",
            ),
            "SUBMIT_FLAGS_URL": settings.SUBMIT_FLAGS_URL,
            "DISCORD_URL": settings.DISCORD_URL,
            "_level": 0,
            "THEME_MODE": "dark"
        },
    )


@app.get("/health")
@limiter.limit("1/min")
async def health(request: Request):
    return {"health": "ok"}


@app.get("/faq")
@limiter.limit("1/min")
def render_faq(request: Request):
    response = templates.TemplateResponse(
        f"faq.html",
        {
            "request": request,
            "IMG_FILENAME": app.url_path_for(
                "static",
                path=f"/images/ai_image_banner/ai-challenge_{random.randint(1,18)}.webp",
            ),
            "MD_FILE": FAQ_MARKDOWN
        },
    )
    return response

@app.get("/challenges")
@limiter.limit("1/min")
def render_challanges(request: Request):
    response = templates.TemplateResponse(
        f"challenges.html",
        {
            "request": request,
            "MD_FILE": CHALLANGES_MARKDOWN
        },
    )
    return response