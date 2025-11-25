import base64
import json
import logging
import os
import httpx
from typing import Annotated
from typing import Optional

from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Form, UploadFile
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ctf.app_config import settings
from ctf.leaderboard import record_level_completion, strip_leaderboard_markers

# ADK API base URL
ADK_API_BASE_URL = settings.ADK_API_URL

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)


def denied_response(text_input):
    response = """!! You are not allowed to do that, you have been stopped by the LLM protection!
    Passwords are to be kept secret !!"""
    return HTMLResponse(
        content=f"""
            <div class="chat chat-start">
              <div class="chat-image avatar">
                <div class="w-10 rounded-full">
                  <i class="fa-solid fa-user" style="margin-right: 8px;"></i>
                </div>
              </div>
              <div class="chat-bubble"><md-block>{text_input}</md-block></div>
            </div>
            <div class="chat chat-end">
              <div class="chat-image avatar">
                <div class="w-10 rounded-full">
                  <i class="fa-solid fa-robot" style="margin-right: 8px;"></i>
                </div>
              </div>
              <div class="chat-bubble">{response}</div>
            </div>
            """,
        status_code=200,
    )


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def ensure_session_exists(
    app_name: str, user_id: str, session_id: str
) -> bool:
    """Ensure a session exists for the user, create if it doesn't exist"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Check if session exists
            response = await client.get(
                f"{ADK_API_BASE_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
            )
            if response.status_code == 200:
                return True
        except httpx.HTTPStatusError:
            pass  # Session doesn't exist, we'll create it

        try:
            # Create session
            response = await client.post(
                f"{ADK_API_BASE_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
                json=None,  # Empty state
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(f"Created session {session_id} for user {user_id}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to create session: {e.response.status_code} - {e.response.text}"
            )
            return False


async def call_adk_api(
    user_id: str,
    session_id: str,
    message: str,
    file_data: Optional[bytes] = None,
    file_name: Optional[str] = None,
    file_mime_type: Optional[str] = None,
) -> dict:
    """Call the ADK REST API at http://127.0.0.1:8000/run"""

    # Use the sub_agents app which contains all level agents
    app_name = "sub_agents"

    # Ensure session exists before making the run call
    session_created = await ensure_session_exists(app_name, user_id, session_id)
    if not session_created:
        raise Exception("Failed to create or access session")

    # Prepare the message parts
    parts = []

    # Add text part if message exists
    if message:
        parts.append({"text": message})
    else:
        raise Exception("No message provided")

    # Add inline_data part if file_data is provided
    if file_data:
        file_base64 = base64.b64encode(file_data).decode("utf-8")
        inline_data = {
            "inline_data": {
                "mime_type": file_mime_type or "application/octet-stream",
                "data": file_base64,
            }
        }
        if file_name:
            inline_data["inline_data"]["display_name"] = file_name
        parts.append(inline_data)

    # Use the format from Google ADK docs
    payload = {
        "appName": app_name,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {"role": "user", "parts": parts},
        "streaming": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{ADK_API_BASE_URL}/run",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error calling ADK API: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error calling ADK API: {e.response.status_code} - {e.response.text}"
            )
            raise


