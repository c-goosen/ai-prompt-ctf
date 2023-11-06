import random

from fastapi import FastAPI, Form, Request, Response,Depends
from starlette.responses import RedirectResponse
from llama_index import ServiceContext
from app_config import settings, QDRANT_CLIENT
# from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import LangchainEmbedding
from pydantic import BaseModel
from search import search_qdrant, search_supabase
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import protections
from utils import hash_and_check_password, return_hash, random_block_msg
import os
from langchain.embeddings import OpenAIEmbeddings


from db import User, create_db_and_tables
from schemas import UserCreate, UserRead, UserUpdate
from users import auth_backend, current_active_user, fastapi_users

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY



embed_model = LangchainEmbedding(
    # HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

)
service_context = ServiceContext.from_defaults(
    llm=settings.llm_openai_3_5_turbo, embed_model=embed_model
)
service_context_4 = ServiceContext.from_defaults(
    llm=settings.llm_openai_4_turbo, embed_model=embed_model
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
# app.include_router(
#     fastapi_users.get_verify_router(UserRead),
#     prefix="/auth",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_users_router(UserRead, UserUpdate),
#     prefix="/users",
#     tags=["users"],
# )


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()

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
async def signup(request: Request):
    return templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
        },
    )
class Input(BaseModel):
    query: str


@app.post("/level/{_level}/confirm/", include_in_schema=False)
def confirm_password_generic(_level: str, request: Request, password: str = Form(...), user: User = Depends(current_active_user)):
    answer_hash = hash_and_check_password(level=int(_level), password_input=password)
    if answer_hash:
        new_level = int(_level) + 1
        # url = app.url_path_for("redirected")
        url = f"/level/{new_level}/{answer_hash}"
        response = RedirectResponse(url=url)
        response.set_cookie(key=f"ctf_level_{new_level}", value=return_hash(password))
        return response
    else:
        return templates.TemplateResponse(
            "generic_level.html",
            {"request": request, "message": "Wrong password", "_level": int(_level)},
        )


# @app.get("/level/1")
# async def read_item(request: Request):
#     level = 1
#     return templates.TemplateResponse(
#         "generic_level.html", {"request": request, "_level": level}
#     )


# This endpoint allows going back to levels using cookies, don't need hash in URL
@app.api_route("/level/{_level}", methods=["GET"], include_in_schema=False)
async def load_any_level_cookie(_level: int, request: Request, user: User = Depends(current_active_user)):
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
async def load_any_level_hash(_level: int, request: Request, _hash: str):
    if not _hash:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "_level": 1}
        )
    _pass = settings.PASSWORDS.get(_level - 1)
    print(_pass)
    _hash_to_check = return_hash(_pass)
    print(_hash)
    if _hash_to_check == _hash:
        print(f"loading {_level}")
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
        print("loading 1")
        return templates.TemplateResponse(
            "generic_level.html",
            {"request": request, "message": "Incorrect Answer, try again", "_level": 1},
        )


@app.post("/level/submit/{_level}")
def check_level_generic(request: Request, _level: int, message: str = Form(...)):
    context = service_context if _level < 6 else service_context_4
    response = search_supabase(
        search_input=message,
        service_context=context,
        # QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name=f"level_{_level}",
    )
    trigger_checks = False
    print(f"LEVEL: {_level}")
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
        print("Defending level 5")
        if protections.translate_and_llm(message):
            trigger_checks = True
        else:
            trigger_checks = False
    elif _level == 6:
        print("Defending level 6")
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
