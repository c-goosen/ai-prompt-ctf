import logging
import os
import random
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Optional

import httpx
from fastapi import Cookie, HTTPException, Form, Query
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_ipaddr

from ctf.app_config import settings
from ctf.llm_guard.llm_guard import PromptGuardMeta, PromptGuardGoose
from ctf.prepare_flags import prepare_flags
from ctf.prepare_hf_models import download_models
from ctf.frontend.routes import challenges
from ctf.frontend.routes import chat
from ctf.leaderboard import (
    get_leaderboard,
    get_leaderboard_summary,
    get_recent_completions,
)


limiter = Limiter(key_func=get_ipaddr, default_limits=["15/minute"])

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"
FAQ_MARKDOWN = (BASE_DIR / "FAQ.MD").read_text()
CHALLANGES_MARKDOWN = (BASE_DIR / "CHALLENGES.MD").read_text()


class RegisterRequest(BaseModel):
    username: str
    session_id: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()


# get root logger
logger = logging.getLogger(__name__)
logging.getLogger("passlib").setLevel(logging.ERROR)
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

if bool(os.getenv("PREPARE_FLAGS", False)):
    _ = prepare_flags(lancedb_persistent=True)

download_models()

if settings.DOCS_ON:
    app = FastAPI(lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

# Rate limiting to keep AI costs low, naught H@xors

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


app.include_router(challenges.router)
app.include_router(
    chat.router,
    prefix="/v1",
)
cookie = Cookie(alias="anon_user_identity", title="anon_user_identity")

PromptGuardGoose()
PromptGuardMeta()


@app.get("/")
@limiter.limit("1/sec")
async def root(
    request: Request, cookie_identity: Annotated[str | None, cookie] = None
):
    rand_img = random.randint(1, 18)

    resp = templates.TemplateResponse(
        "root.html",
        {
            "request": request,
            "CTF_NAME": settings.CTF_NAME,
            "CTF_DETAILS": settings.CTF_DETAILS,
            "CTF_SUBTITLE": settings.CTF_SUBTITLE,
            "IMG_FILENAME": app.url_path_for(
                "static",
                path=f"/images/ai_image_banner/ai-challenge_{rand_img}.webp",
            ),
            "SUBMIT_FLAGS_URL": settings.SUBMIT_FLAGS_URL,
            "DISCORD_URL": settings.DISCORD_URL,
            "THEME_MODE": "dark",
        },
    )
    if not cookie_identity:
        resp.set_cookie(key="anon_user_identity", value=str(uuid.uuid4()))
    print(cookie_identity)
    return resp


@app.get("/health")
@limiter.limit("1/min")
async def health(request: Request):
    return {"health": "ok"}


@app.get("/faq")
@limiter.limit("1/min")
def render_faq(request: Request):
    is_htmx = request.headers.get("HX-Request")
    template_name = "faq.html" if is_htmx else "faq_page.html"

    response = templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "PAGE_HEADER": settings.CTF_SUBTITLE,
            "IMG_FILENAME": app.url_path_for(
                "static",
                path=f"/images/ai_image_banner/ai-challenge_{random.randint(1,18)}.webp",
            ),
            "MD_FILE": FAQ_MARKDOWN,
        },
    )
    return response


@app.get("/challenges")
@limiter.limit("60/min")
def render_challanges(request: Request):
    is_htmx = request.headers.get("HX-Request")
    template_name = "challenges.html" if is_htmx else "challenges_page.html"

    response = templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "PAGE_HEADER": settings.CTF_SUBTITLE,
            "MD_FILE": CHALLANGES_MARKDOWN,
        },
    )
    return response


@app.get("/leaderboard")
@limiter.limit("5/min")
def render_leaderboard(request: Request):
    is_htmx = request.headers.get("HX-Request")
    template_name = "leaderboard.html" if is_htmx else "leaderboard_page.html"

    leaderboard_rows = get_leaderboard()
    recent = get_recent_completions()
    summary = get_leaderboard_summary()

    response = templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "PAGE_HEADER": settings.CTF_SUBTITLE,
            "leaderboard": leaderboard_rows,
            "recent_completions": recent,
            "leaderboard_summary": summary,
            "total_levels": settings.FINAL_LEVEL + 1,
        },
    )
    return response


