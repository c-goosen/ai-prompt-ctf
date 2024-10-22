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


@router.post("/level/{_level}/confirm/", include_in_schema=False)
async def confirm_secret_generic(
    _level: int,
    request: Request,
    password: str = Form(...),
):
    answer_hash = return_hash(input=password)
    if hash_and_check_password(level=_level, password_input=password):
        new_level = _level + 1
        # url = app.url_path_for("redirected")
        url = f"/level/{new_level}/{answer_hash}"

        response = RedirectResponse(url=url)
        response.set_cookie(
            key=f"ctf_level_{new_level}", value=return_hash(password)
        )
        return response
    else:
        return templates.TemplateResponse(
            "generic_level.html",
            {
                "request": request,
                "message": "Wrong password",
                "_level": int(_level),
            },
        )


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


@router.post("/level/submit/{_level}")
async def check_level_generic(
    request: Request,
    _level: int,
    message: str = Form(...),
):
    model = settings.OPENAI_MODEL_3_5_TURBO
    if _level == 9:
        model = settings.OPENAI_MODEL_4_VISION

    elif _level in (7, 8):
        model = settings.OPENAI_MODEL_4_O_MINI
    elif _level == 6:
        model = settings.OPENAI_MODEL_4_O_MINI
    else:
        model = settings.OPENAI_MODEL_3_5_TURBO
        Settings.llm.system_prompt = get_system_prompt(level=_level)

    response = search_vecs_and_prompt(
        search_input=message,
        collection_name=f"ctf-secrets",
        level=_level,
        llm=model,
        memory=memory,
    )

    trigger_checks = False
    logging.info(f"LEVEL: {_level}")
    if _level == 1:
        trigger_checks = False
    elif _level == 2:
        if protections.input_check(message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 3:
        if protections.output_check(message, settings.PASSWORDS.get(_level)):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 4:
        if protections.input_and_output_checks(
            input=message, output=str(response)
        ):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 5:
        if await protections.llm_protection(request, message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 6:
        logging.info("Defending level 5")
        if await protections.translate_and_llm(request, message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 7:
        logging.info("Defending level 6")
        if await protections.translate_and_llm(request, message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 8:
        logging.info("Defending level 6")
        if await protections.translate_and_llm(request, message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 9:
        logging.info("Defending level 6")
        if await protections.translate_and_llm(request, message):
            trigger_checks = True
        else:
            trigger_checks = False
    else:
        trigger_checks = False

    if trigger_checks:
        return templates.TemplateResponse(
            "generic_level.html",
            {
                "request": request,
                "message": random_block_msg(),
                "ai_messasge": response,
                "_level": int(_level),
            },
        )
    else:
        return templates.TemplateResponse(
            "generic_level.html",
            {"request": request, "message": response, "_level": int(_level)},
        )


