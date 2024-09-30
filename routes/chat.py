

import datetime
from http.client import responses

from fastapi import APIRouter
from llama_index.core import SimpleDirectoryReader
from llm_guard.system_prompt import get_system_prompt, get_basic_prompt

from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from fastapi import Depends
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from llm_guard.search import search_vecs_and_prompt
from llm_guard import protections
from utils import hash_and_check_password, return_hash, random_block_msg
from llama_index.core import Settings

import contextlib
import base64
from fastapi import UploadFile, Form
from app_config import settings

from fastapi.templating import Jinja2Templates
import os

import logging
from fastapi import Request
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
from fastapi.responses import HTMLResponse
from llm_guard.protections import input_check, output_check
# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
memory = ChatMemoryBuffer.from_defaults(token_limit=100000000)
app = APIRouter()

settings.OPENAI_API_KEY


router = APIRouter()


templates = Jinja2Templates(directory="templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)

def denied_response(text_input):
    response = "You are not allowed to do that, you have been stopped by the LLM protection! Passwords are to be kept secret"
    return HTMLResponse(content=f"""
                        <div class='lmt-heading func-heading'>
                        <div class='new-chat' style='text-align: left;'>
                        <i class="fa-solid fa-user"></i> >> {text_input}</div>
                        <div class='new-chat' style='text-align: right;'><i class="fa-solid fa-robot"></i> >> {response}</div>
                        </div>"""
                        , status_code=200)

@app.post("/chat/completions", include_in_schema=True)
async def confirm_secret_generic(
    request: Request,
    text_input: str = Form(...),
    text_level: int = Form(...),
    text_model: str = Form(...),
):
    _level=text_level
    _llm = OpenAI(model=text_model, temperature=0.5)
    protect = False
    response = ""
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
            system_prompt=get_system_prompt(level=_level) if _level > 2 else get_basic_prompt()
        )
    # if output_check(response, settings.PASSWORDS.get(_level)):
    #     denied_response(text_input)    # if output_check(response, settings.PASSWORDS.get(_level)):
    #     denied_response(text_input)

    return HTMLResponse(content=f"""
        <div class='lmt-heading func-heading'>
        <div class='new-chat' style='text-align: left;'>
        <i class="fa-solid fa-user"></i> >> {text_input}</div>
        <div class='new-chat' style='text-align: right;'><i class="fa-solid fa-robot"></i> >> {response}</div>
        </div>"""
                        , status_code=200)
