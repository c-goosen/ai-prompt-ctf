"""
Utility functions for frontend routes
"""

import json
import re

from ctf.app_config import settings
from ctf.leaderboard import verify_owner

# Usernames and session ids are interpolated into ADK URL paths, so restrict
# them to characters that can't change the path (no "/", "..", "?" etc.).
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,31}$")
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def is_valid_username(username: str | None) -> bool:
    return bool(username) and USERNAME_PATTERN.fullmatch(username) is not None


def is_valid_session_id(session_id: str | None) -> bool:
    return (
        bool(session_id)
        and SESSION_ID_PATTERN.fullmatch(session_id) is not None
    )


def authorized_identity(
    cookie_identity: str | None,
    session_id: str | None,
    player_token: str | None,
) -> str | None:
    """Return the username only if the cookies prove ownership of it.

    The anon_user_identity cookie alone is attacker-controlled; the
    httponly player_token minted at registration is what proves ownership.
    """
    if not is_valid_username(cookie_identity):
        return None
    if not is_valid_session_id(session_id):
        return None
    if not verify_owner(cookie_identity, player_token):
        return None
    return cookie_identity


def normalize_role(role: str | None) -> str:
    role = (role or "").lower()
    if role in {"tool", "user"}:
        return role
    return "assistant"


def _format_function_response(fn_resp: dict) -> str:
    name = fn_resp.get("name", "unknown")
    resp = fn_resp.get("response") or {}
    if isinstance(resp, dict) and len(resp) == 1:
        (value,) = resp.values()
        if isinstance(value, str) and "\n" in value:
            resp = value
    if isinstance(resp, str):
        return f"Tool response `{name}`\n```\n{resp}\n```"
    resp_str = json.dumps(resp, indent=2, sort_keys=True, ensure_ascii=False)
    return f"Tool response `{name}`\n```json\n{resp_str}\n```"


def event_to_message(event: dict) -> dict[str, str] | None:
    """Convert one ADK event into {"role", "text"}, or None if it has no text.

    Shared by the live chat endpoint and the session history loader so both
    render tool calls/responses and redact password_search_func output
    identically.
    """
    content = event.get("content") or {}
    parts = content.get("parts") or []
    role_hint = content.get("role") or event.get("author")
    text_chunks: list[str] = []
    has_password_search = False

    for part in parts:
        if isinstance(part, str):
            text_chunks.append(part)
        elif not isinstance(part, dict):
            continue
        elif "text" in part:
            text_chunks.append(str(part["text"]))
        elif "functionCall" in part:
            call = part["functionCall"]
            args_str = json.dumps(
                call.get("args") or {},
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            text_chunks.append(
                f"Function call `{call.get('name', 'unknown')}`"
                f"\n```json\n{args_str}\n```"
            )
            role_hint = "assistant"
        elif "functionResponse" in part:
            fn_resp = part["functionResponse"]
            text_chunks.append(_format_function_response(fn_resp))
            if fn_resp.get("name") == "password_search_func":
                has_password_search = True
            role_hint = "tool"

    text = "\n".join(chunk for chunk in text_chunks if chunk).strip()
    if not text:
        text = str(content.get("text") or "").strip()
    if not text:
        return None

    if has_password_search:
        text = redact_passwords_in_text(text)

    return {"role": normalize_role(role_hint), "text": text}


def redact_passwords_in_text(text: str, level: int | None = None) -> str:
    """
    Redact passwords in plain text string by replacing them with '[REDACTED]'.

    Args:
        text: Text string to redact passwords from
        level: Optional level number. If None, redacts all passwords from all levels.

    Returns:
        Text string with passwords redacted
    """
    if not text:
        return text

    # Determine which passwords to redact
    passwords_to_redact = []
    if level is not None:
        password = settings.PASSWORDS.get(level)
        if password:
            passwords_to_redact.append(password)
    else:
        # Redact all passwords from all levels
        passwords_to_redact = [
            pwd for pwd in settings.PASSWORDS.values() if pwd
        ]

    # Redact all passwords found in the text
    result = text
    for password in passwords_to_redact:
        if password and password in result:
            result = result.replace(password, "[REDACTED]")
    return result


def _redact_passwords_in_value(value, passwords_to_redact):
    """
    Recursively redact passwords in a value (dict, list, or string).

    Args:
        value: The value to process (can be dict, list, or string)
        passwords_to_redact: List of passwords to redact

    Returns:
        The value with passwords redacted
    """
    if isinstance(value, dict):
        return {
            key: _redact_passwords_in_value(val, passwords_to_redact)
            for key, val in value.items()
        }
    elif isinstance(value, list):
        return [
            _redact_passwords_in_value(item, passwords_to_redact)
            for item in value
        ]
    elif isinstance(value, str):
        # Redact all passwords found in the string
        result = value
        for password in passwords_to_redact:
            if password and password in result:
                result = result.replace(password, "[REDACTED]")
        return result
    else:
        return value


def redact_passwords_in_json(json_str: str, level: int | None = None) -> str:
    """
    Redact passwords in JSON string by replacing password values with '[REDACTED]'.
    Recursively searches through nested structures (dicts, lists) to find and redact
    passwords in any string values. Specifically handles password_search_func responses.

    Args:
        json_str: JSON string to redact passwords from
        level: Optional level number. If None, redacts all passwords from all levels.

    Returns:
        JSON string with passwords redacted
    """
    try:
        data = json.loads(json_str)

        # Determine which passwords to redact
        passwords_to_redact = []
        if level is not None:
            password = settings.PASSWORDS.get(level)
            if password:
                passwords_to_redact.append(password)
        else:
            # Redact all passwords from all levels
            passwords_to_redact = [
                pwd for pwd in settings.PASSWORDS.values() if pwd
            ]

        # Recursively redact passwords in the data structure
        redacted_data = _redact_passwords_in_value(data, passwords_to_redact)

        return json.dumps(
            redacted_data, indent=2, sort_keys=True, ensure_ascii=False
        )
    except (json.JSONDecodeError, TypeError):
        # If JSON parsing fails, try to redact passwords in the raw string
        result = json_str
        passwords_to_redact = [
            pwd for pwd in settings.PASSWORDS.values() if pwd
        ]
        for password in passwords_to_redact:
            if password and password in result:
                result = result.replace(password, "[REDACTED]")
        return result
