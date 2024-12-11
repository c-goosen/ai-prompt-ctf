import random
from hashlib import sha256

from app_config import settings


def return_hash(input: str):
    return str(sha256(bytes(input, "utf-8")).hexdigest())


def hash_and_check_password(level, password_input: str):
    password_hash = sha256(
        bytes(settings.PASSWORDS.get(level, ""), "utf-8")
    ).hexdigest()
    input_hash = sha256(bytes(password_input, "utf-8")).hexdigest()
    if password_hash == input_hash:
        return True
    else:
        return False


def random_block_msg():
    return random.choice(settings.BLOCK_MESSAGES)
