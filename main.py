import random
from fastapi import FastAPI, Form, Request
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
            "root.html", {"request": request}
        )


class Input(BaseModel):
    query: str


@app.post("/level/1/submit")
def check_level_one(request: Request, message: str = Form(...)):
    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name="level-1",
    )
    if protections.input_regex(message):
        return templates.TemplateResponse(
            "level1.html", {"request": request, "message": random_block_msg()}
        )
    else:
        return templates.TemplateResponse(
            "level1.html", {"request": request, "message": response}
        )


@app.post("/level/{level}/confirm")
def answer_level_one(level: str, password: str = Form(...)):
    answer_hash = hash_and_check_password(level=int(level), password_input=password)
    if answer_hash:
        #url = app.url_path_for("redirected")
        url = f"/level/{(int(level)+1)}/{answer_hash}"
        # response = RedirectResponse(url=url)
        return RedirectResponse(url=url)
    else:
        return {"message": "Wrong password"}


@app.get("/level/1")
async def read_item(request: Request):
    return templates.TemplateResponse("level1.html", {"request": request})


@app.post("/level/2/submit")
def check_level_two(request: Request, message: str = Form(...)):
    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name="level-2",
    )
    if protections.output_regex(message, settings.PASSWORDS.get(2)):
        return templates.TemplateResponse(
            "level1.html", {"request": request, "message": random_block_msg()}
        )
    else:
        return templates.TemplateResponse(
            "level1.html", {"request": request, "message": response}
        )

# Progressing between levels
# @app.post("/level/{level}/{_hash}", include_in_schema=False)
@app.api_route("/level/{_level}/{_hash}", methods=["GET", "POST"], include_in_schema=False)
async def level_two(_level: str, request: Request, _hash: str):
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

        return templates.TemplateResponse("level1.html", {"request": request, "message": "Incorrect Answer, try again"})


@app.post("/level/4/submit")
def check_level_two(request: Request, message: str = Form(...)):
    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name="level-4",
    )
    if protections.output_regex(message, settings.PASSWORDS.get(4)):
        return templates.TemplateResponse(
            "level1.html", {"request": request, "message": random_block_msg()}
        )
    else:
        return templates.TemplateResponse(
            "level1.html", {"request": request, "message": response}
        )

@app.post("/level/5/submit")
def check_level_two(request: Request, message: str = Form(...)):
    response = search_qdrant(
        search_input=message,
        service_context=service_context,
        QDRANT_CLIENT=QDRANT_CLIENT,
        collection_name="level-5",
    )
    if protections.output_regex(message, settings.PASSWORDS.get(5)):
        return templates.TemplateResponse(
            "level1.html", {"request": request, "message": random_block_msg()}
        )
    else:
        return templates.TemplateResponse(
            "level1.html", {"request": request, "message": response}
        )


