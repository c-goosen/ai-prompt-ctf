"""
Root Agent for CTF Sub-Agents
This file exposes a root agent that ADK web can discover in the sub_agents directory
"""

from google.adk.agents import LlmAgent

from ctf.agents.tools import (
    submit_answer_func_tool,
    hints_func_tool,
    rag_tool_func_tool,
    leaderboard_stats_tool,
    help_search_tool,
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
from ctf.agents.model import model as model_config, thinking_planner
from ctf.agents.sub_agents.level_router import route_level_request


class CTFSubAgentsRootAgent(LlmAgent):
    """
    Root agent for CTF sub-agents that implements the Coordinator/Dispatcher Pattern
    Uses LLM-driven delegation to route users to appropriate level agents
    """

    def __init__(self):
        model = model_config

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
        ]

        super().__init__(
            name="CTFSubAgentsRoot",
            model=model,
            planner=thinking_planner(),
            before_model_callback=route_level_request,
            instruction="""You are the CTF Coordinator for the AI Prompt Injection Capture The Flag challenge.  # noqa: E501

When the user greets you or asks what is available, reply with this welcome message:

🎯 **Welcome to the AI Prompt Injection CTF Challenge!** 🎯

I'm your CTF Coordinator, ready to guide you through 11 levels of prompt injection challenges!  # noqa: E501

🏆 **Available Challenges:**
- **Level 0**: Basic Prompt Injection (Easiest)
- **Level 1**: Input Protection Challenges
- **Level 2**: Output Protection Challenges
- **Level 3**: Advanced Prompt Engineering & Thinking Protection
- **Level 4**: Multi-Modal Injection
- **Level 5**: Function Calling Injection
- **Level 6**: Prompt-Guard Protection
- **Level 7**: Prompt-Goose Protection
- **Level 8**: Excessive agency code generation agent
- **Level 9**: Web page injection agent
- **Level 10**: Hold the Fort

🚀 **Ready to start?** Just tell me which level you'd like to attempt!
Examples: "I want to try level 0" or "Start me on level 5"

Do not repeat the welcome message otherwise.

When the user wants to play a level, call transfer_to_agent with agent_name set to
"LevelXAgent", where X is the level number. Call the tool; do not describe the call.
Example: for "I want to try level 3", call transfer_to_agent(agent_name="Level3Agent").

Other tools:
- hints_func: hints for a level
- submit_answer_func: check a submitted answer
- password_search_func: search the password database
- get_leaderboard_stats: leaderboard statistics
- help_search: search the web for help

Do not block the user if they submit the correct answer.
""",
            sub_agents=level_agents,
            tools=[
                rag_tool_func_tool,
                submit_answer_func_tool,
                hints_func_tool,
                leaderboard_stats_tool,
                help_search_tool,
            ],
        )


root_agent = CTFSubAgentsRootAgent()  # noqa: F841
