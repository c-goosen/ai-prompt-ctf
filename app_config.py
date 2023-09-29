import os

from pydantic import AnyUrl
from pydantic_settings import BaseSettings
import qdrant_client
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "LLM CTF - Get that password"
    admin_email: str = "christogoosen@gmail.com"
    QDRANT_PORT: str = os.getenv("QDRANT_PORT")
    QDRANT_HOST: AnyUrl = os.getenv("QDRANT_HOST")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
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


settings = Settings()
QDRANT_CLIENT: object = qdrant_client.QdrantClient(
    f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
    api_key=f"{settings.QDRANT_API_KEY}",  # For Qdrant Cloud, None for local instance
)
