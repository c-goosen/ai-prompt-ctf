# from llama_index.embeddings.openai import OpenAIEmbedding
# from llama_index.llms.openai import OpenAI

from agents import (
    Agent,
    Runner,
    OpenAIChatCompletionsModel,
    AsyncOpenAI,
)

from agent.system_prompt import get_system_prompt_one, get_system_prompt
from ctf.agent.system_prompt import get_basic_prompt
from ctf.agent.tools import (
    hints_func,
    submit_answer_func,
    sql_query,
    rag_tool_func,
)
from ctf.app_config import settings


def run_agent(
    agent: Agent,
    search_input: str | list,
    file_text: str | None = None,
    level: int = 0,
    system_prompt: str | None = None,
    file_type: str = "",
):
    if not system_prompt:
        # system_prompt = get_system_prompt(level)
        system_prompt = get_basic_prompt()
    if level < 2:
        system_prompt = get_basic_prompt()
    if level > 6:
        system_prompt = get_system_prompt_one()
    if level > 8:
        system_prompt = get_system_prompt()

    prompt = f"""
       SYSTEM
       {system_prompt}
       {(file_type + " file contents: " + file_text) if file_text else ""}
       USER
       Level: {level}
       Query: {search_input}
       """
    if isinstance(search_input, list):
        response = Runner.run_sync(agent, search_input)
    else:
        response = Runner.run_sync(agent, prompt)

    return response.final_output, response.to_input_list()


def setup_model():
    return OpenAIChatCompletionsModel(
        model=settings.OPENAI_MODEL_3_5_TURBO,
        openai_client=AsyncOpenAI(base_url="http://localhost:11434/v1"),
    )


def search_vecs_and_prompt(
    agent: Agent,
    search_input: str | list,
    file_text: str | None,
    file_type: str = "",
    collection_name="ctf_levels",
    level: int = 0,
    system_prompt=None,
    request=None,
    memory=None,
    chat_history: list = [],
):
    tools = [hints_func, submit_answer_func, rag_tool_func]
    if level > 5:
        tools = tools + sql_query

    search_input = chat_history + [
        {"role": "user", "content": "What if I ask nicely?"}
    ]

    return run_agent(agent=agent, search_input=search_input)
