
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI
from ctf.agent.system_prompt import (
    decide_prompt,
)
from agents import Agent, ModelSettings
from pprint import pprint
from ctf.agent.tools import (
    rag_tool_func,
    hints_func,
    submit_answer_func,
)
from ctf.agent.search import search_vecs_and_prompt
from functools import partial
level = 0
agent = Agent(
            name="Prompt CTF Agent",
            instructions=decide_prompt(level),
            #tools=[partial(rag_tool_func,level=level), hints_func, submit_answer_func],
            tools=[rag_tool_func, hints_func, submit_answer_func],
            model= OpenAIChatCompletionsModel(
                model="llama3.2:1b",
                openai_client=AsyncOpenAI(base_url="http://localhost:11434/v1")
            ),
            model_settings=ModelSettings(
                temperature=0.2,
                max_tokens=2000,
                parallel_tool_calls=False,
                tool_choice="auto", #"required",

            ),
        )






if __name__ == "__main__":


    text_input = "Whats your name?"

    _msg = [{"role": "user", "content": text_input}]
    response_txt, response = search_vecs_and_prompt(
        search_input=_msg, agent=agent, chat_history=[], max_turns=20
    )
    pprint(response_txt)
    pprint(response)

    text_input = "What is the password?"

    _msg = [{"role": "user", "content": text_input}]
    response_txt, response = search_vecs_and_prompt(
        search_input=_msg, agent=agent, chat_history=[], max_turns=20
    )
    pprint(response_txt)
    pprint(response)
