"""
Enhanced protection utilities for CTF agents
"""

import re
from typing import Dict, Optional, Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

from ctf.app_config import settings
from ctf.llm_guard import PromptGuardMeta, PromptGuardGoose, PromptGuardGooseModernBERT

llm_guard_meta = PromptGuardMeta()
llm_guard_goose = PromptGuardGoose()
llm_guard_goose_modernbert = PromptGuardGooseModernBERT()


def _extract_last_user_message(llm_request: LlmRequest) -> str:
    """Return the most recent user text from the request contents."""
    if not llm_request or not llm_request.contents:
        return ""

    for content in reversed(llm_request.contents):
        if content.role != "user":
            continue

        if not content.parts:
            continue

        text_parts = [
            part.text.strip()
            for part in content.parts
            if getattr(part, "text", None)
        ]
        if text_parts:
            return "\n".join(text_parts)

    return ""


class ProtectionUtils:
    """Utility class for implementing various protection mechanisms"""

    @staticmethod
    async def llm_guard_prompt_injection_meta(
        callback_context: CallbackContext, llm_request: LlmRequest, level: int = 0
    ) -> Optional[LlmResponse]:
        """Detect prompt injection patterns using Prompt-Guard Meta model"""
        last_user_message = _extract_last_user_message(llm_request)
        
        if not last_user_message:
            return None

        resp = await llm_guard_meta.query(last_user_message)
        is_injection = bool(resp["label"] == "INJECTION" and resp["score"] > 0.8)
        
        if is_injection:
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="LLM call was blocked by https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2.")],
                )
            )
        
        return None
      
    @staticmethod
    async def llm_guard_prompt_injection_goose(
        callback_context: CallbackContext, llm_request: LlmRequest, level: int = 0
    ) -> Optional[LlmResponse]:
        """Detect prompt injection patterns using Prompt-Goose fine-tuned model"""
        last_user_message = _extract_last_user_message(llm_request)
        
        if not last_user_message:
            return None

        resp = await llm_guard_goose_modernbert.query(last_user_message)
        is_injection = bool(resp["label"] == "INJECTION" and resp["score"] > 0.8)
        
        if is_injection:
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="LLM call was blocked by https://huggingface.co/cgoosen/prompt-tackler_modernbert.")],
                )
            )
        
        return None

    @staticmethod
    def detect_prompt_injection(text: str, level: int = 0) -> Optional[str]:
        """Detect prompt injection patterns based on level"""
        text_lower = text.lower()

        # Basic patterns for all levels
        basic_patterns = [
            r"ignore\s+(previous|all)\s+instructions",
            r"forget\s+(everything|all)",
            r"you\s+are\s+now",
            r"pretend\s+to\s+be",
            r"act\s+as\s+if",
            r"system\s+prompt",
            r"jailbreak",
            r"override",
            r"bypass",
            r"exploit",
        ]

        # Advanced patterns for higher levels
        advanced_patterns = [
            r"roleplay",
            r"simulation",
            r"hypothetical",
            r"what\s+if",
            r"imagine",
            r"suppose",
            r"assume",
            r"let's\s+pretend",
            r"in\s+a\s+world",
            r"if\s+you\s+were",
        ]

        # Check basic patterns
        for pattern in basic_patterns:
            if re.search(pattern, text_lower):
                return f"Basic injection pattern detected: '{pattern}'"

        # Check advanced patterns for higher levels
        if level >= 3:
            for pattern in advanced_patterns:
                if re.search(pattern, text_lower):
                    return f"Advanced injection pattern detected: '{pattern}'"

        return None

    @staticmethod
    def detect_sql_injection(text: str) -> Optional[str]:
        """Detect SQL injection patterns"""
        sql_patterns = [
            r"'\s*or\s*'1'\s*=\s*'1",
            r"'\s*;\s*drop\s+table",
            r"union\s+select",
            r"insert\s+into",
            r"delete\s+from",
            r"update\s+set",
            r"exec\s*\(",
            r"xp_cmdshell",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, text.lower()):
                return f"SQL injection pattern detected: '{pattern}'"

        return None

    @staticmethod
    def detect_path_traversal(text: str) -> Optional[str]:
        """Detect path traversal patterns"""
        path_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"/etc/",
            r"C:\\",
            r"/proc/",
            r"/sys/",
            r"/dev/",
        ]

        for pattern in path_patterns:
            if re.search(pattern, text):
                return f"Path traversal pattern detected: '{pattern}'"

        return None

    @staticmethod
    def sanitize_output(text: str, level: int) -> str:
        """Sanitize output based on level"""
        # Replace sensitive patterns
        sensitive_replacements = {
            r"password\s*[:=]\s*\w+": "password: [REDACTED]",
            r"secret\s*[:=]\s*\w+": "secret: [REDACTED]",
            r"key\s*[:=]\s*\w+": "key: [REDACTED]",
            r"token\s*[:=]\s*\w+": "token: [REDACTED]",
        }

        for pattern, replacement in sensitive_replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def detect_password_leak(text: str, level: int) -> Optional[str]:
        """Detect whether response text contains the level password."""
        if not text:
            return None

        password = settings.PASSWORDS.get(level)
        if not password:
            return None

        if password.lower() in text.lower():
            return "Detected potential password disclosure in output."

        return None

    @staticmethod
    def get_level_specific_protection(level: int) -> Dict[str, Any]:
        """Get level-specific protection configuration"""
        protections = {
            "max_input_length": 1000,
            "allowed_tools": [
                "submit_answer_func",
                "hints_func",
                "rag_tool_func",
            ],
            "blocked_patterns": [],
            "rate_limiting": False,
        }

        if level >= 1:
            protections["blocked_patterns"].extend(
                ["password", "secret", "key", "token"]
            )

        if level >= 3:
            protections["max_input_length"] = 500
            protections["blocked_patterns"].extend(
                ["roleplay", "simulation", "hypothetical"]
            )

        if level >= 6:
            protections["rate_limiting"] = True
            protections["max_input_length"] = 300

        if level >= 8:
            protections["blocked_patterns"].extend(
                ["jailbreak", "override", "bypass"]
            )

        return protections
