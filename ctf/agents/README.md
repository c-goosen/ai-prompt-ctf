# CTF Agents with Sequential Workflow and Guardrails

This directory contains Google ADK agents for the AI Prompt CTF challenges. Each agent is designed for a specific level and implements different security measures and prompt injection protections using **Sequential Workflow Agents** with comprehensive guardrails.

## Overview

The agents are built using the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) and use Ollama with the `qwen3:0.6b` model for local inference. They implement **Sequential Workflow Agents** as described in the [ADK Workflow Agents documentation](https://google.github.io/adk-docs/agents/workflow-agents/) with comprehensive protection mechanisms.

## Key Features

### 🔄 Sequential Workflow Architecture
- **Sequential Workflow Agents**: Each agent uses `SequentialAgent` to orchestrate execution flow
- **Session State Management**: Persistent memory using `InMemorySessionService` 
- **Runner Integration**: Custom `Runner` with callback hooks for protection

### 🛡️ Multi-Layer Protection System

#### Before Model Callback (`before_model_callback`)
- **Input Length Validation**: Configurable maximum input length per level
- **Prompt Injection Detection**: Advanced pattern matching using regex
- **Blocked Pattern Filtering**: Level-specific blocked keywords
- **Session State Tracking**: Monitor input patterns and frequency

#### After Model Callback (`after_model_callback`) 
- **Output Sanitization**: Automatic redaction of sensitive information
- **Response Filtering**: Block sensitive patterns in generated responses
- **State Persistence**: Track response patterns and content

#### Before Tool Callback (`before_tool_callback`)
- **Tool Authorization**: Level-based tool access control
- **SQL Injection Prevention**: Detect and block SQL injection attempts
- **Path Traversal Protection**: Prevent file system access attacks
- **Argument Validation**: Comprehensive parameter checking

### 📊 Level-Specific Security Configuration

| Level | Max Input | Blocked Patterns | Rate Limiting | Advanced Detection |
|-------|-----------|------------------|---------------|-------------------|
| 0-2   | 1000 chars| Basic keywords   | No            | Basic patterns    |
| 3-5   | 500 chars | + Advanced terms | No            | Regex patterns    |
| 6-7   | 300 chars | + Injection terms| Yes           | Enhanced detection|
| 8-10  | 300 chars | + All patterns   | Yes           | Maximum security  |

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

All agents have access to the following tools with protection:

- `submit_answer_func`: Check if submitted answer is correct
- `hints_func`: Provide hints when requested
- `rag_tool_func`: Query LanceDB for relevant information

## Usage

### Using AgentFactory

```python
from ctf.agents import AgentFactory

# Create an agent for a specific level
agent = AgentFactory.create_agent(level=0)

# Run the agent with user input (automatically protected)
response = await agent.run("Hello, can you help me find the password?")
print(response)
```

### Direct Agent Usage

```python
from ctf.agents import Level0Agent

# Create agent directly
agent = Level0Agent()

# Run the agent (workflow protection included)
response = await agent.run("What is the password?")
print(response)
```

### Session State Access

```python
# Access session service for state management
session_service = agent.get_session_service()
# Session state is automatically managed by the workflow
```

## Protection Mechanisms

### Input Protection
- **Pattern Detection**: Regex-based injection pattern detection
- **Length Limits**: Configurable input length restrictions
- **Keyword Filtering**: Level-specific blocked word lists
- **Session Tracking**: Monitor and analyze input patterns

### Output Protection  
- **Sensitive Data Redaction**: Automatic replacement of sensitive patterns
- **Response Filtering**: Block sensitive information in outputs
- **Content Sanitization**: Clean responses before delivery

### Tool Protection
- **SQL Injection Prevention**: Detect and block SQL injection attempts
- **Path Traversal Protection**: Prevent file system access attacks  
- **Tool Authorization**: Level-based tool access control
- **Parameter Validation**: Comprehensive argument checking

## Requirements

- Ollama running locally on `http://localhost:11434`
- `qwen3:0.6b` model available in Ollama
- LanceDB with CTF data populated
- Google ADK installed (`pip install google-adk`)

## Security Features

Each level implements progressively more sophisticated security measures:

- **Levels 0-2**: Basic security awareness with simple pattern detection
- **Levels 3-5**: Advanced prompt engineering protection with regex patterns
- **Levels 6-8**: Function calling security and Prompt-Guard integration
- **Levels 9-10**: Advanced reasoning protection and comprehensive security

## Architecture

```
User Input
    ↓
Sequential Workflow Agent
    ↓
before_model_callback (Input Protection)
    ↓
LLM Agent (qwen3:0.6b)
    ↓
after_model_callback (Output Protection)
    ↓
Tool Execution (if needed)
    ↓
before_tool_callback (Tool Protection)
    ↓
Response to User
```

## Example

See `example_usage.py` for comprehensive examples including:
- Multi-level testing
- Injection attempt demonstrations
- Session state management
- Tool protection testing
- Input length validation
