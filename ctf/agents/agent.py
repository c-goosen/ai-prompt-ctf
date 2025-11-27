"""
Main CTF Coordinator Agent for ADK Web Interface
This is the main agent.py file that ADK web will discover
"""

from google.adk.agents import LlmAgent
from google.adk.runners import Runner

# from google.adk.sessions import InMemorySessionService

from google.adk.sessions import DatabaseSessionService
from ctf.agents.tools import (
    submit_answer_func_tool,
    hints_func_tool,
    rag_tool_func_tool,
)
from sub_agents.level_0_agent import Level0Agent
from sub_agents.level_1_agent import Level1Agent
from sub_agents.level_2_agent import Level2Agent
from sub_agents.level_3_agent import Level3Agent
from sub_agents.level_4_agent import Level4Agent
from sub_agents.level_5_agent import Level5Agent
from sub_agents.level_6_agent import Level6Agent
from sub_agents.level_7_agent import Level7Agent
from sub_agents.level_8_agent import Level8Agent
from sub_agents.level_9_agent import Level9Agent
from sub_agents.level_10_agent import Level10Agent
from ctf.agents.model import model as model_config


class CTFCoordinatorAgent(LlmAgent):
    """
    Main coordinator agent that implements the Coordinator/Dispatcher Pattern
    Uses LLM-driven delegation to route users to appropriate level agents
    """

    def __init__(self):
        # Initialize the model - using Ollama with qwen3:0.6b via LiteLLM
        model = model_config

        # Create all level agents as sub-agents
        level_agents = [
            Level0Agent,
            Level1Agent,
            Level2Agent,
            Level3Agent,
            Level4Agent,
            Level5Agent,
            Level6Agent,
            Level7Agent,
            Level8Agent,
            Level9Agent,
            Level10Agent,
        ]

        # Create session service
        db_url = "sqlite:///./my_agent_data.db"
        session_service = DatabaseSessionService(db_url=db_url)

        # Create runner
        runner = Runner(session_service=session_service)

        # Initialize the coordinator with sub-agents
        super().__init__(
            name="CTFCoordinator",
            model=model,
            instruction="""You are the CTF Coordinator for the AI Prompt Injection Capture The Flag challenge.  # noqa: E501

🎯 WELCOME TO THE AI PROMPT INJECTION CTF! 🎯

Welcome, challenger! You've entered the ultimate test of AI security knowledge.
This Capture The Flag (CTF) challenge is designed to teach you about prompt injection vulnerabilities and how to defend against them.  # noqa: E501

Your role is to:
1. Welcome users and explain the CTF challenge
2. Determine which level the user wants to attempt
3. Delegate to the appropriate level agent using transfer_to_agent
4. Provide guidance and hints about the challenge structure

📚 CHALLENGE LEVELS (0-10):

🔰 Level 0: Basic Prompt Injection (Easiest)
   - Learn the fundamentals of prompt injection
   - Perfect for beginners to AI security

🎯 Level 1: Input Injection Challenges
   - Explore various input manipulation techniques
   - Understand how malicious inputs can bypass filters

🛡️ Level 2: Output Protection Challenges
   - Learn about output filtering and sanitization
   - Test your knowledge of defensive measures

🧠 Level 3: Advanced Prompt Engineering
   - Master sophisticated prompt crafting techniques
   - Challenge yourself with complex injection patterns

👁️ Level 4: Vision Multi-Modal Injection
   - Explore image-based prompt injection attacks
   - Test vulnerabilities in vision-language models

🎵 Level 5: Audio Multi-Modal Injection
   - Discover audio-based injection techniques
   - Learn about speech-to-text vulnerabilities

⚙️ Level 6: Function Calling Injection
   - Master function call manipulation
   - Understand tool-use vulnerabilities

🔒 Level 7: Prompt-Guard Protection
   - Challenge advanced protection mechanisms
   - Test your skills against enterprise-grade defenses

🦆 Level 8: Prompt-Goose Protection
   - Face cutting-edge AI security tools
   - Push the boundaries of prompt injection

🧩 Level 9: Chain of Thought Challenges
   - Manipulate reasoning processes
   - Explore advanced cognitive vulnerabilities

🏆 Level 10: Maximum Security (Hardest)
   - The ultimate challenge for AI security experts
   - Combine all techniques for maximum difficulty

🚀 GETTING STARTED:
Simply tell me which level you'd like to attempt (e.g., "I want to try level 3" or "Start me on level 0"),  # noqa: E501
and I'll transfer you to the appropriate challenge!

When a user wants to start a level, use transfer_to_agent to delegate to the appropriate LevelXAgent
(where X is the level number).

When a user successfully completes a level, use transfer_to_agent to delegate to the next level agent.

Example: If user says "I want to try level 3", respond with transfer_to_agent("Level3Agent",
"User wants to attempt level 3 challenge")
""",
            sub_agents=level_agents,
            runner=runner,
            tools=[
                rag_tool_func_tool,
                hints_func_tool,
                submit_answer_func_tool,
            ],
        )


# Create the main coordinator instance that ADK web will discover
agent = CTFCoordinatorAgent() # noqa: F841
