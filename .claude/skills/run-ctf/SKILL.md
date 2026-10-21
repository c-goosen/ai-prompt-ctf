---
name: run-ctf
description: Launch the PwnGPT CTF stack locally (Ollama, ADK API, FastAPI/HTMX frontend), via Docker Compose or uv. Use when asked to run, start, or try the app, or to check a change in the real UI.
---

# Run the CTF locally

| Service | URL |
|---|---|
| Frontend (CTF UI) | http://localhost:8100 (`/health`) |
| ADK API / adk web | http://localhost:8000 (`/docs`) |

## Option A — Docker Compose (full stack, recommended)
```bash
make run          # = docker compose --profile default up --build adk-api frontend
```
- Ollama runs in a container; `ollama-init` pulls `qwen3:0.6b` on first start.
- The frontend downloads Hugging Face guard models at startup, which takes minutes. Wait for `Uvicorn running on http://0.0.0.0:8100` in `docker compose logs -f frontend`.
- Host Ollama or Gemini instead: `make run-prod` with `OLLAMA_API_BASE=http://host.docker.internal:11434` or `USE_GEMINI=1`.
- Stop: `docker compose down`.

## Option B — uv, no Docker
Prerequisites: `ollama serve` and `ollama pull qwen3:0.6b`; optional `PASSWORD_*` env vars (defaults are `PASS_ZERO`…).

1. ADK API, run from the agents dir like `Dockerfile.adk` does:
   ```bash
   cd ctf/agents && uv run adk web --host 127.0.0.1 --port 8000
   ```
2. Frontend, in a second terminal from the repo root:
   ```bash
   uv run python ctf/frontend/main.py   # port 8100, reload unless FASTAPI_ENV=production
   ```
   It reaches the agents via `ADK_API_URL` (default `http://127.0.0.1:8000`).
3. RAG levels need flags in LanceDB: `uv run python ctf/prepare_flags.py`.

Run long-lived servers in the background, then confirm with `curl -s localhost:8100/health` and `curl -s localhost:8000/docs -o /dev/null -w '%{http_code}'`.

More detail: `DOCKER.md`, `ADK_INTEGRATION.md`.
