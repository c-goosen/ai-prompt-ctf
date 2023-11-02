
from .. import protections

import pytest

testdata = [
    ('4111111111111111', True),
    ("378282246310005", True)
]


@pytest.mark.parametrize("output,expected", testdata)
def test_input_protections(output, expected):
    assert protections.output_regex(output) == expected
