import random

from fastapi import FastAPI, Form, Request, Response
from starlette.responses import RedirectResponse
from llama_index import ServiceContext
from app_config import settings, QDRANT_CLIENT
from llama_index.llms import OpenAI
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import LangchainEmbedding
from pydantic import BaseModel
from search import search_qdrant
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import protections
from utils import hash_and_check_password, return_hash, random_block_msg

llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY)
embed_model = LangchainEmbedding(
    HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
)
service_context = ServiceContext.from_defaults(llm=llm, embed_model=embed_model)

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/")
async def root(request:Request):
    return templates.TemplateResponse(
            "root.html", {"request": request, "CTF_NAME": settings.CTF_NAME, "CTF_DETAILS": settings.CTF_DETAILS}
        )


class Input(BaseModel):
    query: str


@app.post("/level/1/submit")
def check_level_one(request: Request, response: Response, message: str = Form(...)):
    level = 1

    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name=f"level-{level}",
    )
    if protections.input_check(message):
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": random_block_msg(), "level": level}
        )
    else:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": response, "level": level}
        )


@app.post("/level/{_level}/confirm")
def answer_level_one(_level: str, request: Request, password: str = Form(...)):
    answer_hash = hash_and_check_password(level=int(_level), password_input=password)
    if answer_hash:
        #url = app.url_path_for("redirected")
        url = f"/level/{(int(_level)+1)}/{answer_hash}"
        response = RedirectResponse(url=url)
        response.set_cookie(key=f"ctf_level_{_level}", value=return_hash(password))
        return response
    else:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": "Wrong password", "level": int(_level)}
        )


@app.get("/level/1")
async def read_item(request: Request):
    level = 1
    return templates.TemplateResponse(
        "generic_level.html", {"request": request, "level": level}
    )


# This endpoint allows going back to levels using cookies, don't need hash in URL
@app.api_route("/level/{_level}",  methods=["GET"], include_in_schema=False)
async def load_any_level_cookie(_level: str, request: Request):
    cookie = request.cookies.get(f"ctf_level_{int(_level)-1}")
    if cookie == return_hash(settings.PASSWORDS.get(int(_level)-1)):
        return templates.TemplateResponse("generic_level.html", {"request": request, "level": int(_level)})
    else:
        url = f"/level/1/"
        return RedirectResponse(url=url)


# Progressing between levels
# @app.post("/level/{level}/{_hash}", include_in_schema=False)
@app.api_route("/level/{_level}/{_hash}", methods=["GET", "POST"], include_in_schema=False)
async def load_any_level_hash(_level: str, request: Request, _hash: str):
    if not _hash:
        return templates.TemplateResponse("generic_level.html", {"request": request,"level": 1})
    _pass = settings.PASSWORDS.get(int(_level)-1)
    print(_pass)
    _hash_to_check = return_hash(_pass)
    print(_hash)
    if _hash_to_check == _hash:
        print(f"loading {int(_level)}")
        if int(_level)-1 != 5:
            return templates.TemplateResponse("generic_level.html", {"request": request, "level": int(_level)})
        else:
            return templates.TemplateResponse("complete.html", {"request": request, "pass": settings.PASSWORDS.get(int(_level)-1)})
    else:
        print("loading 1")
        return templates.TemplateResponse("generic_level.html", {"request": request, "message": "Incorrect Answer, try again", "level": int(_level)-1})


@app.post("/level/2/submit")
def check_level_two(request: Request, message: str = Form(...)):
    _level = 2
    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name=f"level-{_level}",
    )
    if protections.output_check(message, settings.PASSWORDS.get(_level)):
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": random_block_msg(), "level": _level}
        )
    else:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": response, "level": _level}
        )
@app.post("/level/3/submit")
def check_level_three(request: Request, message: str = Form(...)):
    _level = 3
    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name=f"level-{_level}",
    )
    if protections.input_and_output_checks(input=message, output=str(response)):

        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": random_block_msg(), "level": int(_level)}
        )
    else:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": response, "level": int(_level)}
        )
@app.post("/level/4/submit")
def check_level_four(request: Request, message: str = Form(...)):
    level = 4
    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name=f"level-{level}",
    )
    if protections.llm_protection(message):
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": random_block_msg(), "level": level}
        )
    else:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": response, "level": level}
        )

@app.post("/level/5/submit")
def check_level_five(request: Request, message: str = Form(...)):
    level = 5
    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name=f"level-{level}",
    )
    if protections.translate_and_llm(message):
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": random_block_msg(), "level": level}
        )
    else:
        return templates.TemplateResponse(
            "generic_level.html", {"request": request, "message": response, "level": level}
        )



