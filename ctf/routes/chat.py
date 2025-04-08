import base64
import logging
import os
from pprint import pprint
from typing import Annotated
from typing import Optional

from agents import Agent, ModelSettings
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Form, UploadFile
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI as OG_OPENAI

from ctf.agent.search import search_vecs_and_prompt
from ctf.agent.system_prompt import (
    decide_prompt,
)
from ctf.agent.tools import (
    rag_tool_func,
    hints_func,
    submit_answer_func,
)
from ctf.app_config import settings
from ctf.llm_guard.llm_guard import PromptGuardMeta, PromptGuardGoose
from ctf.llm_guard.protections import (
    input_check,
    input_and_output_checks,
    llm_protection,
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
    mem = settings.MEMORY
    # memory = settings.chat_history.get_messages(key=f"level-{_level}-{cookie_identity}")
    message_history = mem.get_all(
        run_id=f"{cookie_identity}-{_level}",
    ).get("results", [])

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
            from utils import image_to_text

            print("In image file")
            # client = OG_OPENAI()

            # image_path = "path_to_your_image.jpg"

            # Getting the base64 string
            # base64_image = encode_image(image_path)
            # b64_img = base64.b64encode(data).decode("utf-8")
            # response = client.chat.completions.create(
            #     model="gpt-4o-mini",
            #     messages=[
            #         {
            #             "role": "user",
            #             "content": [
            #                 {
            #                     "type": "text",
            #                     "text": "What is in this image?",
            #                 },
            #                 {
            #                     "type": "image_url",
            #                     "image_url": {
            #                         "url": f"data:image/jpeg;base64,{b64_img}"
            #                     },
            #                 },
            #             ],
            #         }
            #     ],
            #     max_tokens=500,
            # )
            # print(f"Image response: {response}")
            file_text = image_to_text(data, prompt="What is in this image?")
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

        # if _level == 4:
        #     _llm = OllamaMultiModal(
        #         model="gemma3:1b",
        #         temperature=0.1,
        #         max_new_tokens=1500,
        #         memory=memory,
        #     )
        # else:
        #     _llm = Ollama(
        #         model="MFDoom/deepseek-r1-tool-calling:1.5b",
        #         # model=text_model,
        #         temperature=0.1,
        #         max_new_tokens=1500,
        #         memory=memory,
        #     )
        agent = Agent(
            name="Prompt CTF Agent",
            instructions=decide_prompt(_level),
            tools=[rag_tool_func, hints_func, submit_answer_func],
            model_settings=ModelSettings(
                temperature=0.2,
                max_tokens=2000,
                parallel_tool_calls=True,
                tool_choice="required",
            ),
        )
        print(text_input)
        _msg = [{"role": "user", "content": text_input}]

        response_txt, response = search_vecs_and_prompt(
            search_input=_msg, agent=agent, chat_history=message_history
        )
        mem.add(
            _msg,
            infer=False,
            run_id=f"{cookie_identity}-{_level}",
            metadata={"level": _level, "role": "user"},
            prompt=_msg[0]["content"],
        )

        _res = mem.add(
            messages=[{"role": "assistant", "content": response_txt}],
            infer=False,
            run_id=f"{cookie_identity}-{_level}",
            metadata={"level": _level, "role": "assistant"},
            # prompt=_msg[0]['content']
        )

        print(f"settings.MEMORY.add\(['role': 'assistant', 'co' -->")
        pprint(_res)
    # messages = [
    #   ChatMessage(content=text_input, role="user"),
    #    ChatMessage(content=str(response), role="assistant"),
    # ]
    # await request.app.chat_store.aset_messages(f"level-{_level}-{uuid4()}", messages)
    if _level in [3, 10] and input_and_output_checks(
        input=text_input, output=response_txt
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
          <div class="chat-bubble">{response_txt}</div>
        </div>
        """,
        status_code=200,
    )
