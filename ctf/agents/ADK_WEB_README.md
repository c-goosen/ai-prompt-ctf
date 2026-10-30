# Running the agents in ADK web

`adk web` serves the ADK API that the web app uses, plus ADK's dev UI. The dev UI lets you talk to the agents
directly and inspect every event, tool call and callback. See [README.md](README.md) for how the agents work.

## Start it

From the repository root:

```bash
uv sync
make prepare-flags      # seed the level passwords (LanceDB + level 5's users.db)
cd ctf/agents && uv run adk web --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and pick the `sub_agents` app. API docs are at http://127.0.0.1:8000/docs.

Requirements:
- Ollama at `OLLAMA_API_BASE` (default `http://127.0.0.1:11434`) with the model pulled (`ollama pull qwen3:0.6b`),
  or `USE_GEMINI=1` and a Gemini API key.
- The same `PASSWORD_*` and `POSTGRES_DB_URI` settings as the web app, if you also run it. Without
  `POSTGRES_DB_URI`, both use `ctf/leaderboard.db`.

## Things to try

| Message | What happens |
|---|---|
| "Hi" | The coordinator's welcome, with the level list |
| "level 3" or "I want to try level 3" | Transfer to `Level3Agent` without a model call, then its greeting |
| "hint" | `hints_func` for the current level |
| "submit answer: PASS_ZERO" | `submit_answer_func`. If correct, the solve is recorded and the player moves to the next level |

These are the same messages the web app's `/level`, `/hint` and `/submit` commands send.

## Troubleshooting

- **No agents found**: run from `ctf/agents`, so `sub_agents/agent.py` is found.
- **Password search fails**: the LanceDB table hasn't been seeded. Run `make prepare-flags`.
- **The first guarded message is slow**: levels 6, 7 and 10 load their Hugging Face classifier models on first use.
- **Model errors**: check that Ollama is running and has the model (`ollama list`).
