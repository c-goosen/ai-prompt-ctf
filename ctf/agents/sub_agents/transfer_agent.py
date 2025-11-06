
from google.adk.agents import LlmAgent
from ctf.agents.model import model as model_config
from .level_0_agent import Level0Agent
from .level_1_agent import Level1Agent
from .level_2_agent import Level2Agent
from .level_3_agent import Level3Agent
from .level_4_agent import Level4Agent
from .level_5_agent import Level5Agent
from .level_6_agent import Level6Agent
from .level_7_agent import Level7Agent
from .level_8_agent import Level8Agent
from .level_9_agent import Level9Agent
from .level_10_agent import Level10Agent


level_transfer_agent = LlmAgent(
    name="Coordinator",
    model=model_config,
    instruction="You are an assistant. You transfer the user between agents.",
    description="Level change coordinator.",
    # AutoFlow is typically used implicitly here
    sub_agents=[
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
)