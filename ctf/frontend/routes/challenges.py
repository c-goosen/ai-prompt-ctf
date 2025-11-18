import json
import logging
import os
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import APIRouter, Cookie, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ctf.app_config import settings

cookie = Cookie(alias="anon_user_identity", title="anon_user_identity")

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


settings.OPENAI_API_KEY


router = APIRouter()

FRONTEND_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = FRONTEND_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)


# @router.get("/ctf", include_in_schema=False)
# async def render_ctf(request: Request):
#     """Serve the chat screen template at /ctf."""
#     return templates.TemplateResponse(
#         "levels/chat_screen.html",
#         {
#             "request": request,
#         },
#     )


class Input(BaseModel):
    query: str


@router.get("/ctf", include_in_schema=False)
async def load_chat(
    request: Request,
    cookie_identity: Annotated[str | None, cookie] = None,
    session_cookie: Annotated[
        str | None, Cookie(alias="session_id", title="session_id")
    ] = None,
):
    """Render the chat experience without level-specific logic."""
    chat_history: list = []
    if cookie_identity and session_cookie:
        chat_history = await get_session_history(
            "sub_agents", cookie_identity, session_cookie
        )

    is_htmx = request.headers.get("HX-Request")
    template_name = "levels/chat_screen.html" if is_htmx else "chat_page.html"
    context = {
        "request": request,
        "message": "",
        "chat_history": chat_history,
    }
    return templates.TemplateResponse(template_name, context)


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

            def _normalize_role(role: str | None, fallback: str | None) -> str:
                role = (role or fallback or "").lower()
                if role in {"assistant", "model", "ctfsubagentsroot"}:
                    return "assistant"
                if role in {"user"}:
                    return "user"
                return "assistant" if role else "assistant"

            def _event_to_message(event: dict) -> dict | None:
                content = event.get("content") or {}
                parts = content.get("parts") or []
                text_chunks: list[str] = []
                role_hint = content.get("role") or event.get("author")
                for part in parts:
                    if isinstance(part, dict):
                        if "text" in part:
                            text_chunks.append(str(part["text"]))
                        elif "functionCall" in part:
                            call = part["functionCall"]
                            args = call.get("args") or {}
                            args_str = json.dumps(
                                args, indent=2, sort_keys=True
                            )
                            text_chunks.append(
                                f"Function call `{call.get('name', 'unknown')}`"
                                f"\n```json\n{args_str}\n```"
                            )
                            role_hint = "assistant"
                        elif "functionResponse" in part:
                            fn_resp = part["functionResponse"]
                            resp = fn_resp.get("response") or {}
                            resp_str = json.dumps(
                                resp, indent=2, sort_keys=True
                            )
                            text_chunks.append(
                                f"Tool response `{fn_resp.get('name', 'unknown')}`"
                                f"\n```json\n{resp_str}\n```"
                            )
                            role_hint = "tool"
                    elif isinstance(part, str):
                        text_chunks.append(part)
                text = "\n".join(
                    chunk for chunk in text_chunks if chunk
                ).strip()
                if not text:
                    text = str(content.get("text") or "").strip()
                if not text:
                    return None
                role = _normalize_role(role_hint, event.get("author"))
                return {"memory": text, "metadata": {"role": role}}

            history: list = []

            # Prefer events payload (new ADK format)
            events = session_data.get("events", [])
            for event in events:
                message = _event_to_message(event)
                if message:
                    history.append(message)

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
        logger.warning(f"Could not retrieve session history: {e}")
    return []


@router.get("/chat/history", include_in_schema=False)
async def load_history(
    request: Request,
    cookie_identity: Annotated[str | None, cookie] = None,
    session_cookie: Annotated[
        str | None,
        Cookie(alias="session_id", title="session_id"),
    ] = None,
):
    """HTMX endpoint to render chat history."""
    chat_history: list = []

    if cookie_identity and session_cookie:
        chat_history = await get_session_history(
            "sub_agents", cookie_identity, session_cookie
        )
        logger.info(
            "Loaded %s history items for user %s",
            len(chat_history),
            cookie_identity,
        )
    else:
        logger.debug("Cannot load history without user/session cookies")

    response = templates.TemplateResponse(
        "levels/chat_history.html",
        {"request": request, "chat_history": chat_history},
    )
    return response
