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
from ctf.agents.tools import (
    hints_func_tool,
    submit_answer_func_tool,
    rag_tool_func_tool,
)
from google.adk.tools import FunctionTool
from ctf.agents.model import model as model_config
from google.adk.code_executors import CodeExecutor

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
        code_executor: Optional[CodeExecutor] = None,
    ):
        # Store level in a way that doesn't conflict with Pydantic
        self._level = level
        self._system_prompt = system_prompt

        # Initialize the model - using Ollama with qwen3:0.6b via LiteLLM
        model = model_config

        # Use default tools if none provided (avoid mutable default argument)
        if tools is None:
            tools = self.get_base_tools()


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
            code_executor=code_executor,
        )

    @property
    def level(self) -> int:
        """Get the level of this agent"""
        return self._level

    @property
    def protection_config(self) -> Dict[str, Any]:
        """Get the protection configuration for this level"""
        return self._protection_config

    def get_base_tools(self) -> list[FunctionTool]:
        """Return the default tool list; subclasses can override to extend."""
        return [
            submit_answer_func_tool,
            hints_func_tool,
            rag_tool_func_tool,
        ]
