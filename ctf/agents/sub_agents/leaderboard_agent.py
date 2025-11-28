"""
Leaderboard Agent - Displays CTF leaderboard statistics
"""

from google.adk.agents import LlmAgent

from ctf.agents.model import model as model_config
from ctf.agents.tools import leaderboard_stats_tool


class LeaderboardAgent(LlmAgent):
    """Agent that displays leaderboard statistics for the CTF challenge"""

    def __init__(self):
        # Initialize the model - using Ollama with qwen3:0.6b via LiteLLM
        model = model_config

        super().__init__(
            name="LeaderboardAgent",
            model=model,
            instruction="""You are the Leaderboard Assistant for the AI Prompt Injection
CTF Challenge.

Your role is to help users view and understand the CTF leaderboard statistics.

When a user asks about the leaderboard, rankings, top players, or statistics,
use the get_leaderboard_stats tool to retrieve and display the current
leaderboard information.

Always present the information in a clear, friendly, and organized manner. Include:
- Summary statistics (total players, total completions)
- Top players with their progress
- Recent completions

Be helpful and encourage users to compete and improve their rankings!""",
            tools=[leaderboard_stats_tool],
        )
