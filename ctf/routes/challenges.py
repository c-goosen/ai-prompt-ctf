import logging
import os
from typing import Annotated

from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Request
from fastapi.templating import Jinja2Templates
from llama_index.core.memory import ChatMemoryBuffer
from pydantic import BaseModel

from ctf.app_config import settings

cookie = Cookie(alias="anon_user_identity", title="anon_user_identity")

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


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
    cookie_identity: Annotated[str | None, cookie] = None,
):
    # chat_history = settings.chats.get(int(_level))
    chat_history = ChatMemoryBuffer.from_defaults(
        token_limit=settings.token_limit,
        chat_store=settings.chat_store,
        chat_store_key=f"level-{_level}-{cookie_identity}",
    )

    if request.headers.get("hx-request"):
        response = templates.TemplateResponse(
            f"levels/htmx_level_{_level}.html",
            {
                "request": request,
                "message": "",
                "_level": _level,
                "chat_history": chat_history.chat_store.get_messages(
                    key=f"level-{_level}-{cookie_identity}"
                ),
            },
        )
        return response

    else:
        response = templates.TemplateResponse(
            "levels/generic_level.html",
            {
                "request": request,
                "message": "",
                "_level": _level,
                "chat_history": chat_history.chat_store.get_messages(
                    key=f"level-{_level}"
                ),
            },
        )
        return response


@router.get("/level/history/{_level}", include_in_schema=False)
def load_history(
    request: Request,
    _level: int = 0,
    cookie_identity: Annotated[str | None, cookie] = None,
):
    # chat_history = settings.chats.get(int(_level))
    chat_history = ChatMemoryBuffer.from_defaults(
        token_limit=settings.token_limit,
        chat_store=settings.chat_store,
        chat_store_key=f"level-{_level}-{cookie_identity}",
    )
    _messages = chat_history.chat_store.get_messages(
        key=f"level-{_level}-{cookie_identity}"
    )
    # print(len(_messages))
    print(f"chat_history len: {len(_messages)}")
    # _messages = _messages.reverse()

    response = templates.TemplateResponse(
        "levels/chat_history.html",
        {"request": request, "chat_history": _messages, "level": _level},
    )
    return response
