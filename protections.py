from app_config import settings


def input_regex(input) -> bool:
    if any([x in input.lower() for x in settings.INPUT_FILTERS]):
        return True
    else:
        return False


def output_regex(input, check) -> bool:
    if input in check or input == check:
        return True
    else:
        return False


def input_and_output_regex(input) -> bool:
    return False


def llm_protection(input) -> bool:
    return False


def translate_and_llm(input) -> bool:
    return False
