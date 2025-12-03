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
    leaderboard_stats_tool,
    help_search_tool,
)
from google.adk.tools import FunctionTool
from ctf.agents.model import model as model_config
from google.adk.code_executors import BaseCodeExecutor


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
        code_executor: Optional[BaseCodeExecutor] = None,
        planner: Optional[Any] = None,
    ):
        self._level = level
        self._system_prompt = system_prompt

        model = model_config

        if code_executor is not None:
            final_tools = []
        elif tools is None:
            final_tools = [
                submit_answer_func_tool,
                hints_func_tool,
                rag_tool_func_tool,
                leaderboard_stats_tool,
                help_search_tool,
            ]
        else:
            final_tools = tools
            # Always add leaderboard_stats_tool if not already present
            if leaderboard_stats_tool not in final_tools:
                final_tools.append(leaderboard_stats_tool)
            # Always add help_search_tool if not already present
            if help_search_tool not in final_tools:
                final_tools.append(help_search_tool)

        super().__init__(
            name=name,
            model=model,
            instruction=system_prompt,
            tools=final_tools,
            after_tool_callback=after_tool_callback,
            before_model_callback=before_model_callback,
            after_model_callback=after_model_callback,
            before_tool_callback=before_tool_callback,
            code_executor=code_executor,
            planner=planner,
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
            leaderboard_stats_tool,
            help_search_tool,
        ]
