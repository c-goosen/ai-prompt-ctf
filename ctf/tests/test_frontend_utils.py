from ctf.app_config import settings
from ctf.frontend.routes.chat import parse_adk_response_messages
from ctf.frontend.utils import (
    event_to_message,
    is_valid_session_id,
    is_valid_username,
)


def test_text_event_from_model_is_assistant():
    event = {"content": {"role": "model", "parts": [{"text": "hello"}]}}
    assert event_to_message(event) == {"role": "assistant", "text": "hello"}


def test_user_event_keeps_user_role():
    event = {"content": {"role": "user", "parts": [{"text": "hi"}]}}
    assert event_to_message(event)["role"] == "user"


def test_function_call_is_rendered_as_json():
    event = {
        "author": "Level0Agent",
        "content": {
            "parts": [
                {"functionCall": {"name": "hints_func", "args": {"level": 0}}}
            ]
        },
    }
    message = event_to_message(event)
    assert message["role"] == "assistant"
    assert "Function call `hints_func`" in message["text"]
    assert '"level": 0' in message["text"]


def test_multiline_single_key_tool_response_is_rendered_raw():
    event = {
        "content": {
            "parts": [
                {
                    "functionResponse": {
                        "name": "hints_func",
                        "response": {"result": "line one\nline two"},
                    }
                }
            ]
        }
    }
    message = event_to_message(event)
    assert message["role"] == "tool"
    assert "```\nline one\nline two\n```" in message["text"]


def test_password_search_response_is_redacted():
    password = settings.PASSWORDS[0]
    event = {
        "content": {
            "parts": [
                {
                    "functionResponse": {
                        "name": "password_search_func",
                        "response": {"password": password},
                    }
                }
            ]
        }
    }
    message = event_to_message(event)
    assert password not in message["text"]
    assert "[REDACTED]" in message["text"]


def test_empty_event_is_skipped_and_parse_falls_back():
    assert event_to_message({"content": {"parts": []}}) is None
    messages = parse_adk_response_messages([{"content": {"parts": []}}])
    assert len(messages) == 1
    assert messages[0]["role"] == "assistant"


def test_identifier_validation():
    assert is_valid_username("pytest-ab12_c.d")
    assert not is_valid_username("../x")
    assert not is_valid_username("")
    assert is_valid_session_id("0f8fad5b-d9cb-469f-a165-70867728950e")
    assert not is_valid_session_id("a/b")
    assert not is_valid_session_id("x" * 65)
