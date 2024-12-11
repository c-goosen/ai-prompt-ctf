import os

from ctf.app_config import settings
from ctf.utils import return_hash, hash_and_check_password, random_block_msg

os.environ["PASSWORD_ZERO"] = "test0"
os.environ["PASSWORD_ONE"] = "test1"

settings.PASSWORDS[0] = "PASSWORD_ZERO"
settings.PASSWORDS[1] = "PASSWORD_ONE"


def test_return_hash():
    assert (
        return_hash(input="test")
        == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    )


def test_hash_and_check_password():
    assert hash_and_check_password(0, "PASSWORD_ZERO")
    assert not hash_and_check_password(1, "PASSWORD_ZERO")


def test_random_block_msg():
    assert random_block_msg() == "LLM protection activated, you can't do that."
