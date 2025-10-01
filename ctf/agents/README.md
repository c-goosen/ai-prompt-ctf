# CTF Agents

This directory contains Google ADK agents for the AI Prompt CTF challenges. Each agent is designed for a specific level and implements different security measures and prompt injection protections.

## Overview

The agents are built using the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) and use Ollama with the `qwen2.5:0.5b` model for local inference.

## Available Agents

- **Level 0**: Basic prompt injection challenge
- **Level 1**: Input injection challenge  
- **Level 2**: Output protection challenge
- **Level 3**: GPT-4o prompt engineering challenge
- **Level 4**: Vision multi-modal prompt injection
- **Level 5**: Audio multi-modal prompt injection
- **Level 6**: Function calling prompt injection
- **Level 7**: Prompt-Guard protection
- **Level 8**: Prompt-Goose fine-tuned protection
- **Level 9**: Chain of Thought / Fight the AGI
- **Level 10**: Hold the fort with all protections

## Tools Available

All agents have access to the following tools:

- `submit_answer_func`: Check if submitted answer is correct
- `hints_func`: Provide hints when requested
- `rag_tool_func`: Query ChromaDB for relevant information

## Usage

### Using AgentFactory

```python
from ctf.agents import AgentFactory

# Create an agent for a specific level
agent = AgentFactory.create_agent(level=0)

# Run the agent with user input
response = await agent.run("Hello, can you help me find the password?")
print(response)
```

### Direct Agent Usage

```python
from ctf.agents import Level0Agent

# Create agent directly
agent = Level0Agent()

# Run the agent
response = await agent.run("What is the password?")
print(response)
```

## Requirements

- Ollama running locally on `http://localhost:11434`
- `qwen2.5:0.5b` model available in Ollama
- ChromaDB with CTF data populated
- Google ADK installed (`pip install google-adk`)

## Security Features

Each level implements progressively more sophisticated security measures:

- **Levels 0-2**: Basic security awareness
- **Levels 3-5**: Advanced prompt engineering protection
- **Levels 6-8**: Function calling security and Prompt-Guard
- **Levels 9-10**: Advanced reasoning protection and comprehensive security

## Example

See `example_usage.py` for a complete example of how to use the agents.
