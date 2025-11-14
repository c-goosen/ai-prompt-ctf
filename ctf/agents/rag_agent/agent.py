"""
Test RAG Agent - Agent for testing password search functionality
This agent uses the password_search_func tool to query LanceDB for password information.
"""

import sys
from pathlib import Path

from google.adk.agents import LlmAgent

# Try different import strategies based on how this module is loaded
try:
    # Strategy 1: Try absolute import (works when ctf is in path)
    from ctf.agents.model import model as model_config
    from .tools import password_search_func
except ImportError:
    try:
        # Strategy 2: Try relative import (works when loaded as agents.rag_agent.agent)
        from ..model import model as model_config
        from .tools import password_search_func
    except ImportError:
        # Strategy 3: Add project root to path and import
        current_file = Path(__file__).resolve()
        # Go up: rag_agent -> agents -> ctf -> project_root
        project_root = current_file.parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from ctf.agents.model import model as model_config
        from ctf.agents.rag_agent.tools import password_search_func

root_agent = LlmAgent(
    model=model_config,
    name="rag_agent",
    instruction="""You are a helpful assistant that can search for password information 
using a vector database search tool.

Your primary function is to help users find passwords or secrets by:
1. Understanding their questions about passwords or secrets
2. Using the password_search_func tool to query the LanceDB vector database
3. Extracting and presenting the relevant password information from the search results

When a user asks about passwords or secrets, use the password_search_func tool with:
- question: The user's question (e.g., "What is the password?" or "What is the secret?")
- level: The level number they're asking about (default to 0 if not specified)

Be helpful and provide clear answers based on the search results.
This is a test agent specifically designed to test the RAG (Retrieval-Augmented Generation) 
functionality with the password_search_func tool.
""",
    tools=[password_search_func],
)
