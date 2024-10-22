import logging
import os
from uuid import uuid4

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
from rag.search import search_vecs_and_prompt
from rag.system_prompt import get_system_prompt, get_basic_prompt

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
memory = ChatMemoryBuffer.from_defaults(token_limit=100000000)

settings.OPENAI_API_KEY


router = APIRouter()


templates = Jinja2Templates(directory="ctf/templates")
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

        _llm = OpenAI(model=model, temperature=0.9, memory=request.app.chat_memory)

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
            coa_agent=True if _level == 9 else False,
            request=request
        )
    # if output_check(response, settings.PASSWORDS.get(_level)):
    #     denied_response(text_input)    # if output_check(response, settings.PASSWORDS.get(_level)):
    #     denied_response(text_input)
    #request.app.chat_store.add_message(key=str(uuid4()), message=str(response))

    from llama_index.core.llms import ChatMessage
    messages = [
        ChatMessage(content=text_input, role="user"),
        ChatMessage(content=str(response), role="assistant"),
    ]
    await request.app.chat_store.aset_messages(f"level-{uuid4()}", messages)
    print(f"Chat history json--> {request.app.chat_store.json()}")
    print(f"Chat history get_keys--> {request.app.chat_store.get_keys()}")
    print(f"Chat chat_memory json--> {request.app.chat_memory.json()}")
    print(f"Chat chat_memory get--> {request.app.chat_memory.get()}")
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


@router.get("/chat/completion/suggestion")
def render_faq(
    request: Request,
    suggestion: str = "",
):
    response = templates.TemplateResponse(
        f"levels/suggestion_chatbox.html",
        {
            "request": request,
            "suggestion": suggestion,
        },
    )
    return response
