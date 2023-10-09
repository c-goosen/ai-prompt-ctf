import os

from pydantic import AnyUrl
from pydantic_settings import BaseSettings
import qdrant_client
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    CTF_NAME: str = os.getenv("CTF_NAME", "UW Prompt Injection challenge")
    CTF_DETAILS: str = os.getenv("CTF_DETAILS", """
    This is a prompt injection ( https://www.lakera.ai/insights/what-is-prompt-injection ) challenge.
    You need to progress through multiple levels. Each time you get a password/secret back,
    you should submit it to progress through the levels.
    Each level becomes harder.
    """)
    app_name: str = "LLM CTF - Get that password"
    admin_email: str = "christogoosen@gmail.com"
    QDRANT_PORT: str = os.getenv("QDRANT_PORT")
    QDRANT_HOST: AnyUrl = os.getenv("QDRANT_HOST")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY")
    INPUT_FILTERS: list[str] = ["secret", "password", "passphrase"]
    BLOCK_MESSAGES: list[str] = [
        "LLM protection activated, you can't do that.",
        "You have been blocked",
        "Sneaky sneaky",
    ]
    PASSWORDS: dict = {
        1: os.getenv("PASSWORDS_ONE"),
        2: os.getenv("PASSWORDS_TWO"),
        3: os.getenv("PASSWORDS_THREE"),
        4: os.getenv("PASSWORDS_FOUR"),
        5: os.getenv("PASSWORDS_FIVE"),
    }
    LEVEL_ICONS: dict = {
        1: "icon fa-solid fa-battery-empty fa-lg",
        2: "icon fa-solid fa-battery-quarter fa-lg",
        3:"icon fa-solid fa-battery-half fa-lg",
        4: "icon fa-solid fa-battery-three-quarters fa-lg",
        5: "icon fa-solid fa-battery-full fa-lg",
    }
    REGEX_LIST: list = [
        r"(\b[\w]{2}[\d]{6}\b)",
        r'\b(\d{5}-\d{3}-\d{7})|(\d{9})\b',
        r'[A-Z]{4}-[A-Z]{6}-[A-Z]{4}',
        r'(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}',
        r'^(?:4[0-9]{12}(?:[0-9]{3})?|[25][1-7][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})$'
        r'[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}-[a-zA-Z0-9]{5}' #takealot
    ]


settings = Settings()
QDRANT_CLIENT: object = qdrant_client.QdrantClient(
    f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
    api_key=f"{settings.QDRANT_API_KEY}",  # For Qdrant Cloud, None for local instance
)
