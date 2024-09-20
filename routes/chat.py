

import datetime
from http.client import responses

from fastapi import APIRouter
from llama_index.core import SimpleDirectoryReader
from llm_guard.system_prompt import get_system_prompt

from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from fastapi import Depends
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from llm_guard.search import search_vecs_and_prompt
from llm_guard import protections
from utils import hash_and_check_password, return_hash, random_block_msg
from llama_index.core import Settings

from database.db import (
    User,
    UserPrompts,
)
from database.leaderboard import update_leaderboard_user
from database.users import (
    current_active_user,
    current_active_user_opt,
)
from database.leaderboard import cookies_after_login
import contextlib
import base64
from fastapi import UploadFile, Form
from app_config import settings

from fastapi.templating import Jinja2Templates
import os

from database.db import (
    get_async_session,
)
from database.leaderboard import get_leaderboard_data
import logging
from fastapi import Request
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
from fastapi.responses import HTMLResponse
# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
get_async_session_context = contextlib.asynccontextmanager(get_async_session)
memory = ChatMemoryBuffer.from_defaults(token_limit=100000000)
app = APIRouter()

settings.OPENAI_API_KEY


router = APIRouter()


templates = Jinja2Templates(directory="templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)

@app.post("/chat/completions", include_in_schema=True)
async def confirm_secret_generic(
    request: Request,
    text_input: str = Form(...),
):
    # _level=0
    # model = settings.OPENAI_MODEL_3_5_TURBO
    # if _level == 9:
    #     model = settings.OPENAI_MODEL_4_VISION
    #
    # elif _level in (7, 8):
    #     model = settings.OPENAI_MODEL_4_O_MINI
    # elif _level == 6:
    #     model = settings.OPENAI_MODEL_4_O_MINI
    # else:
    #     model = settings.OPENAI_MODEL_3_5_TURBO
    #     Settings.llm.system_prompt = get_system_prompt(level=_level)
    #
    # _llm = OpenAI(model=model, temperature=0.5)
    #
    # print(text_input)
    # response = search_vecs_and_prompt(
    #     search_input=str(text_input),
    #     collection_name=f"ctf-secrets",
    #     level=0,
    #     llm=_llm,
    #     memory=memory
    # )
    response = "Whoa!"
    return  HTMLResponse(content=f"""
    <div class='lmt-heading func-heading'>
    <div class='new-chat' style='text-align: left;'>
    <i class="fa-solid fa-user"></i> >> {text_input}</div>
    <div class='new-chat' style='text-align: right;'><i class="fa-solid fa-robot"></i> >> {response}</div>
    </div>"""
                         , status_code=200)