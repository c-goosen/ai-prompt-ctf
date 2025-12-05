"""
Utility functions for frontend routes
"""

import json

from ctf.app_config import settings


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
