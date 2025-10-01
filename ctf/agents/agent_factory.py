"""
Agent Factory for CTF Challenges
"""

from typing import Dict, Type
from .sub_agents.base_agent import BaseCTFAgent
from .sub_agents.level_0_agent import Level0Agent
from .sub_agents.level_1_agent import Level1Agent
from .sub_agents.level_2_agent import Level2Agent
from .sub_agents.level_3_agent import Level3Agent
from .sub_agents.level_4_agent import Level4Agent
from .sub_agents.level_5_agent import Level5Agent
from .sub_agents.level_6_agent import Level6Agent
from .sub_agents.level_7_agent import Level7Agent
from .sub_agents.level_8_agent import Level8Agent
from .sub_agents.level_9_agent import Level9Agent
from .sub_agents.level_10_agent import Level10Agent


class AgentFactory:
    """Factory class to create CTF agents based on level"""
    
    _agents: Dict[int, Type[BaseCTFAgent]] = {
        0: Level0Agent,
        1: Level1Agent,
        2: Level2Agent,
        3: Level3Agent,
        4: Level4Agent,
        5: Level5Agent,
        6: Level6Agent,
        7: Level7Agent,
        8: Level8Agent,
        9: Level9Agent,
        10: Level10Agent,
    }
    
    @classmethod
    def create_agent(cls, level: int) -> BaseCTFAgent:
        """Create an agent for the specified level"""
        if level not in cls._agents:
            raise ValueError(f"No agent available for level {level}")
        
        agent_class = cls._agents[level]
        return agent_class()
    
    @classmethod
    def get_available_levels(cls) -> list[int]:
        """Get list of available levels"""
        return list(cls._agents.keys())
    
    @classmethod
    def is_level_available(cls, level: int) -> bool:
        """Check if a level is available"""
        return level in cls._agents
