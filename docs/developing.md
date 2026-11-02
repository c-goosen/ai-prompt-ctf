# Developing

How to run the agent and web app without Docker, and how to debug a level. For Compose, see [DOCKER.md](../DOCKER.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) and Python 3.13 or 3.14
- Node 24 and [pnpm](https://pnpm.io)
- [Ollama](https://ollama.com) 0.40 or later, or a Gemini API key with `USE_GEMINI=1`

## Install

```bash
uv sync
make web-install   # = pnpm --dir web install --frozen-lockfile
ollama pull qwen3.5:2b
ollama pull d1-omni:600m   # levels 10, 11 and 15, even when the agents run on Gemini
```

## Run

```bash
make prepare-flags   # first run, or after changing a password
cd ctf/agents && uv run adk web --host 127.0.0.1 --port 8000
```

In a second terminal, from the repository root:

```bash
make web-dev   # http://localhost:3000
```

The dev server binds to `localhost` (IPv6 `::1`), so use `localhost` rather than `127.0.0.1`. The ADK API docs are at http://127.0.0.1:8000/docs.

## Level passwords

The defaults are `PASS_ZERO` to `PASS_FIFTEEN`, which is fine for local work. To change them, set `PASSWORD_ZERO`, `PASSWORD_ONE` and so on through `PASSWORD_FIFTEEN`, with the same values for **both** the agent and the web app. The agent checks them, and the web app redacts them from RAG tool output.

Every level needs its own password: one level's password must never solve another.

`make prepare-flags` seeds them into `ctf/lancedb` and `ctf/agents/users.db`, where `adk web` in `ctf/agents` reads them. In Docker, Compose sets `PREPARE_FLAGS=1`, so the agent re-seeds them on every start.

If seeding fails with `Permission denied`, check who owns `ctf/lancedb` (`ls -ld ctf/lancedb`). If it's owned by root, take ownership of it, or set `LANCE_DB_PATH` to another directory for both `make prepare-flags` and `adk web`.

## Databases

LanceDB holds the vector store for the RAG levels. All passwords go into the same table and are filtered by level.

The leaderboard and player tokens live in Postgres (`POSTGRES_DB_URI`), or SQLite at `ctf/leaderboard.db` when that isn't set. The agent and the web app must point at the same database.

## Debugging with the ADK dev UI

The web app shows players a tidy chat. When you're building or debugging a level, use ADK's dev UI instead: it shows which agent answered, every tool call with its arguments and response, and what was sent to the model.

Start the agent as above, then open http://127.0.0.1:8000/dev-ui/?app=sub_agents. You don't need the web app running. The Compose stack serves the same UI on port 8000, so stop it first if you want to run the agent locally.

> **Local development only.** The dev UI has no login and shows raw tool responses, including passwords. Don't expose it to players. See [Hosting an event](../DOCKER.md#hosting-an-event).

### Reading a chat

Type in the box at the bottom. Each event in the conversation is numbered, and its avatar colour changes with the agent that produced it. Here the coordinator hands over to `Level0Agent`, which then answers a hint request:

![A level 0 chat in the ADK dev UI, with tool calls between the messages](screenshots/adk-web-chat.png)

- A **lightning bolt** marks a tool call and a **tick** marks its response, so `hints_func` appears twice.
- **THOUGHT** blocks are the model's reasoning. They often explain a surprising turn: asked for the password in this session, the model decided it had "no need to use the password_search_func" and never called it.

### Seeing a tool call

Click an event to open it in the left panel, then choose a view from the icons down the side. **Raw JSON** (`{}`) shows everything. This is the tool call, with the arguments the model passed under `args`:

![The submit_answer_func call in the Raw JSON view, showing its answer and level arguments](screenshots/adk-web-tool-call.png)

The next event is what the tool returned, under `functionResponse`:

![The submit_answer_func response in the Raw JSON view, rejecting the answer](screenshots/adk-web-tool-response.png)

The other views:

| View | Use it to see |
|---|---|
| Info | The event's author, invocation and node path, such as `CTFSubAgentsRoot@1/Level0Agent@1` |
| Graph | The agents and tools, with the active agent highlighted |
| Request | On a model turn, what was sent to the model, including the level's full system prompt |
| Response | On a model turn, what the model returned |
| Usage Metadata | Token counts for a response and for the session |
| State Changes | What the event changed in session state. Levels 12 and 13 keep plugins and memories there |

### Debugging tips

- **Is it the wiring or the model?** `level N`, `hint` and `submit answer: <password>` are routed in `ctf/agents/sub_agents/level_router.py` without asking the model to choose a tool. If these fail, look at the agent's wiring. If they work but a normal question doesn't, look at the prompt or the model.
- **Did a guard block it?** A guard on the way in replies with its block message before the model runs, so you see that message with no tool call and no THOUGHT.
- **Web app different from the dev UI?** The web app redacts passwords from `password_search_func` output and strips leaderboard markers. The dev UI shows the raw event.
- **Testing a correct answer counts.** The dev UI chats as the user `user`, so a correct `submit answer:` records a solve for `user` in whichever leaderboard database the agent is using. Use a wrong answer to test the tool against a shared database.

## See also

- [Adding a level](adding-a-level.md)
- [Agents and how a turn flows](../ctf/agents/README.md)
- [How the web app and agents connect](../ADK_INTEGRATION.md)
- [Agent evals](../ctf/tests/eval/README.md)
- [Contributing](../CONTRIBUTING.md), including the checks CI runs
