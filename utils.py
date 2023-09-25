from app_config import settings
from hashlib import sha256


def return_hash(input: str):
    return str(sha256(bytes(input, "utf-8")).hexdigest())


def hash_and_check_password(level, password_input: str):
    _password_hash = sha256(bytes(settings.PASSWORDS.get(level), "utf-8")).hexdigest()
    if _password_hash == sha256(bytes(password_input, "utf-8")).hexdigest():
        return _password_hash
    else:
        return False
