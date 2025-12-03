# from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from google.adk.models import Gemini

# model = LiteLlm(model="ollama_chat/qwen3:0.6b")
# model = LiteLlm(model="ollama_chat/qwen3:1.7b")

# "qwen3:1.7b"
# model = LiteLlm(model="openai/gpt-5-nano")
# model = LiteLlm(model="openai/gpt-5-mini")
# model_name = "gemini-2.5-pro"
model_name = "gemini-2.5-flash-lite"
# model = LiteLlm(model="openai/gpt-4o-mini")

# gemini

model = Gemini(
    retry_options=types.HttpRetryOptions(initial_delay=1, attempts=3),
    model=model_name,
)
