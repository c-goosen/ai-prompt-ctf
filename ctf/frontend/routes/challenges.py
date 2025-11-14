import logging
import os
import httpx
from typing import Annotated

from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ctf.app_config import settings

cookie = Cookie(alias="anon_user_identity", title="anon_user_identity")

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


settings.OPENAI_API_KEY


router = APIRouter()


templates = Jinja2Templates(directory="frontend/templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)


class Input(BaseModel):
    query: str


@router.api_route("/level/{_level}", methods=["GET"], include_in_schema=False)
async def load_level(
    _level: int,
    request: Request,
    cookie_identity: Annotated[str | None, cookie] = None,
):
    # For now, we'll use empty chat history since ADK manages session state
    # In the future, we could call ADK API to get session history if needed
    chat_history = []

    if request.headers.get("hx-request"):
        response = templates.TemplateResponse(
            f"levels/htmx_level_{_level}.html",
            {
                "request": request,
                "PAGE_HEADER": settings.CTF_SUBTITLE,
                "message": "",
                "_level": _level,
                "chat_history": chat_history,
            },
        )
        return response

    else:
        response = templates.TemplateResponse(
            "levels/generic_level.html",
            {
                "request": request,
                "PAGE_HEADER": settings.CTF_SUBTITLE,
                "message": "",
                "_level": _level,
                "chat_history": chat_history,
            },
        )
        return response


async def get_session_history(
    app_name: str, user_id: str, session_id: str
) -> list:
    """Get session history from ADK API if available"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"http://127.0.0.1:8000/apps/{app_name}/users/{user_id}/sessions/{session_id}"
            )
            if response.status_code == 200:
                session_data = response.json()
                # Extract messages from session data if available
                # This depends on the ADK session structure
                return session_data.get("messages", [])
    except Exception as e:
        logger.warning(f"Could not retrieve session history: {e}")
    return []


@router.get("/level/history/{_level}", include_in_schema=False)
async def load_history(
    request: Request,
    _level: int = 0,
    cookie_identity: Annotated[str | None, cookie] = None,
):
    # Try to get chat history from ADK API
    user_id = cookie_identity or "anonymous"
    session_id = f"{user_id}-level-{_level}"

    _messages = await get_session_history("sub_agents", user_id, session_id)
    print(f"Loading history for level {_level}, user {cookie_identity}")
    print(f"chat_history len: {len(_messages)}")

    response = templates.TemplateResponse(
        "levels/chat_history.html",
        {"request": request, "chat_history": _messages, "level": _level},
    )
    return response
