import os

from pydantic import AnyUrl
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import logging

load_dotenv()


class Settings(BaseSettings):
    ORG_NAME: str = "BSIDES CPT"
    APP_SECRET: str = os.getenv("SECRET", "SECRET")
    DISCORD_URL: str = os.getenv(
        "DISCORD_URL",
        "https://discord.com/channels/687602309395382282/1042715550960341032",
    )
    SUBMIT_FLAGS_URL: str = os.getenv(
        "SUBMIT_FLAGS_URL", "http://www.example.org"
    )
    CTF_NAME: str = os.getenv(
        "CTF_NAME", "BSIDES CTF Prompt Injection challenge"
    )
    CTF_SUBTITLE: str = os.getenv("CTF_SUBTITLE", "aka Talk Dirty to me....")
    CTF_DETAILS: str = os.getenv(
        "CTF_DETAILS",
        """This is a prompt injection
        (https://www.lakera.ai/insights/what-is-prompt-injection)
        challenge.
        You need to progress through multiple levels.
        Each time you get a password/secret back,
        you should submit it to progress through the levels.
        Each level becomes progressively harder. Happy chatting/prompting.
        """,
    )
    # Supabase
    #
    app_name: str = "LLM CTF - Get that password"
    admin_email: str = "christogoosen@gmail.com"
    # OPENAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL_DAVINCI: str = "text-davinci-003"
    OPENAI_MODEL_3_5_TURBO: str = "gpt-3.5-turbo"
    OPENAI_MODEL_4: str = "gpt-4"
    OPENAI_MODEL_4_TURBO: str = "gpt-4-turbo"
    OPENAI_MODEL_4_VISION: str = "gpt-4-turbo"
    OPENAI_MODEL_4_O_MINI: str = "gpt-4o-mini"
    OPENAI_MODEL_0_ONE: str = "o1-preview"
    OPENAI_MODEL_0_ONE_MINI: str = "o1-mini"
    #
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY")
    INPUT_FILTERS: list[str] = ["secret", "password", "passphrase"]
    BLOCK_MESSAGES: list[str] = [
        "LLM protection activated, you can't do that.",
    ]
    IMAGE_DIR: str | bool = os.getenv("IMAGE_DIR", f"{os.getcwd()}/tmp")
    PASSWORDS: dict = {
        0: os.getenv("PASSWORD_ZERO", "PASSWORD_ZERO"),
        1: os.getenv("PASSWORD_ONE", "PASSWORD_ONE"),
        2: os.getenv("PASSWORD_TWO", "PASSWORD_TWO"),
        3: os.getenv("PASSWORD_THREE", "PASSWORD_THREE"),
        4: os.getenv("PASSWORD_FOUR", "PASSWORD_FOUR"),
        5: os.getenv("PASSWORD_FIVE", "PASSWORD_FIVE"),
        6: os.getenv("PASSWORD_SIX", "PASSWORD_SIX"),
        7: os.getenv("PASSWORD_SEVEN", "PASSWORD_SEVEN"),
        8: os.getenv("PASSWORD_EIGHT", "PASSWORD_EIGHT"),
        9: os.getenv("PASSWORD_NINE", "PASSWORD_NINE"),
        10: os.getenv("PASSWORD_TEN", "PASSWORD_TEN"),
    }
    # Regex list for things like IPs, credit cards etc
    # Amazon vouchers, etc.
    REGEX_LIST: list = [
        r"(\b[\w]{2}[\d]{6}\b)",
        r"\b(\d{5}-\d{3}-\d{7})|(\d{9})\b",
        r"[A-Z]{4}-[A-Z]{6}-[A-Z]{4}",
        r"(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]"
        + "|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}",
        r"^(?:4[0-9]{12}(?:[0-9]{3})?|[25][1-7][0-9]{14}|6(?:011|5[0-9]"
        + "[0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|["
        r"68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})$ ",
        r"[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}",  # takealot
        r"[a-f0-9]{8}\\-[a-f0-9]{4}\\-[a-f0-9]{4}\\-[a-f0-9]{4}\\-[a-f0-9]{12}",
        r"\\b[A-Za-z0-9._%+-]+(\\[AT\\]|@)[A-Za-z0-9.-]+(\\[DOT\\]|\\.)[A-Za-z]{2,}\\b",
    ]
    FINAL_LEVEL: int = 10  # Actually 5
    COOKIE_TIMEOUT: int = 5 * 24 * 60 * 60
    HUGGINGFACE_INFERENCE_API_URL: AnyUrl = os.getenv(
        "HUGGINGFACE_INFERENCE_API_URL",
        "https://k7jo934jj9b0wjer.us-east-1.aws.endpoints.huggingface.cloud",
    )
    COOKIE_DOMAIN: str = os.getenv("COOKIE_DOMAIN", "localhost")
    logger: object = logging.getLogger(__name__)
    DOCS_ON: bool = os.getenv("DOCS_ON", False)
    LOCAL_GUARD_LLM: bool = os.getenv("LOCAL_GUARD_LLM", True)
    THEME_COLOR: str = os.getenv("THEME_COLOR", "#de7838")
    LOGO_URL: str = os.getenv("LOGO_URL", "logo.svg")


settings = Settings()
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
os.environ["THEME_COLOR"] = settings.THEME_COLOR
print(settings.IMAGE_DIR)
