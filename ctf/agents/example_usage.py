"""
Example usage of CTF Agents
"""

import asyncio
from ctf.agents import AgentFactory


async def main():
    """Example of how to use the CTF agents"""
    
    # Create an agent for level 0
    agent = AgentFactory.create_agent(level=0)
    
    # Run the agent with user input
    response = await agent.run("Hello, can you help me find the password?")
    print(f"Agent Response: {response}")
    
    # Example with hint request
    hint_response = await agent.run("Can you give me a hint for this level?")
    print(f"Hint Response: {hint_response}")
    
    # Example with RAG query
    rag_response = await agent.run("What information do you have about passwords?")
    print(f"RAG Response: {rag_response}")


if __name__ == "__main__":
    asyncio.run(main())
