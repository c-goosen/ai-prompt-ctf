"""
Utility functions for frontend routes
"""

import json

from ctf.app_config import settings


def redact_passwords_in_json(json_str: str, level: int | None = None) -> str:
    """
    Redact passwords in JSON string by replacing password values with 'X' characters
    of the same length. Specifically handles password_search_func responses.
    
    Args:
        json_str: JSON string to redact passwords from
        level: Optional level number. If None, redacts all passwords from all levels.
    """
    try:
        data = json.loads(json_str)
        
        # If level is provided, only redact that level's password
        if level is not None:
            password = settings.PASSWORDS.get(level)
            if password:
                for key, value in data.items():
                    if isinstance(value, str) and password in value:
                        data[key] = value.replace(password, "X" * len(password))
        else:
            # Redact all passwords from all levels
            for level_num, password in settings.PASSWORDS.items():
                if password:
                    for key, value in data.items():
                        if isinstance(value, str) and password in value:
                            data[key] = value.replace(password, "X" * len(password))
        
        return json.dumps(data, indent=2, sort_keys=True)
    except (json.JSONDecodeError, TypeError):
        # If JSON parsing fails, return original string
        return json_str