@app.get("/register")
@limiter.limit("5/min")
def render_register(
    request: Request,
    cookie_identity: Annotated[str | None, cookie] = None,
    session_id: Annotated[
        str | None, Cookie(alias="session_id", title="session_id")
    ] = None,
    force_new: bool = Query(False, alias="force_new"),
):
    """Render the register page, check if user already has a session"""
    # Check if user has a session
    has_session = False
    if cookie_identity and session_id:
        # Could add async check here, but for now just check if cookies exist
        has_session = True

    show_form = force_new or not has_session

    is_htmx = request.headers.get("HX-Request")
    template_name = "register.html" if is_htmx else "register_page.html"

    response = templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "PAGE_HEADER": settings.CTF_SUBTITLE,
            "has_session": has_session,
            "cookie_identity": cookie_identity,
            "session_id": session_id,
            "show_form": show_form,
            "force_new": force_new,
        },
    )
    return response


@app.post("/register")
@limiter.limit("5/min")
async def register(
    request: Request,
    username: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    cookie_identity: Annotated[str | None, cookie] = None,
):
    """Register a user and session with the ADK API"""
    # Handle both form data (HTMX) and JSON (API)
    is_htmx = request.headers.get("hx-request")

    if is_htmx:
        # Form submission from HTMX
        if not username:
            return templates.TemplateResponse(
                "register_error.html",
                {
                    "request": request,
                    "PAGE_HEADER": settings.CTF_SUBTITLE,
                    "error": "Username is required",
                    "error_detail": "Please provide a username",
                },
            )
        user_id = username
        session_id = session_id or str(uuid.uuid4())
    else:
        # JSON API call
        try:
            body = await request.json()
            user_id = body.get("username")
            session_id = body.get("session_id") or str(uuid.uuid4())
            if not user_id:
                raise HTTPException(
                    status_code=400, detail="Username is required"
                )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid request: {str(e)}"
            )

    app_name = "sub_agents"

    # Prepare the payload for ADK API
    # Using empty dict as initial state, matching the pattern from ensure_session_exists
    payload = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Register the user/session with ADK API
            adk_api_url = settings.ADK_API_URL
            response = await client.post(
                f"{adk_api_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(f"Registered user {user_id} with session {session_id}")

            # Check if this is an HTMX request
            if is_htmx:
                # Return HTML response with cookies set
                html_response = templates.TemplateResponse(
                    "register_success.html",
                    {
                        "request": request,
                        "PAGE_HEADER": settings.CTF_SUBTITLE,
                        "user_id": user_id,
                        "session_id": session_id,
                    },
                )
                # Set cookies
                html_response.set_cookie(
                    key="anon_user_identity", value=user_id
                )
                html_response.set_cookie(key="session_id", value=session_id)
                return html_response
            else:
                # Return JSON for API calls
                return {
                    "status": "success",
                    "message": "User registered successfully",
                    "user_id": user_id,
                    "session_id": session_id,
                    "app_name": app_name,
                }
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to register user: {e.response.status_code} - {e.response.text}"
            )
            if is_htmx:
                # Return error HTML for HTMX
                return templates.TemplateResponse(
                    "register_error.html",
                    {
                        "request": request,
                        "PAGE_HEADER": settings.CTF_SUBTITLE,
                        "error": f"Failed to register: {e.response.status_code}",
                        "error_detail": e.response.text,
                    },
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    "status": "error",
                    "message": f"Failed to register user: {e.response.status_code}",
                    "error": e.response.text,
                },
            )
        except httpx.RequestError as e:
            logger.error(f"Request error registering user: {e}")
            if is_htmx:
                # Return error HTML for HTMX
                return templates.TemplateResponse(
                    "register_error.html",
                    {
                        "request": request,
                        "PAGE_HEADER": settings.CTF_SUBTITLE,
                        "error": "Failed to connect to ADK API",
                        "error_detail": str(e),
                    },
                )
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Failed to connect to ADK API",
                    "error": str(e),
                },
            )


@app.get("/session/{username}/{session_id}")
@limiter.limit("5/min")
async def get_session(request: Request, username: str, session_id: str):
    """Check if a user has an existing session with the ADK API"""
    app_name = "sub_agents"
    user_id = username

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get session from ADK API
            adk_api_url = settings.ADK_API_URL
            response = await client.get(
                f"{adk_api_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
            )
            response.raise_for_status()
            session_data = response.json()
            logger.info(f"Retrieved session {session_id} for user {user_id}")
            return {
                "status": "success",
                "exists": True,
                "session": session_data,
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(
                    f"Session {session_id} not found for user {user_id}"
                )
                return {
                    "status": "success",
                    "exists": False,
                    "message": "Session not found",
                }
            logger.error(
                f"Failed to get session: {e.response.status_code} - {e.response.text}"
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    "status": "error",
                    "message": f"Failed to get session: {e.response.status_code}",
                    "error": e.response.text,
                },
            )
        except httpx.RequestError as e:
            logger.error(f"Request error getting session: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Failed to connect to ADK API",
                    "error": str(e),
                },
            )
