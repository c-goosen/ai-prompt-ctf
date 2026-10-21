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
   the guardrails and call the tools (`ctf/agents/tools.py`).

## Request flow

1. The chat UI posts `multipart/form-data` (`text_input`, optional `file_input`) to `/v1/chat/completions`.
2. The route checks the identity cookies: `anon_user_identity` and `session_id` must be well formed, and the
   httpOnly `player_token` must match the stored hash for that username. Otherwise it returns 401 and never
   calls ADK.
3. `web/lib/adk.ts` makes sure the session exists:
   - `GET /apps/sub_agents/users/{user_id}/sessions/{session_id}`
   - `POST` the same URL with `{}` if it returned 404
4. It calls `POST /run` (payload below). Uploads (PDF, JSON, images, audio; up to 10 MB) are sent as a base64
   `inline_data` part.
5. `web/lib/events.ts` turns the returned events into messages (text, function calls, tool responses),
   redacts level passwords from `password_search_func` output, and strips leaderboard markers.
6. The route responds `{ "messages": [{ "role": "assistant" | "tool", "text": "..." }] }`, which the client
   renders as markdown (raw HTML is not rendered).

One ADK session per player session: the coordinator moves the player between levels within it ("I want to try
level 3"), so there is no level prefix in messages.

### `/run` payload

```json
{
  "appName": "sub_agents",
  "userId": "alice",
  "sessionId": "0f8fad5b-d9cb-469f-a165-70867728950e",
  "newMessage": { "role": "user", "parts": [{ "text": "I want to try level 0" }] },
  "streaming": false
}
```

### Response

An array of events; text is taken from `content.parts[].text`, plus `functionCall` and `functionResponse` parts:

```json
[{ "author": "Level0Agent", "content": { "role": "model", "parts": [{ "text": "Response text here" }] } }]
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

Test the ADK API directly:
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
3. **Timeouts**: `/run` allows 60 s; small local models can be slow on the first call.

```bash
curl http://127.0.0.1:8000/docs      # ADK server
curl http://localhost:3000/health    # web app (8100 in Docker)
```
