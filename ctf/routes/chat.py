import base64
import logging
import os
from typing import Annotated
from typing import Optional

from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Form, UploadFile
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
from openai import OpenAI as OG_OPENAI

from ctf.app_config import settings
from ctf.llm_guard.llm_guard import PromptGuardMeta, PromptGuardGoose
from ctf.llm_guard.protections import (
    input_check,
    input_and_output_checks,
    llm_protection,
)
from ctf.rag.search import search_vecs_and_prompt
from ctf.rag.system_prompt import (
    decide_prompt,
)

# get root logger
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

settings.OPENAI_API_KEY

router = APIRouter()

templates = Jinja2Templates(directory="ctf/templates")
templates.env.globals.update(LOGO_URL=settings.LOGO_URL)
templates.env.globals.update(THEME_COLOR=settings.THEME_COLOR)


def denied_response(text_input):
    response = """!! You are not allowed to do that, you have been stopped by the LLM protection!
    Passwords are to be kept secret !!"""
    return HTMLResponse(
        content=f"""
            <div class="chat chat-start">
              <div class="chat-image avatar">
                <div class="w-10 rounded-full">
                  <i class="fa-solid fa-user" style="margin-right: 8px;"></i>
                </div>
              </div>
              <div class="chat-bubble"><md-block>{text_input}</md-block></div>
            </div>
            <div class="chat chat-end">
              <div class="chat-image avatar">
                <div class="w-10 rounded-full">
                  <i class="fa-solid fa-robot" style="margin-right: 8px;"></i>
                </div>
              </div>
              <div class="chat-bubble">{response}</div>
            </div>
            """,
        status_code=200,
    )


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


@router.post("/chat/completions", include_in_schema=True)
async def chat_completion(
    request: Request,
    file_input: UploadFile | None = None,
    text_input: str = Form(...),
    text_level: int = Form(...),
    text_model: Optional[str] = Form(None),
    file_type: Optional[str] = Form(None),
    cookie_identity: Annotated[
        str | None,
        Cookie(alias="anon_user_identity", title="anon_user_identity"),
    ] = None,
):
    _level = text_level
    file_text = ""
    memory: ChatMemoryBuffer = ChatMemoryBuffer.from_defaults(
        token_limit=settings.token_limit,
        chat_store=settings.chat_store,
        chat_store_key=f"level-{_level}-{cookie_identity}",
    )

    if file_input:
        data = await file_input.read()
        if _level == 5:
            print("File input detected -->")
            print(f"file_type --> {file_type}")
            if file_type == "audio":
                client = OG_OPENAI()

                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=(
                        "temp." + file_input.filename.split(".")[1],
                        file_input.file,
                        file_input.content_type,
                    ),
                    response_format="text",
                )
                file_text = transcription
                print(file_text)

        elif _level == 4:
            print("In image file")
            client = OG_OPENAI()

            # image_path = "path_to_your_image.jpg"

            # Getting the base64 string
            # base64_image = encode_image(image_path)
            b64_img = base64.b64encode(data).decode("utf-8")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What is in this image?",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_img}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )
            print(f"Image response: {response}")
            file_text = response.choices[0].message
            print(f"file_text -->{file_text}")

    if int(_level) == 1:
        protect = input_check(text_input)
    elif int(_level) == 7:
        protect = await llm_protection(
            model=PromptGuardMeta(),
            labels=["INJECTION", "JAILBREAk", "NEGATIVE"],
            input=text_input,
        )
    elif int(_level) in (8, 9, 10) and len(text_input.split(" ")) > 1:
        print("Running llm_protection")
        protect = await llm_protection(
            model=PromptGuardGoose(),
            labels=["injection", "jailbreak", "negative"],
            input=text_input,
        )
    else:
        protect = False

    if protect:
        return denied_response(text_input)
    else:
        Settings.llm.system_prompt = decide_prompt(level=_level)

        _llm = OpenAI(
            model=text_model,
            temperature=0.1,
            max_new_tokens=1500,
            memory=memory,
        )

        print(text_input)
        response = search_vecs_and_prompt(
            search_input=str(text_input),
            file_text=str(file_text),
            file_type=file_type,
            collection_name="ctf_levels",
            level=_level,
            llm=_llm,
            system_prompt=decide_prompt(_level),
            request=request,
            memory=memory,
        )

    # messages = [
    #   ChatMessage(content=text_input, role="user"),
    #    ChatMessage(content=str(response), role="assistant"),
    # ]
    # await request.app.chat_store.aset_messages(f"level-{_level}-{uuid4()}", messages)

    if _level in [3, 10] and input_and_output_checks(
        input=text_input, output=response
    ):
        return denied_response(text_input)
    return HTMLResponse(
        content=f"""
        <div class="chat chat-start">
          <div class="chat-image avatar">
            <div class="w-10 rounded-full">
              <i class="fa-solid fa-user" style="margin-right: 8px;"></i>
            </div>
          </div>
          <div class="chat-bubble"><md-block>{text_input}</md-block></div>
        </div>
        <div class="chat chat-end">
          <div class="chat-image avatar">
            <div class="w-10 rounded-full">
              <i class="fa-solid fa-robot" style="margin-right: 8px;"></i>
            </div>
          </div>
          <div class="chat-bubble">{response}</div>
        </div>
        """,
        status_code=200,
    )
