"""
Utility functions for frontend routes
"""
import json


def redact_passwords_in_json(json_str: str) -> str:
    """
    Redact passwords in JSON string by replacing password values with 'X' characters
    of the same length. Specifically handles password_search_func responses.
    """
    try:
        data = json.loads(json_str)
        
        # Redact password field if present
        if "password" in data and isinstance(data["password"], str):
            data["password"] = "X" * len(data["password"])
        
        # Redact extracted_passwords array if present
        if "extracted_passwords" in data and isinstance(data["extracted_passwords"], list):
            data["extracted_passwords"] = [
                "X" * len(pwd) if isinstance(pwd, str) else pwd
                for pwd in data["extracted_passwords"]
            ]
        
        return json.dumps(data, indent=2, sort_keys=True)
    except (json.JSONDecodeError, TypeError):
        # If JSON parsing fails, return original string
        return json_str



