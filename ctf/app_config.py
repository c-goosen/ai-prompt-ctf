import logging
import os

from dotenv import load_dotenv
from mem0 import Memory
from pydantic import AnyUrl
from pydantic_settings import BaseSettings


if not os.getenv("PYTEST_CURRENT_TEST", False):
    load_dotenv()


class Settings(BaseSettings):
    ORG_NAME: str = "BSIDES CPT"
    APP_SECRET: str = os.getenv("SECRET", "SECRET")

    MEM0_CONFIG: dict = {
        "llm": {
            "provider": "ollama",
            "config": {
                "model": "deepseek-r1:1.5b",
                "temperature": 0,
                "max_tokens": 2000,
                "ollama_base_url": "http://localhost:11434",  # Ensure this URL is correct
            },
        },
        "embedder": {
                "provider": "ollama",
                "config": {
                    "model": "chroma/all-minilm-l6-v2-f32",
                    # Alternatively, you can use "snowflake-arctic-embed:latest"
                    "ollama_base_url": "http://localhost:11434",
                },
            },
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "memory",
                "path": "chroma_db",
            },
        }
    }

    DISCORD_URL: str = os.getenv(
        "DISCORD_URL",
        "https://discord.com/channels/687602309395382282/1168515417514442834",
    )
    SUBMIT_FLAGS_URL: str = os.getenv(
        "SUBMIT_FLAGS_URL", "http://www.example.org"
    )
    CTF_NAME: str = os.getenv(
        "CTF_NAME", "BSIDES CTF Prompt Injection challenge"
    )
    CTF_SUBTITLE: str = os.getenv("CTF_SUBTITLE", "Agentic LLM CTF")
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

    # Open Source
    # Run everything opensource the default
    OPENSOURCE_LLM: bool = os.getenv("OPENSOURCE_LLM", True)
    OPENSOURCE_REASONING_MODEL: str = os.getenv(
        "OPENSOURCE_REASONING_MODEL", "deepseek-r1:1.5b"
    )
    OPENSOURCE_VISION_MODEL: str = os.getenv("OPENSOURCE_VISION_MODEL", "")
    OPENSOURCE_AUDIO_MODEL: str = os.getenv("OPENSOURCE_AUDIO_MODEL", "")

    # OPENAI
    # Not so open
    OPENAI_LLM: bool = os.getenv("OPENAI_LLM", False)
    EMBED_MODEL: str = "nomic-embed-text"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL_3_5_TURBO: str = "deepseek-r1:1.5b"
    OPENAI_MODEL_4: str = "deepseek-r1:1.5b"
    OPENAI_MODEL_4_TURBO: str = "deepseek-r1:1.5b"
    OPENAI_MODEL_4_VISION: str = "deepseek-r1:1.5b"
    OPENAI_MODEL_4_O_MINI: str = "deepseek-r1:1.5b"
    OPENAI_MODEL_0_ONE: str = "deepseek-r1:1.5b"
    OPENAI_MODEL_0_ONE_MINI: str = "deepseek-r1:1.5b"
    #
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY")
    INPUT_FILTERS: list[str] = ["secret", "password", "passphrase"]
    BLOCK_MESSAGES: list[str] = [
        "LLM protection activated, you can't do that.",
    ]
    IMAGE_DIR: str | bool = os.getenv("IMAGE_DIR", f"{os.getcwd()}/tmp")
    PASSWORDS: dict = {
        0: os.getenv("PASSWORD_ZERO", "PASS_ZERO"),
        1: os.getenv("PASSWORD_ONE", "PASS_ONE"),
        2: os.getenv("PASSWORD_TWO", "PASS_TWO"),
        3: os.getenv("PASSWORD_THREE", "PASS_THREE"),
        4: os.getenv("PASSWORD_FOUR", "PASS_FOUR"),
        5: os.getenv("PASSWORD_FIVE", "PASS_FIVE"),
        6: os.getenv("PASSWORD_SIX", "PASS_SIX"),
        7: os.getenv("PASSWORD_SEVEN", "PASS_SEVEN"),
        8: os.getenv("PASSWORD_EIGHT", "PASS_EIGHT"),
        9: os.getenv("PASSWORD_NINE", "PASS_NINE"),
        10: os.getenv("PASSWORD_TEN", "PASS_TEN"),
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
    token_limit: int = 20000
    MEMORY: Memory = Memory.from_config(MEM0_CONFIG)


settings = Settings()
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
os.environ["THEME_COLOR"] = settings.THEME_COLOR
print(settings.IMAGE_DIR)
