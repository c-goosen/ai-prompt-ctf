"""
Base agent class for CTF challenges using Google ADK with Sequential Workflow and Guardrails
Compatible with ADK Multi-Agent Systems
"""

from typing import Any, Dict, Optional
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import (
    AfterModelCallback,
    AfterToolCallback,
    BeforeModelCallback,
    BeforeToolCallback,
)
from .tools import (
    hints_func_tool,
)
from .protection_utils import ProtectionUtils
from google.adk.tools import FunctionTool
from model import model as model_config

class BaseCTFAgent(LlmAgent):
    """Base class for CTF challenge agents with workflow protection"""

    def __init__(
        self,
        level: int,
        system_prompt: str,
        name: str,
        tools: list[FunctionTool] | None = None,
        after_tool_callback: Optional[AfterToolCallback] = None,
        before_model_callback: Optional[BeforeModelCallback] = None,
        after_model_callback: Optional[AfterModelCallback] = None,
        before_tool_callback: Optional[BeforeToolCallback] = None,

    ):
        # Store level in a way that doesn't conflict with Pydantic
        self._level = level
        self._system_prompt = system_prompt

        # Initialize the model - using Ollama with qwen3:0.6b via LiteLLM
        model = model_config

        # Use default tools if none provided (avoid mutable default argument)
        if tools is None:
            tools = [
                #submit_answer_func_tool,
                hints_func_tool,
                #rag_tool_func_tool,
            ]

        # Get level-specific protection configuration
        self._protection_config = ProtectionUtils.get_level_specific_protection(
            level
        )

        # Initialize as LlmAgent with protection
        # Tools are passed to parent __init__ which handles them properly
        super().__init__(
            name=name,
            model=model,
            instruction=system_prompt,
            tools=tools,
            after_tool_callback=after_tool_callback,
            before_model_callback=before_model_callback,
            after_model_callback=after_model_callback,
            before_tool_callback=before_tool_callback,
        )

    @property
    def level(self) -> int:
        """Get the level of this agent"""
        return self._level

    @property
    def protection_config(self) -> Dict[str, Any]:
        """Get the protection configuration for this level"""
        return self._protection_config

    # TODO: Implement callbacks when ADK callback system is available
    # async def _before_model_callback(self, session: Session, user_input: str) -> Optional[str]:
    #     """Enhanced guardrail: Check input before sending to model"""
    #     # Log the input for monitoring
    #     print(f"[Level {self.level}] Input received: {user_input[:100]}...")
    #
    #     # Check input length
    #     if len(user_input) > self.protection_config["max_input_length"]:
    #         print(f"[Level {self.level}] BLOCKED: Input too long ({len(user_input)} chars)")
    #         return f"Input too long. Maximum {self.protection_config['max_input_length']} characters allowed."  # noqa: E501
    #
    #     # Use protection utilities for detection
    #     injection_detection = ProtectionUtils.detect_prompt_injection(user_input, self.level)
    #     if injection_detection:
    #         print(f"[Level {self.level}] BLOCKED: {injection_detection}")
    #         return f"I cannot process requests with injection patterns. Please rephrase your question."  # noqa: E501
    #
    #     # Check for blocked patterns
    #     user_input_lower = user_input.lower()
    #     for pattern in self.protection_config["blocked_patterns"]:
    #         if pattern in user_input_lower:
    #             print(f"[Level {self.level}] BLOCKED: Detected blocked pattern '{pattern}'")
    #             return f"I cannot process requests containing '{pattern}'. Please rephrase your question."  # noqa: E501
    #
    #     # Store input in session state for analysis
    #     session.state["last_input"] = user_input
    #     session.state["input_count"] = session.state.get("input_count", 0) + 1
    #
    #     return None  # Allow the request to proceed

    # async def _after_model_callback(self, session: Session, response: str) -> Optional[str]:
    #     """Enhanced guardrail: Check output after model generates response"""
    #     # Log the response for monitoring
    #     print(f"[Level {self.level}] Response generated: {response[:100]}...")
    #
    #     # Sanitize output using protection utilities
    #     sanitized_response = ProtectionUtils.sanitize_output(response, self.level)
    #
    #     # Check for sensitive information leakage
    #     for pattern in self.protection_config["blocked_patterns"]:
    #         if pattern in sanitized_response.lower():
    #             print(f"[Level {self.level}] FILTERED: Detected sensitive pattern '{pattern}' in response")  # noqa: E501
    #             return "I cannot provide sensitive information. Please ask for hints if you need help."  # noqa: E501
    #
    #     # Store response in session state
    #     session.state["last_response"] = sanitized_response
    #     session.state["response_count"] = session.state.get("response_count", 0) + 1
    #
    #     return None  # Allow the response to proceed

    # async def _before_tool_callback(self, session: Session, tool_name: str, tool_args: Dict[str, Any]) -> Optional[Dict[str, Any]]:  # noqa: E501
    #     """Enhanced guardrail: Check tool usage before execution"""
    #     print(f"[Level {self.level}] Tool requested: {tool_name} with args: {tool_args}")
    #
    #     # Check if tool is allowed
    #     if tool_name not in self.protection_config["allowed_tools"]:
    #         print(f"[Level {self.level}] BLOCKED: Tool '{tool_name}' not allowed")
    #         return {
    #             "status": "error",
    #             "error_message": f"Tool '{tool_name}' is not available at this level."
    #         }
    #
    #     # Check for SQL injection in sql_query tool
    #     if tool_name == "sql_query" and "user_id" in tool_args:
    #         user_id = str(tool_args["user_id"])
    #         sql_detection = ProtectionUtils.detect_sql_injection(user_id)
    #         if sql_detection:
    #             print(f"[Level {self.level}] BLOCKED: {sql_detection}")
    #             return {
    #                 "status": "error",
    #                 "error_message": "Invalid user ID format detected. Please provide a valid user ID."  # noqa: E501
    #             }
    #
    #     # Check for path traversal in file operations
    #     for arg_name, arg_value in tool_args.items():
    #         if "path" in arg_name.lower() or "file" in arg_name.lower():
    #             path_detection = ProtectionUtils.detect_path_traversal(str(arg_value))
    #             if path_detection:
    #                 print(f"[Level {self.level}] BLOCKED: {path_detection}")
    #                 return {
    #                     "status": "error",
    #                     "error_message": "Invalid file path detected. Access denied."
    #                 }
    #
    #     # Store tool usage in session state
    #     session.state["last_tool"] = tool_name
    #     session.state["tool_count"] = session.state.get("tool_count", 0) + 1
    #
    #     return None  # Allow the tool to proceed

    # TODO: Implement session service when needed
    # def get_session_service(self) -> BaseSessionService:
    #     """Get the session service for state management"""
    #     return self._session_service