@router.post("/chat/completions", include_in_schema=True)
async def chat_completion(
    request: Request,
    file_input: UploadFile | None = None,
    text_input: str = Form(...),
    file_type: Optional[str] = Form(None),
    cookie_identity: Annotated[
        str | None,
        Cookie(alias="anon_user_identity", title="anon_user_identity"),
    ] = None,
    session_id: Annotated[
        str | None,
        Cookie(alias="session_id", title="session_id"),
    ] = None,
):
    file_data: Optional[bytes] = None
    file_name: Optional[str] = None
    file_mime_type: Optional[str] = None

    # Handle file uploads (audio and image processing)
    if file_input:
        file_name = file_input.filename
        file_mime_type = file_input.content_type or ""

        # Validate file type - only allow PDF, JSON, images, and audio
        allowed_mime_prefixes = [
            "image/",
            "audio/",
            "application/pdf",
            "application/json",
        ]
        # allowed_extensions = [".pdf", ".json"]

        file_name_lower = file_name.lower() if file_name else ""
        file_mime_lower = file_mime_type.lower()

        # has_allowed_extension = any(file_name_lower.endswith(ext) for ext in allowed_extensions)
        has_allowed_mime = any(
            file_mime_lower.startswith(prefix)
            for prefix in allowed_mime_prefixes
        )

        # if not has_allowed_extension and not has_allowed_mime:
        if not has_allowed_mime:
            return HTMLResponse(
                content="""
                <div class="alert alert-error">
                    <i class="fa-solid fa-exclamation-circle"></i>
                    <div>
                        <h4>Invalid file type</h4>
                        <p>Only PDF, JSON, image, and audio files are allowed.</p>
                    </div>
                </div>
                """,
                status_code=200,
            )

        file_data = await file_input.read()

    # Protection checks are now handled by individual agents

    # Use username and session_id from cookies (set during registration)
    user_id = cookie_identity
    if not user_id:
        return HTMLResponse(
            content="""
            <div class="alert alert-error">
                <i class="fa-solid fa-exclamation-circle"></i>
                <div>
                    <h4>No user session found</h4>
                    <p>Please register first before chatting.</p>
                </div>
            </div>
            """,
            status_code=200,
        )

    if not session_id:
        return HTMLResponse(
            content="""
            <div class="alert alert-error">
                <i class="fa-solid fa-exclamation-circle"></i>
                <div>
                    <h4>No session found</h4>
                    <p>Please register first to create a session.</p>
                </div>
            </div>
            """,
            status_code=200,
        )

    try:
        # Call ADK API
        adk_response = await call_adk_api(
            user_id=user_id,
            session_id=session_id,
            message=text_input,
            file_data=file_data,
            file_name=file_name,
            file_mime_type=file_mime_type,
        )

        def _normalize_role(role: Optional[str]) -> str:
            if not role:
                return "assistant"
            role = role.lower()
            if role in {"assistant", "model", "ctfsubagentsroot"}:
                return "assistant"
            if role in {"tool"}:
                return "tool"
            if role in {"user"}:
                return "user"
            return "assistant"

        response_messages: list[dict[str, str]] = []
        if adk_response and isinstance(adk_response, list):
            for event in adk_response:
                content = event.get("content") or {}
                parts = content.get("parts") or []
                role_hint = content.get("role") or event.get("author")
                text_chunks: list[str] = []

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
                    continue

                role = _normalize_role(role_hint)
                response_messages.append({"role": role, "text": text})

        if not response_messages:
            response_messages = [
                {
                    "role": "assistant",
                    "text": "Sorry, I couldn't process your request. Please try again.",
                }
            ]

    except Exception as e:
        logger.error(f"Error calling ADK API: {e}")
        response_messages = [
            {
                "role": "assistant",
                "text": "Sorry, there was an error processing your request. Please try again.",
            }
        ]

    # Output protection checks are now handled by individual agents

    chat_segments = [
        f"""
        <div class="chat chat-start">
          <div class="chat-image avatar">
            <div class="w-10 rounded-full">
              <i class="fa-solid fa-user" style="margin-right: 8px;"></i>
            </div>
          </div>
          <div class="chat-bubble"><md-block>{text_input}</md-block></div>
        </div>
        """
    ]

    completed_levels: set[int] = set()
    for message in response_messages:
        cleaned_text, markers = strip_leaderboard_markers(message["text"])
        message["text"] = cleaned_text
        for marker in markers:
            if marker.get("status") == "correct":
                level = marker.get("level")
                if isinstance(level, int):
                    completed_levels.add(level)
        if message["role"] == "assistant":
            chat_segments.append(
                f"""
                <div class="chat chat-end">
                  <div class="chat-image avatar">
                    <div class="w-10 rounded-full">
                      <i class="fa-solid fa-robot" style="margin-right: 8px;"></i>
                    </div>
                  </div>
                  <div class="chat-bubble"><md-block>{message['text']}</md-block></div>
                </div>
                """
            )
        elif message["role"] == "tool":
            chat_segments.append(
                f"""
                <div class="chat chat-end">
                  <div class="chat-image avatar">
                    <div class="w-10 rounded-full">
                      <i class="fa-solid fa-wrench" style="margin-right: 8px;"></i>
                    </div>
                  </div>
                  <div class="chat-bubble chat-bubble-secondary">
                    <md-block>{message['text']}</md-block>
                  </div>
                </div>
                """
            )

    if completed_levels and cookie_identity:
        for level in sorted(completed_levels):
            record_level_completion(
                username=cookie_identity,
                level=level,
            )

    return HTMLResponse(content="".join(chat_segments), status_code=200)
