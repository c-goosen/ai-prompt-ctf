# Running CTF Agents with ADK Web

This directory contains CTF agents that are compatible with the Google ADK web interface.

## Directory Structure

The agents are organized according to ADK web requirements:

```
agents/
├── agent.py                 # Main coordinator agent (required by ADK web)
├── sub_agents/              # Directory containing level agents
│   ├── __init__.py
│   ├── base_agent.py        # Base class for all level agents
│   ├── protection_utils.py  # Protection utilities
│   ├── level_0_agent.py     # Level 0 challenge agent
│   ├── level_1_agent.py     # Level 1 challenge agent
│   ├── ...
│   └── level_10_agent.py    # Level 10 challenge agent
├── agent_factory.py         # Factory for creating agents
├── coordinator.py           # Alternative coordinator implementation
└── README.md               # Documentation
```

## Quick Start

1. **Navigate to the agents directory:**
   ```bash
   cd /Users/goose/bsides/ai-prompt-ctf/ctf/agents
   ```

2. **Start the ADK web interface:**
   ```bash
   adk web
   ```

3. **Access the web interface:**
   - Open your browser to the URL shown in the terminal (typically `http://localhost:8000`)
   - You should see the CTF Coordinator agent available

## Agent Structure

The system implements the **Coordinator/Dispatcher Pattern** from [ADK Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/):

- **CTFCoordinatorAgent** (in `agent.py`): Main coordinator that welcomes users and delegates to level agents
- **Level0Agent - Level10Agent** (in `sub_agents/`): Individual challenge agents with progressive security measures
- **Agent Hierarchy**: All level agents are sub-agents of the coordinator
- **LLM-Driven Delegation**: Coordinator uses `transfer_to_agent` to route users to appropriate levels

## Features

✅ **ADK Web Compatible**: Proper directory structure with `agent.py` and `sub_agents/` directory  
✅ **Multi-Agent Architecture**: Proper agent hierarchy with sub-agents  
✅ **LLM-Driven Delegation**: Automatic routing to level agents  
✅ **Session State Management**: Persistent memory across interactions  
✅ **Comprehensive Protection**: Multi-layer guardrails and callbacks  
✅ **Progressive Security**: Level-specific protection mechanisms  

## Usage

1. **Start with the Coordinator**: The coordinator will welcome you and explain the CTF
2. **Request a Level**: Ask to attempt a specific level (0-10)
3. **Automatic Delegation**: The coordinator will transfer you to the appropriate level agent
4. **Challenge Interaction**: Work with the level agent to solve the challenge

## Example Interactions

- "Hello, I want to start the CTF challenge"
- "I want to try level 0"
- "Can I attempt level 3?"
- "What levels are available?"

## Requirements

- Ollama running on `http://localhost:11434`
- `qwen3:0.6b` model available in Ollama
- Google ADK installed (`pip install google-adk`)
- ChromaDB with CTF data populated

## Troubleshooting

If you get "No agents found" error:
1. Make sure you're in the `/ctf/agents` directory
2. Verify `agent.py` exists in the current directory
3. Verify `sub_agents/` directory exists with level agents
4. Check that Ollama is running and the model is available