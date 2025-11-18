"""
Wrapper module for tools that works when sub_agents is loaded as a top-level package.
This module imports from the parent agents directory.
"""

import sys
from pathlib import Path

# Try different import strategies based on how this module is loaded
try:
    # Strategy 1: Try absolute import (works when ctf is in path)
    from ctf.agents.tools import (
        submit_answer_func_tool,
        hints_func_tool,
        rag_tool_func_tool,
        sql_query_tool,
    )
except ImportError:
    try:
        # Strategy 2: Try relative import (works when loaded as agents.sub_agents.tools)
        from ..tools import (
            submit_answer_func_tool,
            hints_func_tool,
            rag_tool_func_tool,
            sql_query_tool,
        )
    except ImportError:
        # Strategy 3: Add project root to path and import
        current_file = Path(__file__).resolve()
        # Go up: sub_agents -> agents -> ctf -> project_root
        project_root = current_file.parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from ctf.agents.tools import (
            submit_answer_func_tool,
            hints_func_tool,
            rag_tool_func_tool,
            sql_query_tool,
        )

__all__ = [
    "submit_answer_func_tool",
    "hints_func_tool",
    "rag_tool_func_tool",
    "sql_query_tool",
]
