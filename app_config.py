import os

from pydantic import AnyUrl
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from llama_index.llms import OpenAI

load_dotenv()


class Settings(BaseSettings):
    APP_SECRET: str = os.getenv("SECRET", "SECRET")
    CTF_NAME: str = os.getenv("CTF_NAME", "UW Prompt Injection challenge")
    CTF_DETAILS: str = os.getenv(
        "CTF_DETAILS",
        """
    This is a prompt injection ( https://www.lakera.ai/insights/what-is-prompt-injection ) challenge.
    You need to progress through multiple levels. Each time you get a password/secret back,
    you should submit it to progress through the levels.
    Each level becomes harder.
    """,
    )
    # Supabase
    SUPABASE_PG_USER: str = "postgres"
    SUPABASE_PG_PASSWORD: str = os.getenv("SUPABASE_PG_PASSWORD")
    SUPABASE_HOST: str = os.getenv(
        "SUPABASE_HOST", "db.dfqzxhihppgdbotizxul.supabase.co"
    )
    SUPABASE_PORT: str = "5432"
    SUPABASE_DB_NAME: str = "postgres"
    SUPABASE_PG_URI: str = f"postgresql://{SUPABASE_PG_USER}:{SUPABASE_PG_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DB_NAME}"
    SUPABASE_PG_URI_ASYNC: str = f"postgresql+asyncpg://{SUPABASE_PG_USER}:{SUPABASE_PG_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DB_NAME}"
    #
    app_name: str = "LLM CTF - Get that password"
    admin_email: str = "christogoosen@gmail.com"
    # OPENAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL_DAVINCI: str = "text-davinci-003"
    OPENAI_MODEL_3_5_TURBO: str = "gpt-3.5-turbo"
    OPENAI_MODEL_4: str = "gpt-4"
    OPENAI_MODEL_4_TURBO: str = "gpt-4-1106-preview"
    #
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY")
    INPUT_FILTERS: list[str] = ["secret", "password", "passphrase"]
    BLOCK_MESSAGES: list[str] = [
        "LLM protection activated, you can't do that.",
    ]
    PASSWORDS: dict = {
        1: os.getenv("PASSWORD_ONE"),
        2: os.getenv("PASSWORD_TWO"),
        3: os.getenv("PASSWORD_THREE"),
        4: os.getenv("PASSWORD_FOUR"),
        5: os.getenv("PASSWORD_FIVE"),
        6: os.getenv("PASSWORD_SIX"),
        7: os.getenv("PASSWORD_SEVEN"),
    }
    REGEX_LIST: list = [
        r"(\b[\w]{2}[\d]{6}\b)",
        r"\b(\d{5}-\d{3}-\d{7})|(\d{9})\b",
        r"[A-Z]{4}-[A-Z]{6}-[A-Z]{4}",
        r"(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}",
        r"^(?:4[0-9]{12}(?:[0-9]{3})?|[25][1-7][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})$"
        r"[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}",  # takealot
        r"[a-f0-9]{8}\\-[a-f0-9]{4}\\-[a-f0-9]{4}\\-[a-f0-9]{4}\\-[a-f0-9]{12}",
        r"\\b[A-Za-z0-9._%+-]+(\\[AT\\]|@)[A-Za-z0-9.-]+(\\[DOT\\]|\\.)[A-Za-z]{2,}\\b",
    ]
    FINAL_LEVEL: int = 7  # Actually 5
    COOKIE_TIMEOUT: int = 5 * 24 * 60 * 60


settings = Settings()
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
