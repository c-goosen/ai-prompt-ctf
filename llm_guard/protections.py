import decimal

from app_config import settings
import re
import cleantext
from .llm_guard import LLMGaurdV1
from googletrans import Translator


def text_normalization(text):
    return cleantext.clean(
        text,
        fix_unicode=True,  # fix various unicode errors
        to_ascii=True,  # transliterate to closest ASCII representation
        lower=True,  # lowercase text
        no_line_breaks=False,  # fully strip line breaks as opposed to only normalizing them
        no_urls=False,                  # replace all URLs with a special token
        no_emails=False,                # replace all email addresses with a special token
        no_numbers=False,  # replace all numbers with a special token
        no_digits=False,  # replace all digits with a special token
        no_currency_symbols=True,  # replace all currency symbols with a special token
        no_punct=True,  # remove punctuations
        lang="en",  # set to 'de' for German special handling)
    )


def input_check(input) -> bool:
    if any([x in text_normalization(input) for x in settings.INPUT_FILTERS]):
        return True
    else:
        return False


def output_check(input: str, output: str) -> bool:
    input = text_normalization(input)
    if input in output or input == output:
        return True
    else:
        return False


def output_regex(output):
    output = output.lower()
    for _regex in settings.REGEX_LIST:
        res = re.search(_regex, output)
        if res:
            return True
    output = text_normalization(output)
    for _regex in settings.REGEX_LIST:
        res = re.search(_regex, output)
        if res:
            return True
    return False


def input_and_output_checks(input: str, output: str) -> bool:
    output = text_normalization(output)
    input = text_normalization(input)

    output = output.lower()
    if any(
        [
            input_check(input),
            output_check(input=input, output=output),
            output_regex(output=output),
        ]
    ):
        return True
    else:
        return False


def llm_protection(input) -> bool:
    protected = False
    llm = LLMGaurdV1()
    resp = llm.query(input)
    # print(resp)
    resp = resp[0]
    # print(resp)
    resp = dict(resp)
    if resp.get("label") == "NEGATIVE":
        if resp["score"] > 0.8:
            protected = True
    input = text_normalization(input)
    resp = llm.query(input)[0]
    if resp.get("label") == "NEGATIVE":
        if resp["score"] > 0.8:
            protected = True

    return protected


def translate_and_llm(input) -> bool:
    protected = False
    translator = Translator()
    translated = translator.translate(text=input).text
    llm = LLMGaurdV1()
    resp = llm.query(translated)[0]
    # print(resp)
    if resp.get("label") == "NEGATIVE":
        if resp["score"] > decimal.Decimal(0.8):
            protected = True
    input = text_normalization(input)
    translated = translator.translate(text=input).text
    resp = llm.query(translated)[0]
    if resp.get("label") == "NEGATIVE":
        if resp["score"] > decimal.Decimal(0.8):
            protected = True

    return protected
