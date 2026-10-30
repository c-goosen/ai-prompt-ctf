# ADK API Integration

How the web app (`web/`, Next.js 16.4 on vinext) talks to the Google ADK API server that runs the CTF agents.

## Architecture

```
Browser -> Web app (8100 in Docker, 3000 in dev) -> ADK API Server (8000) -> sub_agents (coordinator + level agents)
                  \-> Postgres (leaderboard, player tokens) <-/
```

1. **Web app** (`web/`): UI, registration and username ownership, the chat proxy, history, leaderboard, rate limits.
2. **ADK API server**: `adk web` / `adk api_server` serving the `sub_agents` app from `ctf/agents`.
3. **Agents** (`ctf/agents/sub_agents/`): `CTFSubAgentsRoot` routes to `Level0Agent` … `Level10Agent`, which apply
   the guardrails and call the tools (`ctf/agents/tools.py`). See [ctf/agents/README.md](ctf/agents/README.md).

## Request flow

1. The chat UI posts `multipart/form-data` (`text_input`, optional `file_input`, optional `session_id`) to
   `/v1/chat/completions`.
2. **Slash commands** (`web/lib/slash.ts`, `web/lib/commands.ts`) are handled first:
   - `/register` registers or switches the player from the chat, under the register page's rate limit.
   - `/challenges`, `/faq` and `/discord` work for anyone.
   - The rest need a registered player. `/help`, `/whoami`, `/leaderboard`, `/newsession` and `/skills` are
     answered by the web app. `/level`, `/start`, `/continue`, `/hint`, `/submit` and skills become a prompt for the
     agent. For example, `/submit X` sends `submit answer: X`.
3. Everything else needs the identity cookies. `anon_user_identity` and `session_id` must be well formed, and the
   httpOnly `player_token` must match the stored hash for that username. Otherwise the route returns 401 and never
   calls ADK. A `session_id` field from `/ctf/<session>` overrides the cookie's session, and ADK keeps sessions per
   user, so it only reaches the player's own sessions.
4. `web/lib/adk.ts` makes sure the session exists:
   - `GET /apps/sub_agents/users/{user_id}/sessions/{session_id}`
   - `POST` the same URL with `{}` if it returned 404
5. `web/lib/runs.ts` starts the run detached from the request and records it in the `agent_runs` table. The run
   finishes even if the player closes the tab. A page opened mid-run polls `GET /api/chat/status` until the run
   ends, then loads `GET /api/chat/history`.
6. The run calls `POST /run_sse` with `streaming: true` (payload below). Uploads (PDF, JSON, images, audio; up to
   10 MB) are sent as a base64 `inline_data` part. `/run` sends nothing until the agent finishes, and Node's fetch
   gives up after 5 minutes without response headers, which is why the run streams.
7. `web/lib/events.ts` turns the final events into messages (text, thoughts, function calls, tool responses). It
   redacts level passwords from `password_search_func` output, strips leaderboard markers, and notes any level that
   `submit_answer_func` accepted.
8. The route responds with:

   | Field | |
   |---|---|
   | `messages` | `[{ "role": "assistant" \| "tool", "text": "...", "thoughts"?: "..." }]`, rendered as markdown (no raw HTML) |
   | `progress` | The player's levels on the leaderboard, for the quest map |
   | `solved` | Levels whose password `submit_answer_func` accepted in this run, for the siege animation. Taken only from the tool's response, never from model text |
   | `sessionId`, `newSession` | Set by `/newsession` and `/register`, which move the player to another session |

One ADK session per player session: the agents move the player between levels within it, so there is no level
prefix in messages.

### Routing without the model

Small models such as qwen3:0.6b don't reliably call tools. Before any model call,
`ctf/agents/sub_agents/level_router.py` answers these messages itself:

| Message | Coordinator | Level agent |
|---|---|---|
| "level N", "I want to try level N" | `transfer_to_agent` to `LevelNAgent` | The same, or a greeting if it's already level N |
| "submit answer: X" | `submit_answer_func` for the level whose password is X (level 0 if none) | `submit_answer_func` for its own level |
| "hint" / "give me a hint …" | (model) | `hints_func` for its level |

A level agent greets the player with no model call right after a transfer. Level changes and submits run before the
level's guards, so a guard can't block leaving a level or submitting a password. Hint routing runs after the
guards. On a correct answer, `submit_answer_func` records the solve and transfers the player to the next level,
whose greeting closes the reply.

### `/run_sse` payload

```json
{
  "appName": "sub_agents",
  "userId": "alice",
  "sessionId": "0f8fad5b-d9cb-469f-a165-70867728950e",
  "newMessage": { "role": "user", "parts": [{ "text": "I want to try level 0" }] },
  "streaming": true
}
```

### Response

Server-sent events, each an ADK event. Partial (`"partial": true`) chunks only reset the idle timeout; the final
events carry `content.parts[]` with `text` (or `thought: true` reasoning), `functionCall` and `functionResponse`:

```json
{ "author": "Level0Agent", "content": { "role": "model", "parts": [{ "text": "Response text here" }] } }
```

Chat history comes from the session's `events` (`GET /apps/sub_agents/users/{user_id}/sessions/{session_id}`),
parsed the same way.

## Leaderboard

Completions are recorded by the agent: `submit_answer_func` writes to `leaderboard_entries` (`ctf/leaderboard.py`)
using the ADK session's user id. The web app only reads the leaderboard and adds a level 0 entry at registration.
Credit is never derived from model text, which players can steer with prompt injection.

## Running the System

```bash
uv sync
cd ctf/agents && uv run adk web --host 127.0.0.1 --port 8000   # agent
make web-dev                                                   # web app, http://localhost:3000
```

Test the ADK API directly (`/run` returns every event at once, which is easier to read when debugging):
```bash
curl -X POST "http://localhost:8000/apps/sub_agents/users/test_user/sessions/test_session" \
  -H "Content-Type: application/json" -d "{}"

curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"appName":"sub_agents","userId":"test_user","sessionId":"test_session","newMessage":{"parts":[{"text":"I want to try level 0"}],"role":"user"},"streaming":false}'
```

End-to-end agent tests (need a running agent): `uv run pytest ctf/tests/test_vals.py -m adk_api -o addopts=""`.

## Error handling

- ADK unreachable: chat replies with an apology message; `/health` reports `degraded` with the error.
- Registration when ADK is down: 502, and the just-claimed username is released.
- Database unreachable: registration returns 503, ownership checks fail closed, and the leaderboard shows an
  "unavailable" notice.

## Troubleshooting

1. **Connection refused**: ensure the ADK server is running on port 8000 and `ADK_API_URL` points at it.
2. **"No user session found" in chat**: register first; the `player_token` cookie proves the username is yours.
3. **Timeouts**: a run may go `ADK_RUN_TIMEOUT_MS` (default 180 s) without streaming anything, and
   `ADK_RUN_MAX_MS` (default 600 s) in total. Small local models can be slow on the first call.

```bash
curl http://127.0.0.1:8000/docs      # ADK server
curl http://localhost:3000/health    # web app (8100 in Docker)
```
