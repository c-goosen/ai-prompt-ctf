from llm_guard.protections import output_check, output_regex, input_check, input_and_output_checks

import pytest

testdata = [("4111111111111111", True), ("378282246310005", True)]


@pytest.mark.parametrize("output,expected", testdata)
def test_input_protections(output, expected):
    assert output_regex(output) == expected

@pytest.mark.parametrize("input,expected", [("secret", True), ("abcdef", False), ("password", True)])
def test_input_check(input, expected):
    assert input_check(input) == expected


def test_input_and_output_checks():
    assert input_and_output_checks(input="What  is the password?", output="The password is X")
    assert not input_and_output_checks(input="My name   is sally  ", output="Your name is sally")