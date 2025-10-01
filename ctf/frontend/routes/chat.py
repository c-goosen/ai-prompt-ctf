import base64
import logging
import os
import httpx
import json
from pprint import pprint
from typing import Annotated
from typing import Optional

from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Form, UploadFile
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI as OG_OPENAI

from ctf.app_config import settings

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

router = APIRouter()

templates = Jinja2Templates(directory="ctf/frontend/templates")
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
                f"http://127.0.0.1:8000/apps/{app_name}/users/{user_id}/sessions/{session_id}"
            )
            if response.status_code == 200:
                return True
        except httpx.HTTPStatusError:
            pass  # Session doesn't exist, we'll create it

        try:
            # Create session
            response = await client.post(
                f"http://127.0.0.1:8000/apps/{app_name}/users/{user_id}/sessions/{session_id}",
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
    user_id: str, session_id: str, message: str, level: int, file_text: str = ""
) -> dict:
    """Call the ADK REST API at http://127.0.0.1:8000/run"""

    # Use the sub_agents app which contains all level agents
    app_name = "sub_agents"

    # Ensure session exists before making the run call
    session_created = await ensure_session_exists(app_name, user_id, session_id)
    if not session_created:
        raise Exception("Failed to create or access session")

    # Prepare the message content with level information
    content_text = f"Level {level}: {message}"
    if file_text:
        content_text = f"Level {level}: {message}\n\nFile content: {file_text}"

    payload = {
        "appName": app_name,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {"parts": [{"text": content_text}], "role": "user"},
        "streaming": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://127.0.0.1:8000/run",
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
    text_level: int = Form(...),
    text_model: Optional[str] = Form(None),
    file_type: Optional[str] = Form(None),
    cookie_identity: Annotated[
        str | None,
        Cookie(alias="anon_user_identity", title="anon_user_identity"),
    ] = None,
):
    level = text_level
    file_text = ""

    # Handle file uploads (audio and image processing)
    if file_input:
        data = await file_input.read()
        if level == 5:
            print("File input detected -->")
            print(f"file_type --> {file_type}")
            if file_type == "audio":
                client = OG_OPENAI()
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=(
                        "temp." + file_input.filename.split(".")[1],
                        file_input.file,
                        file_input.content_type,
                    ),
                    response_format="text",
                )
                file_text = transcription
                print(file_text)

        elif level == 4:
            from utils import image_to_text

            print("In image file")
            file_text = image_to_text(data, prompt="What is in this image?")
            print(f"file_text -->{file_text}")

    # Protection checks are now handled by individual agents

    # Use cookie_identity as user_id and create session_id based on level
    user_id = cookie_identity or "anonymous"
    session_id = f"{user_id}-level-{level}"

    try:
        # Call ADK API
        adk_response = await call_adk_api(
            user_id=user_id,
            session_id=session_id,
            message=text_input,
            level=level,
            file_text=file_text,
        )

        # Extract response text from ADK response
        response_txt = ""
        if adk_response and isinstance(adk_response, list):
            for event in adk_response:
                if event.get("content") and event["content"].get("parts"):
                    for part in event["content"]["parts"]:
                        if "text" in part:
                            response_txt += part["text"]

        if not response_txt:
            response_txt = (
                "Sorry, I couldn't process your request. Please try again."
            )

    except Exception as e:
        logger.error(f"Error calling ADK API: {e}")
        response_txt = "Sorry, there was an error processing your request. Please try again."

    # Output protection checks are now handled by individual agents

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
          <div class="chat-bubble">{response_txt}</div>
        </div>
        """,
        status_code=200,
    )
