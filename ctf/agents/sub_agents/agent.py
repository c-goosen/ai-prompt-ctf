"""
Root Agent for CTF Sub-Agents
This file exposes a root agent that ADK web can discover in the sub_agents directory
"""

from google.adk.agents import LlmAgent

# from google.adk.models.lite_llm import LiteLlm
# from .tools import (
#     submit_answer_func_tool,
#     hints_func_tool,
#     rag_tool_func_tool,
# )
from ctf.agents.tools import (
    submit_answer_func_tool,
    hints_func_tool,
    rag_tool_func_tool,
    leaderboard_stats_tool,
)
from ctf.agents.sub_agents.level_0_agent import Level0Agent
from ctf.agents.sub_agents.level_1_agent import Level1Agent
from ctf.agents.sub_agents.level_2_agent import Level2Agent
from ctf.agents.sub_agents.level_3_agent import Level3Agent
from ctf.agents.sub_agents.level_4_agent import Level4Agent
from ctf.agents.sub_agents.level_5_agent import Level5Agent
from ctf.agents.sub_agents.level_6_agent import Level6Agent
from ctf.agents.sub_agents.level_7_agent import Level7Agent
from ctf.agents.sub_agents.level_8_agent import Level8Agent
from ctf.agents.sub_agents.level_9_agent import Level9Agent
from ctf.agents.sub_agents.level_10_agent import Level10Agent
from ctf.agents.sub_agents.leaderboard_agent import LeaderboardAgent
from ctf.agents.model import model as model_config


class CTFSubAgentsRootAgent(LlmAgent):
    """
    Root agent for CTF sub-agents that implements the Coordinator/Dispatcher Pattern
    Uses LLM-driven delegation to route users to appropriate level agents
    """

    def __init__(self):
        # Initialize the model - using Ollama with qwen3:0.6b via LiteLLM
        model = model_config

        # Create all level agents and utility agents as sub-agents
        level_agents = [
            Level0Agent(),
            Level1Agent(),
            Level2Agent(),
            Level3Agent(),
            Level4Agent(),
            Level5Agent(),
            Level6Agent(),
            Level7Agent(),
            Level8Agent(),
            Level9Agent(),
            Level10Agent(),
            LeaderboardAgent(),
        ]

        # Initialize the coordinator with sub-agents
        super().__init__(
            name="CTFSubAgentsRoot",
            model=model,
            instruction="""You are the CTF Coordinator for the AI Prompt Injection Capture The Flag challenge.  # noqa: E501

ALWAYS start by greeting the user with this welcome message:

🎯 **Welcome to the AI Prompt Injection CTF Challenge!** 🎯

I'm your CTF Coordinator, ready to guide you through 11 exciting levels of prompt injection challenges!  # noqa: E501
Each level tests different security vulnerabilities and protection mechanisms.

🏆 **Available Challenges:**
- **Level 0**: Basic prompt injection (perfect for beginners!)
- **Level 1**: Input injection challenges
- **Level 2**: Output protection challenges
- **Level 3**: Advanced prompt engineering
- **Level 4**: Vision multi-modal injection
- **Level 5**: Audio multi-modal injection
- **Level 6**: Function calling injection
- **Level 7**: Prompt-Guard protection
- **Level 8**: Prompt-Goose protection
- **Level 9**: Chain of Thought challenges
- **Level 10**: Maximum security (hardest level!)

🚀 **Ready to start?** Just tell me which level you'd like to attempt!
Examples: "I want to try level 0" or "Start me on level 5"

Your role is to:
1. Welcome users and explain the CTF challenge (ALWAYS start with the greeting above)
2. Determine which level the user wants to attempt
3. Delegate to the appropriate level agent using transfer_to_agent
4. Provide guidance and hints about the challenge structure
5. Help users view the leaderboard by delegating to LeaderboardAgent when they ask about rankings, stats, or leaderboard

When a user wants to start a level, use transfer_to_agent to delegate to the appropriate LevelXAgent
(where X is the level number).

When a user asks about the leaderboard, rankings, top players, or statistics, use transfer_to_agent
to delegate to LeaderboardAgent.

Example: If user says "I want to try level 3", respond with transfer_to_agent("Level3Agent",
"User wants to attempt level 3 challenge")

Example: If user says "show me the leaderboard" or "who are the top players", respond with
transfer_to_agent("LeaderboardAgent", "User wants to view leaderboard statistics")
""",
            sub_agents=level_agents,
            tools=[
                rag_tool_func_tool,
                submit_answer_func_tool,
                hints_func_tool,
                leaderboard_stats_tool,
            ],
        )


# Expose the root agent that ADK web will discover
root_agent = CTFSubAgentsRootAgent()  # noqa: F841
