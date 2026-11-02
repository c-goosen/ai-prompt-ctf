# Docker Setup for AI Prompt CTF

## Files

- `web/Dockerfile` - The web app (Next.js 16.4 on vinext) as a standalone Node server (port 8100). Build context: `web/`.
- `Dockerfile.adk` - The Google ADK API server with the CTF agents (port 8000). Build context: repository root.
- `docker-compose.yml` - Runs Ollama, Postgres, the agent, the web app and (optionally) Traefik together.

## Requirements

- Docker Engine 25 or later, which the agent's health check needs for `start_interval`
- Docker Compose v2.20 or later (`docker compose`), which the optional `ollama-init` dependency needs

## Quick Start

Compose uses **profiles**:

| Profile | Ollama | Use case |
|---------|--------|----------|
| `default` | In Docker (`ollama` + `ollama-init`) | Local / dev (recommended) |
| `prod` | Not started — set `OLLAMA_API_BASE` or `USE_GEMINI` | Remote Ollama or API LLM |

### Default profile

From the repository root:

```bash
make run
# = docker compose --profile default up --build adk-api web
```

To run `docker compose up` without `--profile`, copy `.env.example` to `.env`, which sets `COMPOSE_PROFILES=default`.

On first start, `ollama-init` pulls the default model (`qwen3.5:2b`) and the decision model, and the agent container downloads the Hugging Face guard models before serving (`ctf/agent_startup.py`). This can take several minutes.

Start-up order: `postgres` (healthy) → `adk-api` (downloads guard models, then healthy) → `web`.

### Production profile

