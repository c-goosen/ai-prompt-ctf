import logging
import os

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI

from app_config import settings
from llm_guard.protections import input_check
from llm_guard.search import search_vecs_and_prompt
from llm_guard.system_prompt import get_system_prompt, get_basic_prompt

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
memory = ChatMemoryBuffer.from_defaults(token_limit=100000000)

settings.OPENAI_API_KEY


router = APIRouter()


templates = Jinja2Templates(directory="templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)


def denied_response(text_input):
    response = "You are not allowed to do that, you have been stopped by the LLM protection! Passwords are to be kept secret"
    return HTMLResponse(
        content=f"""
                        <div class='lmt-heading func-heading'>
                        <div class='new-chat' style='text-align: left;'>
                        <i class="fa-solid fa-user"></i> >> {text_input}</div>
                        <div class='new-chat' style='text-align: right;'><i class="fa-solid fa-robot"></i> >> {response}</div>
                        </div>""",
        status_code=200,
    )


@router.post("/chat/completions", include_in_schema=True)
async def chat_completion(
    request: Request,
    text_input: str = Form(...),
    text_level: int = Form(...),
    text_model: str = Form(...),
):
    _level = text_level
    _llm = OpenAI(model=text_model, temperature=0.5)
    protect = False
    response = ""
    memory=request.app.chat_memory
    if int(_level) == 1:
        protect = input_check(text_input)

    else:
        protect = False
    if protect:
        return denied_response(text_input)
    else:
        if _level == 9:
            model = settings.OPENAI_MODEL_4_VISION

        elif _level in (7, 8):
            model = settings.OPENAI_MODEL_4_O_MINI
        elif _level == 6:
            model = settings.OPENAI_MODEL_4_O_MINI
        else:
            model = settings.OPENAI_MODEL_3_5_TURBO
            Settings.llm.system_prompt = get_system_prompt(level=_level)

        _llm = OpenAI(model=model, temperature=0.5)

        print(text_input)
        response = search_vecs_and_prompt(
            search_input=str(text_input),
            collection_name=f"ctf-secrets",
            level=_level,
            llm=_llm,
            memory=memory,
            react_agent=False if _level < 4 else True,
            system_prompt=get_system_prompt(level=_level)
            if _level > 2
            else get_basic_prompt(),
        )
    # if output_check(response, settings.PASSWORDS.get(_level)):
    #     denied_response(text_input)    # if output_check(response, settings.PASSWORDS.get(_level)):
    #     denied_response(text_input)

    return HTMLResponse(
        content=f"""
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
            <div class='chat-bubble user' style='background-color: #f1f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; text-align: left;'>
                <div style='display: flex; align-items: center;'>
                    <i class="fa-solid fa-user" style="margin-right: 8px;"></i>
                    <div style="flex: 1;"><md-block>{text_input}</md-block></div>
                </div>
            </div>
            <div class='chat-bubble bot' style='background-color: #e0f7fa; padding: 10px; border-radius: 10px; margin-bottom: 10px; text-align: left;'>
                <div style='display: flex; align-items: center;'>
                    <i class="fa-solid fa-robot" style="margin-right: 8px;"></i>
                    <div style="flex: 1;"><md-block>{response}</md-block></div>
                </div>
            </div>
        </div>
        """,
        status_code=200,
    )


@router.get("/chat/completion/suggestion")
def render_faq(
    request: Request,
    completion: str = Form(...),
):
    response = templates.TemplateResponse(
        f"suggestion_chatbox.html",
        {
            "request": request,
            "completion": completion,
        },
    )
    return response
