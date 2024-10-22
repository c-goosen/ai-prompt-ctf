import datetime
from fastapi import APIRouter
from llama_index.core import SimpleDirectoryReader
from rag.system_prompt import get_system_prompt

from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from fastapi import Depends
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from rag.search import search_vecs_and_prompt
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

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
memory = ChatMemoryBuffer.from_defaults(token_limit=100000000)


settings.OPENAI_API_KEY


router = APIRouter()


templates = Jinja2Templates(directory="ctf/templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)


class Input(BaseModel):
    query: str


@router.api_route("/level/{_level}", methods=["GET"], include_in_schema=False)
async def load_level(
    _level: int,
    request: Request,
):
    if request.headers.get('hx-request'):
        response = templates.TemplateResponse(
            f"levels/htmx_level_{_level}.html",
            {"request": request, "message": "", "_level": _level},
        )
        return response

    else:
        response = templates.TemplateResponse(
            f"levels/generic_level.html",
            {"request": request, "message": "", "_level": _level},
        )
        return response