Use the `prod` profile when Ollama runs outside Compose, or when using Gemini or OpenAI. Read [Hosting an event](#hosting-an-event) before exposing it to players.

```bash
make run-prod
```

Remote Ollama, for example a machine with a GPU. This doesn't start the local Ollama container, and it stops with an error if `OLLAMA_API_BASE` isn't set in `.env` or the command. Nothing pulls models for you, so pull the chat and decision models on that machine first:

```bash
make run-remote OLLAMA_API_BASE=http://<host>:11434
```

Ollama on the host (the models must already be pulled there):

```bash
COMPOSE_PROFILES=prod \
  OLLAMA_API_BASE=http://host.docker.internal:11434 \
  OPENSOURCE_LLM_MODEL=qwen3.5:2b \
  docker compose up --build
```

Gemini:

```bash
COMPOSE_PROFILES=prod USE_GEMINI=1 docker compose up --build
```

### Access from the host

| Service | URL |
|---------|-----|
| Web app (CTF UI) | http://localhost:8100 |
| Web app health | http://localhost:8100/health |
| ADK API and dev UI | http://localhost:8000 |
| ADK API docs | http://localhost:8000/docs |

Use `localhost` or `127.0.0.1` in the browser. Ollama and Postgres are not published to the host; containers reach them on the Compose network.

### Common commands

```bash
# Detached mode
docker compose --profile default up --build -d

# Follow logs
docker compose logs -f web adk-api

# Stop and remove containers
docker compose down

# Also delete the Postgres, Ollama, Hugging Face and LanceDB volumes
docker compose --profile default down -v
```

### Optional: Traefik reverse proxy

To serve the web app on port 80 instead of 8100:

```bash
docker compose up -d traefik
```

Then open http://localhost (Traefik routes `Host: localhost` and `Host: 127.0.0.1` to the web app). This configuration is for local use: see [Hosting an event](#hosting-an-event).

## Hosting an event

The Compose defaults are set up for a trusted machine. Players attack this system on purpose, so check these before exposing it:

- **Close port 8000.** The agent container runs `adk web --host 0.0.0.0`, and Compose publishes it as `8000:8000` in both profiles. Anyone who reaches that port gets the dev UI and API with no login, can read raw tool responses including passwords, and can skip the web app's guards on ownership and rate limits. The web app reaches the agent over the Compose network, so change the mapping to `"127.0.0.1:8000:8000"`. Don't rely on a host firewall such as `ufw` alone, because Docker's published ports can bypass it.
- **Set your own secrets.** Set every `PASSWORD_*` and `POSTGRES_PASSWORD`. The defaults are public in this repository, and `.env` must stay out of git.
- **Contain the agent host.** The vulnerabilities are intentional: level 5 has injectable SQL, level 8 runs player-influenced Python in a subprocess, and level 9 fetches arbitrary web pages. Run the stack on a dedicated machine with no credentials you care about, and restrict its outbound access to what the levels need. Don't add other secrets to the agent's environment.
- **Terminate TLS and set `COOKIE_SECURE=1`.** Compose defaults it to `0` for plain http.
- **Don't publish the Traefik setup as it is.** It enables the unauthenticated dashboard on port 8080 (`--api.insecure=true`), mounts the Docker socket, and only routes `localhost`. It has no TLS entrypoint, although it publishes port 443.
- **Check rate limits.** Per-IP limits are in `web/lib/rate-limit.ts`. Behind a proxy, confirm players aren't all seen as one IP.

## Using Individual Images

### Web app
```bash
docker build -t ai-prompt-ctf-web web
docker run -p 8100:8100 \
  -e ADK_API_URL=http://host.docker.internal:8000 \
  -e POSTGRES_DB_URI=postgresql://ctf:ctf@host.docker.internal:5432/ctf \
  -e COOKIE_SECURE=0 \
  ai-prompt-ctf-web
```

### ADK API
```bash
docker build -f Dockerfile.adk -t ai-prompt-ctf-adk .
docker run -p 8000:8000 \
  -e POSTGRES_DB_URI=postgresql://ctf:ctf@host.docker.internal:5432/ctf \
  -e PREPARE_FLAGS=1 \
  -v ctf-lancedb:/app/ctf/lancedb \
  ai-prompt-ctf-adk
```

## Environment Variables

Set these in your shell or `.env`. Defaults are the ones Compose applies.

### Shared by `adk-api` and `web` (`x-shared-env` in docker-compose.yml)
- `POSTGRES_DB_URI` - Leaderboard database, built from `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` (default `ctf`). Both services must use the same database: the agent records completions, the web app shows them.
- `PASSWORD_ZERO` … `PASSWORD_FIFTEEN` - Level passwords (default `PASS_ZERO` …). The web app needs them to redact RAG tool output.

### Web app
- `ADK_API_URL` - URL of the ADK API server (Compose: `http://adk-api:8000`)
- `ADK_RUN_TIMEOUT_MS` / `ADK_RUN_MAX_MS` - How long an agent run may stream nothing (default 180 s), and its total limit (default 600 s)
- `CTF_NAME`, `CTF_SUBTITLE`, `DISCORD_URL` - Branding and the sidebar Discord link
- `COOKIE_SECURE` - `1` behind HTTPS to mark identity cookies `Secure`; Compose defaults to `0` for plain http
- `SITE_URL` - the public URL of the site, so link previews can find their image
- `HOST` / `PORT` - Bind address (`0.0.0.0` / `8100` in the image). vinext uses `HOST`, not `HOSTNAME`.

### ADK API
- `OLLAMA_API_BASE` - Ollama server URL for LiteLLM (`default` profile: `http://ollama:11434`; `prod`: your remote host)
- `OPENSOURCE_LLM_MODEL` - Ollama model tag or LiteLLM model id (default: `qwen3.5:2b`)
- `USE_GEMINI` - Set to `1` to use Gemini instead of Ollama (`prod` profile)
- `GEMINI_MODEL_NAME` - Gemini model when `USE_GEMINI=1`
- `OPENAI_API_KEY` - OpenAI API key (use with `OPENSOURCE_LLM_MODEL=openai/...` on `prod`)
- `PREPARE_FLAGS` - Seed the level passwords into LanceDB and level 5's users.db when the container starts. Read by `ctf/agent_startup.py`, which runs before `adk web`. Off when unset, but Compose sets it to `1`; set `0` to skip. Outside Docker, run `make prepare-flags`
- `DECISION_MODEL` - The decision model for levels 10, 11 and 15, an [Ollama decision model](https://ollama.com/search?c=decision) called through `/v1/systemone` (default `d1-omni:600m`; needs Ollama 0.40+). `ollama-init` pulls it too
- `DECISION_THRESHOLD` - Attack probability at which levels 10 and 15 block a prompt (default `0.5`)
- `DOWNLOAD_MODELS` - `0` to skip pre-downloading the Hugging Face guard models on start
- `LANCE_DB_PATH` - LanceDB directory for the RAG tool (default: `ctf/lancedb`). Compose doesn't set it, so it uses the `lancedb_data` volume mounted at that path

### Ollama (`default` profile only)
- `OLLAMA_MODEL` - Model to pull on startup (default: `qwen3.5:2b`). Keep it the same as `OPENSOURCE_LLM_MODEL`
- `DECISION_MODEL` - Pulled on startup as well, for levels 10, 11 and 15 (default: `d1-omni:600m`)

For example, to use a different Ollama model:

```bash
OLLAMA_MODEL=qwen3:1.7b OPENSOURCE_LLM_MODEL=qwen3:1.7b docker compose up --build
```

### Compose
- `COMPOSE_PROFILES` - `default` or `prod` (see `.env.example`)

## Volumes

- `lancedb_data` - LanceDB vector store with the level passwords (re-seeded on start)
- `hf_cache` - Hugging Face guard and embedding models (about 1.6 GB), so they download once
- `postgres_data` - Leaderboard and player tokens
- `ollama_data` - Persisted Ollama models between restarts

## Troubleshooting

### Web app never starts
- It waits for the ADK API health check, and the agent downloads guard models first. Check `docker compose logs -f adk-api`

### ADK API is unhealthy
- Ensure Ollama finished pulling the models: `docker compose logs ollama-init`

### Web app can't connect to the ADK API
- Check `ADK_API_URL`; inside Compose use the service name: `http://adk-api:8000`
- For standalone containers, use `http://host.docker.internal:8000` to reach services on the host
- `curl localhost:8100/health` reports the ADK status and the error it saw

### Leaderboard doesn't show solved levels
- The agent and the web app must use the same `POSTGRES_DB_URI`

### Registration fails with "temporarily unavailable"
- The web app can't reach Postgres; check `docker compose logs postgres web`

### HTTP 429
- Per-IP rate limits (see `web/lib/rate-limit.ts`) keep LLM costs down

### ADK API can't find agents
- Ensure the `ctf/agents` directory is copied into the image and `sub_agents/agent.py` exists

### LanceDB errors
- Ensure volumes are mounted, check file permissions, and seed flags with `PREPARE_FLAGS=1` (or `make prepare-flags` outside Docker)
- `No module named 'pandas'` from a password search means an old image: rebuild it (`docker compose up --build adk-api`)
