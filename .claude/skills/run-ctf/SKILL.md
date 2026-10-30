---
name: run-ctf
description: Launch the PwnGPT CTF stack locally (Ollama, Python ADK agent, Postgres, Next.js/vinext web app), via Docker Compose or pnpm + uv. Use when asked to run, start, or try the app, or to check a change in the real UI.
---

# Run the CTF locally

| Service | URL |
|---|---|
| Web app (CTF UI, Next.js on vinext) | http://localhost:8100 in Docker, http://localhost:3000 with `pnpm dev` (`/health`) |
| ADK API / adk web (Python agent) | http://localhost:8000 (`/docs`) |
| Postgres (leaderboard, player tokens) | `postgres:5432` inside Compose only |

## Option A — Docker Compose (full stack, recommended)
```bash
make run          # = docker compose --profile default up --build adk-api web
```
- Ollama runs in a container; `ollama-init` pulls `qwen3:0.6b` on first start.
- The agent container downloads the Hugging Face guard models before serving
  (`ctf/agent_startup.py`, minutes on first run; `DOWNLOAD_MODELS=0` skips it).
  Set `PREPARE_FLAGS=1` once to seed the RAG flags. Watch `docker compose logs -f adk-api`.
- `web` waits for `adk-api` to be healthy, then serves on 8100.
- Cookies are only marked `Secure` when `COOKIE_SECURE` isn't `0`. Compose defaults
  it to `0` for plain-http localhost; set `COOKIE_SECURE=1` behind TLS.
- Host Ollama or Gemini instead: `make run-prod` with `OLLAMA_API_BASE=http://host.docker.internal:11434` or `USE_GEMINI=1`.
- Stop: `docker compose down` (add `-v` to wipe the Postgres volume).

## Option B — pnpm + uv, no Docker
Prerequisites: Node 24 + pnpm, `ollama serve` and `ollama pull qwen3:0.6b`; optional `PASSWORD_*` env vars (defaults are `PASS_ZERO`…), the same values for both processes.

1. Agent, run from the agents dir like `Dockerfile.adk` does:
   ```bash
   cd ctf/agents && uv run adk web --host 127.0.0.1 --port 8000
   ```
   RAG levels need flags in LanceDB: `uv run python -m ctf.agent_startup` with `PREPARE_FLAGS=1`.
2. Web app, in a second terminal:
   ```bash
   make web-install   # once
   make web-dev       # = pnpm --dir web dev  → http://localhost:3000
   ```
   It reaches the agent via `ADK_API_URL` (default `http://127.0.0.1:8000`). Without
   `POSTGRES_DB_URI` it uses SQLite at `ctf/leaderboard.db`, the same file the agent writes.
   The dev server binds to `localhost` (IPv6 `::1`), so use `localhost`, not `127.0.0.1`.

Run long-lived servers in the background, then confirm with `curl -s localhost:3000/health` (or `:8100`) and `curl -s localhost:8000/docs -o /dev/null -w '%{http_code}'`.
Stop background servers by the PID listening on the port (`ss -ltnp`), not `pkill -f <pattern>`, which also matches the shell running it.

## Cloudflare Workers preview (web app only)
`pnpm --dir web build:cf && pnpm --dir web preview:cf` runs the Worker in workerd on :8787.
Pass `--var POSTGRES_DB_URI:... --var ADK_API_URL:...` (see `web/cloudflare/wrangler.jsonc`).

More detail: `DOCKER.md`, `ADK_INTEGRATION.md`, `web/README.md`.
