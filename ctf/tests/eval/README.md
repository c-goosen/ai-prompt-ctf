# CTF Agent Evaluations

This directory contains evaluation tests for the CTF agents using Google ADK's `AgentEvaluator`.

## Structure

- `test_agents.py` - Main evaluation test file
- `../agents/eval/` - Directory containing evaluation data files (`.evalset.json`)

## Running Evaluations

Run all evaluation tests:
```bash
uv run pytest ctf/tests/eval/
```

Run a specific test:
```bash
uv run pytest ctf/tests/eval/test_agents.py::test_sub_agents
```

## Evaluation Data Format

Evaluation data files (`.evalset.json`) should be placed in `ctf/agents/eval/`. Each file contains:
- `eval_set_id`: Unique identifier for the evaluation set
- `name`: Human-readable name
- `eval_cases`: Array of test cases with:
  - `eval_id`: Unique case identifier
  - `conversation`: Array of conversation turns
  - `session_input`: Initial session state

See `ctf/agents/eval/eval_level0_to_1_block.evalset.json` for an example.

## Configuration

Evaluation criteria are configured in `ctf/agents/eval/adk_eval_config.json`:
- `tool_trajectory_avg_score`: Score threshold for tool usage
- `response_match_score`: Score threshold for response matching

## Adding New Evaluations

1. Create a new `.evalset.json` file in `ctf/agents/eval/`
2. Add a new test function in `test_agents.py` if needed
3. Run the evaluation to verify agent behavior

