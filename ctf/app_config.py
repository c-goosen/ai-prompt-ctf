import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


if not os.getenv("PYTEST_CURRENT_TEST", False):
    load_dotenv()


class Settings(BaseSettings):
    DISCORD_URL: str = os.getenv(
        "DISCORD_URL",
        "https://discord.com/channels/687602309395382282/1168515417514442834",
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
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENSOURCE_LLM_MODEL: str = os.getenv("OPENSOURCE_LLM_MODEL", "qwen3:0.6b")
    OLLAMA_API_BASE: str = os.getenv(
        "OLLAMA_API_BASE", "http://127.0.0.1:11434"
    )
    INPUT_FILTERS: list[str] = ["secret", "password", "passphrase"]
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
    COOKIE_DOMAIN: str = os.getenv("COOKIE_DOMAIN", "localhost")
    logger: object = logging.getLogger(__name__)
    DOCS_ON: bool = os.getenv("DOCS_ON", False)
    THEME_COLOR: str = os.getenv("THEME_COLOR", "#de7838")
    LOGO_URL: str = os.getenv("LOGO_URL", "logo.svg")
    ADK_API_URL: str = os.getenv("ADK_API_URL", "http://127.0.0.1:8000")
    LEADERBOARD_DB_PATH: str = os.getenv(
        "LEADERBOARD_DB_PATH",
        str(Path(__file__).resolve().parent / "leaderboard.db"),
    )


settings = Settings()
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
os.environ["OLLAMA_API_BASE"] = settings.OLLAMA_API_BASE.rstrip("/")
os.environ["THEME_COLOR"] = settings.THEME_COLOR
