import datetime
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

app = APIRouter()

settings.OPENAI_API_KEY


router = APIRouter()


templates = Jinja2Templates(directory="templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)


class Input(BaseModel):
    query: str


@app.post("/level/{_level}/confirm/", include_in_schema=False)
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

@app.api_route("/htmx/level/{_level}", methods=["GET"], include_in_schema=False)
async def load_htmx_level(
    _level: int,
    request: Request,
):
    response = templates.TemplateResponse(
        f"levels/htmx_level_{_level}.html",
        {"request": request, "message": "", "_level": _level},
    )
    return response

# This endpoint allows going back to levels using cookies, don't need hash in URL
@app.api_route("/level/{_level}", methods=["GET"], include_in_schema=False)
async def load_any_level_cookie(
    _level: int,
    request: Request,
):
    if _level == 0:
        response = templates.TemplateResponse(
            "generic_level.html",
            {"request": request, "message": "", "_level": _level},
        )
        return response
    else:
        if _level < 10:
            return templates.TemplateResponse(
                "generic_level.html",
                {"request": request, "_level": _level},
            )
        else:
            return templates.TemplateResponse(
                "generic_level.html",
                {
                    "request": request,
                    "_level": _level,
                    "message": """This is a visual challenge,
                    try and prompt back the password in an images""",
                },
            )


# Progressing between levels
@app.api_route(
    "/level/{_level}/{_hash}/", methods=["POST"], include_in_schema=False
)
async def load_any_level_hash(
    _level: int,
    request: Request,
    _hash: str,
):
    if not _hash:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "_level": 0}
        )
    _pass = settings.PASSWORDS.get(_level - 1)
    _hash_to_check = return_hash(_pass)
    if _hash_to_check == _hash:
        logging.info(f"loading {_level}")
        return templates.TemplateResponse(
            "generic_level.html",
            {"request": request, "message": "", "_level": _level},
        )

    else:
        logging.info("loading level 1")
        return templates.TemplateResponse(
            "generic_level.html",
            {
                "request": request,
                "message": "Incorrect Answer, try again",
                "_level": 1,
            },
        )


@app.post("/level/submit/{_level}")
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
        memory=memory
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


@app.post("/level/9/photo/upload")
async def photo_upload_v2(
    request: Request,
    file: UploadFile | None,
    message: str = Form(...),
    include_in_schema=False,
):
    level = 9
    _pass = settings.PASSWORDS.get(level, "")

    image_base_dir = settings.IMAGE_DIR or f"{os.getcwd()}/tmp/"
    print(image_base_dir)
    if not os.path.exists(image_base_dir):
        try:
            os.mkdir(image_base_dir)
        except Exception:
            pass

    _img = await file.read()
    # _img_filename = file.filename
    _img_filename = f"{datetime.datetime.utcnow().timestamp()}"
    full_file_name = f"{image_base_dir}/{_img_filename}{os.path.splitext(file.filename)[1]}"
    openai_mm_llm = OpenAIMultiModal(
        model="gpt-4-vision-preview",
        api_key=settings.OPENAI_API_KEY,
        max_new_tokens=300,
    )

    if _img_filename:
        with open(full_file_name, "wb") as f:  # noqa
            f.write(_img)
    else:
        return templates.TemplateResponse(
            "generic_level.html",
            {
                "request": request,
                "message": """
                Please upload/attach an image as well.
                This level requires a prompt + image.
                Click Choose File.
                """,
                "_img": _img,
                "_level": 9,
            },
        )
    print(f"image_base_dir {image_base_dir}")
    print(f"full_file_name {full_file_name}")
    image_documents = SimpleDirectoryReader(
        image_base_dir, input_files=[f"{full_file_name}"], recursive=True
    ).load_data()
    _img_base64 = base64.b64encode(_img).decode("utf-8")
    prompt = get_system_prompt(level=level) + f"""USER\n{message}"""

    complete_response = openai_mm_llm.complete(
        prompt=prompt,
        image_documents=image_documents,
    )

    try:
        os.remove(f"{image_base_dir}/{_img_filename}")
    except Exception:
        pass

    return templates.TemplateResponse(
        "generic_level.html",
        {
            "request": request,
            "message": complete_response,
            "_img": _img_base64,
            "_level": 9,
        },
    )

