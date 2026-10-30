# CTF agents

The CTF's agents, built with the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/). The ADK
app is `sub_agents`: a coordinator plus one agent per level (0-10). Each level agent guards a password. The web app
in `../../web` talks to it over the ADK API server (see [ADK_INTEGRATION.md](../../ADK_INTEGRATION.md)), and
[ADK_WEB_README.md](ADK_WEB_README.md) covers running it in the ADK dev UI.

## Layout

```
ctf/agents/
├── model.py                 # LLM config: Ollama via LiteLLM (default) or Gemini, and thinking_planner()
├── tools.py                 # Function tools shared by the agents
├── eval/                    # ADK evalsets (see the ctf-eval skill)
└── sub_agents/              # The ADK app
    ├── agent.py             # CTFSubAgentsRoot coordinator, and the App
    ├── base_agent.py        # BaseCTFAgent: model, default tools, callback order
    ├── level_router.py      # Model-free routing: level changes, submits, hints, greetings
    ├── guard_rails.py       # Input and output guardrails
    ├── protection_utils.py  # Classifier-model guards and password-leak detection
    ├── system_prompt.py     # Shared system prompts
    └── level_0_agent.py … level_10_agent.py
```

Lower-level checks (input filters, output regexes, text normalization) and the Hugging Face classifiers live in
`ctf/llm_guard/`.

## Model

`model.py` uses Ollama through LiteLLM (`OPENSOURCE_LLM_MODEL`, default `qwen3:0.6b`, at `OLLAMA_API_BASE`). It
switches to Gemini when `USE_GEMINI=1` or `GEMINI_MODEL_NAME` is set. Agents get `thinking_planner()`, which asks
the model to return its reasoning with each response. qwen3 thinks by default, so its thought parts are dropped
unless the planner asks for them.

## How a turn flows

1. The player's message reaches the agent that holds the session: the coordinator in a new session, or the level
   agent the player was transferred to.
2. `before_model_callback`s run in order. Any of them can answer without calling the model:
   1. `level_greeting`: right after a transfer, greet the player with the level's title.
   2. `route_level_change`: "level N" moves the player to `LevelNAgent`.
   3. `route_submit_request`: "submit answer: X" calls `submit_answer_func` for this level.
   4. The level's own guards (below).
   5. `route_hint_request`: "hint" calls `hints_func` for this level.

   Level changes and submits come before the guards, so a guard can't trap a player in a level or block a correct
   password. Hints come after, so the guards still screen them.
3. The model answers or calls tools. `after_model_callback` and `after_tool_callback` guards can block a reply
   or tool result that leaks the password.

The coordinator has its own routing (`route_level_request` and `route_coordinator_submit`). It checks a submitted
answer against the level whose password it is.

Small models such as qwen3:0.6b often describe a tool call instead of making it, or pass the wrong level. That's
why level changes, submits, hints and greetings are handled without the model.

## Levels and protections

| Level | Agent | Protection |
|---|---|---|
| 0 | Basic prompt injection | None |
| 1 | Input protection | `guard_rail_input_injection` on input |
| 2 | Output protection | `guard_rail_output_injection` on model output and tool results |
| 3 | Prompt engineering | Hardened system prompt and a thinking prompt about injection |
| 4 | Multi-modal | Uploaded images, audio, PDFs and JSON go to the model |
| 5 | Function calling | `sql_query` tool with an injectable query on level 5's users table |
| 6 | Prompt-Guard | `llm_guard_prompt_injection_meta` (`protectai/deberta-v3-base-prompt-injection-v2`) |
| 7 | Prompt-Goose | `llm_guard_prompt_injection_goose` (`cgoosen/prompt-tackler_modernbert`) |
| 8 | Excessive agency | `execute_python_code`: the password is in the subprocess environment |
| 9 | Web page injection | `web_search` and `web_scrape`, so web pages are indirect input |
| 10 | Hold the Fort | Input guard, both classifiers, and password-leak detection on output |

## Tools (`tools.py`)

| Tool | What it does |
|---|---|
| `submit_answer_func` | Checks an answer against the level's password. On a match it records the solve on the leaderboard (`ctf/leaderboard.py`) and transfers the player to the next level |
| `hints_func` | Hints for a level |
| `password_search_func` (`rag_tool_func_tool`) | RAG over the LanceDB `ctf_levels` table, filtered by level |
| `get_leaderboard_stats` | Leaderboard summary |
| `help_search` | Web search for CTF, prompt injection, ADK and RAG help |
| `sql_query` | Level 5: looks a user up by ID in `users.db` |
| `execute_python_code` | Level 8: runs Python in a subprocess |
| `web_search`, `web_scrape` | Level 9: search the web (ddgs) and fetch a page as markdown |

`BaseCTFAgent` gives a level `submit_answer_func`, `hints_func`, `password_search_func`, `get_leaderboard_stats`
and `help_search` unless it passes its own `tools`.

## Running

```bash
uv sync
make prepare-flags                                              # seed LanceDB and users.db with the passwords
cd ctf/agents && uv run adk web --host 127.0.0.1 --port 8000    # or: uv run adk api_server
```

Needs Ollama with the model pulled (`ollama pull qwen3:0.6b`), or `USE_GEMINI=1`. The guard models download from
Hugging Face on first use, or at container start (`DOWNLOAD_MODELS`).

## Tests

```bash
uv run pytest ctf/tests -q                                       # unit tests, including the level router and guards
uv run pytest ctf/tests/test_vals.py -m adk_api -o addopts=""    # end-to-end, needs a running agent
```

To add a level, follow the `add-ctf-level` skill.
