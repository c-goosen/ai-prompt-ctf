# Docker Setup for AI Prompt CTF

## Files

- `web/Dockerfile` - The web app (Next.js 16.4 on vinext) as a standalone Node server (port 8100). Build context: `web/`.
- `Dockerfile.adk` - The Google ADK API server with the CTF agents (port 8000). Build context: repository root.
- `docker-compose.yml` - Runs Ollama, Postgres, the agent, the web app and (optionally) Traefik together.

## Quick Start

### Using Docker Compose (Recommended)

Compose uses **profiles**:

| Profile | Ollama | Use case |
|---------|--------|----------|
| `default` | In Docker (`ollama` + `ollama-init`) | Local / dev (recommended) |
| `prod` | Not started — set `OLLAMA_API_BASE` or `USE_GEMINI` | Remote Ollama or API LLM |

1. **Build and start services (default profile; Ollama pulls the model on first run):**
   ```bash
   docker compose --profile default up --build
   # or: make run
   # or: cp .env.example .env  then  docker compose up --build
   ```

   **Production (remote Ollama on host):**
   ```bash
   COMPOSE_PROFILES=prod \
     OLLAMA_API_BASE=http://host.docker.internal:11434 \
     docker compose up --build
   # or: make run-prod
   ```

2. **Access the services:**
   - Web app: http://localhost:8100 (health: `/health`)
   - ADK API: http://localhost:8000
   - Ollama and Postgres: internal only, on the Compose network

3. **Run in detached mode:** `docker compose up -d`
4. **View logs:** `docker compose logs -f web adk-api`
5. **Stop services:** `docker compose down` (add `-v` to drop the Postgres and Ollama volumes)

Start-up order: `postgres` (healthy) → `adk-api` (downloads guard models, then healthy) → `web`.

### Using Individual Images

#### Web app
```bash
docker build -t ai-prompt-ctf-web web
docker run -p 8100:8100 \
  -e ADK_API_URL=http://host.docker.internal:8000 \
  -e POSTGRES_DB_URI=postgresql://ctf:ctf@host.docker.internal:5432/ctf \
  -e COOKIE_SECURE=0 \
  ai-prompt-ctf-web
```

#### ADK API
```bash
docker build -f Dockerfile.adk -t ai-prompt-ctf-adk .
docker run -p 8000:8000 \
  -e POSTGRES_DB_URI=postgresql://ctf:ctf@host.docker.internal:5432/ctf \
  -e PREPARE_FLAGS=1 \
  -v ctf-lancedb:/app/ctf/lancedb \
  ai-prompt-ctf-adk
```

## Environment Variables

### Shared by `adk-api` and `web` (`x-shared-env` in docker-compose.yml)
- `POSTGRES_DB_URI` - Leaderboard database, built from `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` (default `ctf`).
  Both services must use the same database: the agent records completions, the web app shows them.
- `PASSWORD_ZERO` … `PASSWORD_TEN` - Level passwords. The web app needs them to redact RAG tool output.

### Web app
- `ADK_API_URL` - URL of the ADK API server (Compose: `http://adk-api:8000`)
- `ADK_RUN_TIMEOUT_MS` / `ADK_RUN_MAX_MS` - How long an agent run may stream nothing (default 180 s), and its total limit (default 600 s)
- `CTF_NAME`, `CTF_SUBTITLE`, `DISCORD_URL` - Branding and the sidebar Discord link
- `COOKIE_SECURE` - `1` behind HTTPS to mark identity cookies `Secure`; Compose defaults to `0` for plain http
- `HOST` / `PORT` - Bind address (`0.0.0.0` / `8100` in the image). vinext uses `HOST`, not `HOSTNAME`.

### ADK API
- `OLLAMA_API_BASE` - Ollama server URL for LiteLLM (`default` profile: `http://ollama:11434`; `prod`: your remote host)
- `OPENSOURCE_LLM_MODEL` - Ollama model tag or LiteLLM model id (default: `qwen3:0.6b`)
- `USE_GEMINI` - Set to `1` to use Gemini instead of Ollama (`prod` profile)
- `GEMINI_MODEL_NAME` - Gemini model when `USE_GEMINI=1`
- `OPENAI_API_KEY` - OpenAI API key (use with `OPENSOURCE_LLM_MODEL=openai/...` on `prod`)
- `PREPARE_FLAGS` - Seed the level passwords into LanceDB and level 5's users.db when the container starts. Read by `ctf/agent_startup.py`, which runs before `adk web`. Off when unset, but Compose sets it to `1`; set `0` to skip. Outside Docker, run `make prepare-flags`
- `DOWNLOAD_MODELS` - `0` to skip pre-downloading the Hugging Face guard models on start

### Ollama (`default` profile only)
- `OLLAMA_MODEL` - Model to pull on startup (default: `qwen3:0.6b`, matches `OPENSOURCE_LLM_MODEL`)

### Compose
- `COMPOSE_PROFILES` - `default` or `prod` (see `.env.example`)

## Volumes

- `lancedb_data` - LanceDB vector store with the level passwords (re-seeded on start)
- `hf_cache` - Hugging Face guard and embedding models, so they download once
- `postgres_data` - Leaderboard and player tokens
- `ollama_data` - Persisted Ollama models between restarts

## Requirements

- Docker 17.05 or higher (multi-stage builds)
- Docker Compose v2 (`docker compose`)

## Troubleshooting

### Web app can't connect to the ADK API
- Check `ADK_API_URL`; inside Compose use the service name: `http://adk-api:8000`
- For standalone containers, use `http://host.docker.internal:8000` to reach services on the host
- `curl localhost:8100/health` reports the ADK status and the error it saw

### Leaderboard doesn't show solved levels
- The agent and the web app must use the same `POSTGRES_DB_URI`

### Registration fails with "temporarily unavailable"
- The web app can't reach Postgres; check `docker compose logs postgres web`

### ADK API can't find agents
- Ensure the `ctf/agents` directory is copied into the image and `sub_agents/agent.py` exists

### LanceDB errors
- Ensure volumes are mounted, check file permissions, and seed flags with `PREPARE_FLAGS=1` (or `make prepare-flags` outside Docker)
- `No module named 'pandas'` from a password search means an old image: rebuild it (`docker compose up --build adk-api`)
