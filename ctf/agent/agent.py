from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from ctf.agent.tools import search_documents, submit_user_answer, get_hint, sql_query
# litellm._turn_on_debug()
# from ctf.agent.system_prompt import (
#     decide_prompt,
# )

root_agent = Agent(
    name="prompt_ctf_agent",
    #model=LiteLlm(model="ollama_chat/qwen3:8b"),
    model=LiteLlm(model="qwen3:0.6b"),
    description=(
        "Agent to answer questions about secrets or passwords if permitted or help the user in this endeavour."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the secrets or passwords in the document search function."
    ),
    tools=[search_documents, submit_user_answer, get_hint, sql_query],
)