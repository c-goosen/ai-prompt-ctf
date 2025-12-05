import re

import cleantext

from ctf.app_config import settings


def text_normalization(text):
    return cleantext.clean(
        text,
        fix_unicode=True,
        to_ascii=True,
        lower=True,
        no_line_breaks=False,
        no_urls=False,
        no_emails=False,
        no_numbers=False,
        no_digits=False,
        no_currency_symbols=True,
        no_punct=True,
        lang="en",
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


async def llm_protection(model: object, labels: list, input: str = "") -> bool:
    protected = False
    llm = model
    resp = await llm.query(input)
    resp = dict(resp)
    if resp.get("label") in labels:
        if resp["score"] > 0.8:
            protected = True
    input = text_normalization(input)
    resp = await llm.query(input)
    if resp.get("label") in labels:
        if resp["score"] > 0.8:
            protected = True
    print(f"resp --> {resp}")
    return protected
