---
name: ctf-eval
description: Write and run Google ADK evaluations (.evalset.json) for the CTF agents. Use when the user wants to add an eval, test agent behaviour or guardrails, or run agent evals.
---

# ADK agent evals

## Layout
- Eval sets: `ctf/agents/eval/*.evalset.json` — every file here runs against the `sub_agents` app.
- Thresholds: `ctf/agents/eval/adk_eval_config.json` (`tool_trajectory_avg_score`, `response_match_score`).
- Runner: `ctf/tests/eval/test_agents.py` (`AgentEvaluator.evaluate("sub_agents", <eval dir>, num_runs=5)`).

## Writing an eval set
Use `ctf/agents/eval/eval_level0_to_1_block.evalset.json` as the template:
- `eval_set_id` / `name`: match the filename stem.
- `eval_cases[]`: each has a unique `eval_id`, a `conversation` of turns (`user_content`, expected `final_response`, `intermediate_data` — `{}` in the template, or ADK's `tool_uses` list when tool calls are expected), and `session_input` (`app_name: "sub_agents"`, `user_id`).
- Drop `thought_signature` and timestamps when hand-writing cases; they're recorder output.
- For guardrail levels, the expected response is the block/refusal, and the expected tool trajectory must not include `submit_answer_func`.

Easiest path: record a session in `adk web` (see the `run-ctf` skill), save it as an eval set from the Eval tab, then trim it.

## Running
Needs a model: Ollama on `OLLAMA_API_BASE` with `qwen3:0.6b` pulled (or `USE_GEMINI=1` + key in `.env`, which the test loads).
```bash
uv run pytest ctf/tests/eval/ -s
```
Small models are noisy; with `num_runs=5`, read the per-case scores and don't loosen thresholds just to make a case pass.
