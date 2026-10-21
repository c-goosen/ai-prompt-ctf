import logging
import os
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import APIRouter, Cookie, Request
from fastapi.templating import Jinja2Templates

from ctf.app_config import settings
from ctf.frontend.utils import authorized_identity, event_to_message

cookie = Cookie(alias="anon_user_identity", title="anon_user_identity")
session_cookie_param = Cookie(alias="session_id", title="session_id")
player_token_cookie = Cookie(alias="player_token", title="player_token")

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

router = APIRouter()

FRONTEND_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = FRONTEND_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)
templates.env.globals.update(DISCORD_URL=settings.DISCORD_URL)


@router.get("/ctf", include_in_schema=False)
async def load_chat(
    request: Request,
    cookie_identity: Annotated[str | None, cookie] = None,
    session_cookie: Annotated[str | None, session_cookie_param] = None,
    player_token: Annotated[str | None, player_token_cookie] = None,
):
    """Render the chat experience without level-specific logic."""
    chat_history: list = []
    user_id = authorized_identity(cookie_identity, session_cookie, player_token)
    if user_id:
        chat_history = await get_session_history(
            "sub_agents", user_id, session_cookie
        )

    is_htmx = request.headers.get("HX-Request")
    template_name = (
        "chat_components/chat_screen.html" if is_htmx else "chat_page.html"
    )
    context = {
        "message": "",
        "chat_history": chat_history,
    }
    return templates.TemplateResponse(request, template_name, context)


@router.get("/chat", include_in_schema=False)
async def load_chat_alias(
    request: Request,
    cookie_identity: Annotated[str | None, cookie] = None,
    session_cookie: Annotated[str | None, session_cookie_param] = None,
    player_token: Annotated[str | None, player_token_cookie] = None,
):
    """Backward-compatible alias for /ctf."""
    return await load_chat(
        request=request,
        cookie_identity=cookie_identity,
        session_cookie=session_cookie,
        player_token=player_token,
    )


async def get_session_history(
    app_name: str, user_id: str, session_id: str
) -> list:
    """Get session history from ADK API if available."""
    if not user_id or not session_id:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            adk_api_url = settings.ADK_API_URL
            response = await client.get(
                f"{adk_api_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
            )
            response.raise_for_status()
            session_data = response.json()

            history: list = []

            # Prefer events payload (new ADK format)
            for event in session_data.get("events", []):
                message = event_to_message(event)
                if message:
                    history.append(
                        {
                            "memory": message["text"],
                            "metadata": {"role": message["role"]},
                        }
                    )

            if history:
                return history

            # Fallback to legacy messages stored under state/messages/etc.
            legacy_messages = session_data.get("messages")
            if not legacy_messages and isinstance(session_data, dict):
                state = session_data.get("state") or {}
                legacy_messages = (
                    state.get("messages")
                    or state.get("history")
                    or state.get("memories")
                    or []
                )
            if isinstance(legacy_messages, list):
                return legacy_messages
            return []
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 404:
            logger.warning(
                "Failed to retrieve session history (%s): %s",
                e.response.status_code,
                e.response.text,
            )
    except Exception as e:
        logger.error(f"Could not retrieve session history: {e}")
    return []


@router.get("/chat/history", include_in_schema=False)
async def load_history(
    request: Request,
    cookie_identity: Annotated[str | None, cookie] = None,
    session_cookie: Annotated[str | None, session_cookie_param] = None,
    player_token: Annotated[str | None, player_token_cookie] = None,
):
    """HTMX endpoint to render chat history."""
    chat_history: list = []

    user_id = authorized_identity(cookie_identity, session_cookie, player_token)
    if user_id:
        chat_history = await get_session_history(
            "sub_agents", user_id, session_cookie
        )
        logger.info(
            "Loaded %s history items for user %s",
            len(chat_history),
            user_id,
        )
    else:
        logger.debug("Cannot load history without verified user/session")

    response = templates.TemplateResponse(
        request,
        "chat_components/chat_history.html",
        {"chat_history": chat_history},
    )
    return response
