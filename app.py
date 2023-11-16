import contextlib
from llama_index.llms import OpenAI

from fastapi import FastAPI, Form, Request, Depends
from starlette.responses import RedirectResponse
from llama_index import ServiceContext
from app_config import settings
from typing import Annotated

# from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel
from search import search_supabase
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import protections
from utils import hash_and_check_password, return_hash, random_block_msg
import os

from database.db import (
    User,
    create_db_and_tables,
    get_async_session,
    get_user_db,
    UserPrompts,
)
from database.leaderboard import get_leaderboard_data, update_leaderboard_user
from database.schemas import UserCreate, UserRead
from database.users import (
    auth_backend,
    current_active_user,
    fastapi_users,
    current_active_user_opt,
)
import logging

# get root logger
logger = logging.getLogger(
    __name__
)  # the __name__ resolve to "main" since we are at the root of the project.
# This will get the root logger since no logger in the configuration has this name.

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
get_async_session_context = contextlib.asynccontextmanager(get_async_session)


service_context = ServiceContext.from_defaults(
    llm=OpenAI(
        temperature=0.1,
        model=settings.OPENAI_MODEL_3_5_TURBO,
        api_key=settings.OPENAI_API_KEY,
    )
)
service_context_4 = ServiceContext.from_defaults(
    llm=OpenAI(
        temperature=0.1, model=settings.OPENAI_MODEL_4, api_key=settings.OPENAI_API_KEY
    )
)
service_context_4_turbo = ServiceContext.from_defaults(
    llm=OpenAI(
        temperature=0.1,
        model=settings.OPENAI_MODEL_4_TURBO,
        api_key=settings.OPENAI_API_KEY,
    )
)

app = FastAPI()

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "root.html",
        {
            "request": request,
            "CTF_NAME": settings.CTF_NAME,
            "CTF_DETAILS": settings.CTF_DETAILS,
        },
    )


@app.get("/signup")
async def signup(request: Request, user: User = Depends(current_active_user_opt)):
    if user:
        return RedirectResponse("/level/1")
    return templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
        },
    )


import jwt


@app.get("/logout")
async def login(request: Request):
    response = RedirectResponse(url="/login")
    response.delete_cookie("fastapiusersauth")
    return response


@app.get("/login")
async def login(request: Request, user: User = Depends(current_active_user_opt)):
    if user:
        return RedirectResponse("/level/1")
    response = templates.TemplateResponse(
        "login.html",
        {
            "request": request,
        },
    )

    return response


@app.get("/leaderboard")
async def login(request: Request):
    return templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "leaders": await get_leaderboard_data()},
    )


class Input(BaseModel):
    query: str


@app.post("/level/{_level}/confirm/", include_in_schema=False)
async def confirm_secret_generic(
    _level: int,
    request: Request,
    password: str = Form(...),
    user: User = Depends(current_active_user),
):
    answer_hash = hash_and_check_password(level=_level, password_input=password)
    if answer_hash:
        new_level = _level + 1
        # url = app.url_path_for("redirected")
        url = f"/level/{new_level}/{answer_hash}"
        await update_leaderboard_user(
            user=user, level=_level, password_hash=answer_hash
        )
        response = RedirectResponse(url=url)
        response.set_cookie(key=f"ctf_level_{new_level}", value=return_hash(password))
        return response
    else:
        return templates.TemplateResponse(
            "generic_level.html",
            {"request": request, "message": "Wrong password", "_level": int(_level)},
        )


# This endpoint allows going back to levels using cookies, don't need hash in URL
@app.api_route("/level/{_level}", methods=["GET"], include_in_schema=False)
async def load_any_level_cookie(
    _level: int, request: Request, user: User = Depends(current_active_user_opt)
):
    if not user:
        return RedirectResponse("/login")
    if _level == 1:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": "", "_level": _level}
        )
    else:
        cookie = request.cookies.get(f"ctf_level_{_level}", False)
        if cookie == return_hash(settings.PASSWORDS.get(_level - 1)):
            return templates.TemplateResponse(
                "generic_level.html", {"request": request, "_level": _level}
            )
        else:
            url = f"/level/1/"
            return RedirectResponse(url=url)


# Progressing between levels
@app.api_route("/level/{_level}/{_hash}/", methods=["POST"], include_in_schema=False)
async def load_any_level_hash(
    _level: int,
    request: Request,
    _hash: str,
    user: User = Depends(current_active_user_opt),
):
    if not user:
        return RedirectResponse("/login")
    if not _hash:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "_level": 1}
        )
    _pass = settings.PASSWORDS.get(_level - 1)
    _hash_to_check = return_hash(_pass)
    if _hash_to_check == _hash:
        logging.info(f"loading {_level}")
        if int(_level) != settings.FINAL_LEVEL:
            return templates.TemplateResponse(
                "generic_level.html",
                {"request": request, "message": "", "_level": _level},
            )
        else:
            return templates.TemplateResponse(
                "complete.html", {"request": request, "_pass": _pass}
            )
    else:
        logging.info("loading level 1")
        return templates.TemplateResponse(
            "generic_level.html",
            {"request": request, "message": "Incorrect Answer, try again", "_level": 1},
        )


@app.post("/level/submit/{_level}")
async def check_level_generic(
    request: Request,
    _level: int,
    message: str = Form(...),
    user: User = Depends(current_active_user),
):
    if _level == 7:
        context = service_context_4_turbo
    elif _level == 6:
        context = service_context_4_turbo
    else:
        context = service_context

    response = search_supabase(
        search_input=message,
        service_context=context,
        collection_name=f"level_{_level}",
    )

    async with get_async_session_context() as session:
        user_prompt = UserPrompts(
            level=_level, user=user.id, prompt=message, answer=str(response)
        )
        session.add(user_prompt)
        await session.commit()
        await session.refresh(user_prompt)
    trigger_checks = False
    logging.info(f"LEVEL: {_level}")
    if _level == 1:
        if protections.input_check(message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 2:
        if protections.output_check(message, settings.PASSWORDS.get(_level)):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 3:
        if protections.input_and_output_checks(input=message, output=str(response)):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 4:
        if protections.llm_protection(message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 5:
        logging.info("Defending level 5")
        if protections.translate_and_llm(message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 6:
        logging.info("Defending level 6")
        if protections.translate_and_llm(message):
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


@app.post("/auth/signup")
async def signup(
    request: Request, email: Annotated[str, Form()], password: Annotated[str, Form()]
):
    from database.schemas import UserCreate
    from database.users import get_user_manager
    from fastapi_users.exceptions import UserAlreadyExists

    get_user_db_context = contextlib.asynccontextmanager(get_user_db)
    get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(email=email, password=password, is_superuser=False)
                    )
                    logging.info(f"User created {user}")
                    return RedirectResponse(url="/login", status_code=303)
    except UserAlreadyExists:
        logging.info(f"User {email} already exists")
        return RedirectResponse(url="/signup", status_code=303)


@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
