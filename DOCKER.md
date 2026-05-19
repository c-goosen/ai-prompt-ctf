# Docker Setup for AI Prompt CTF

This directory contains Dockerfiles for running the AI Prompt CTF application in containers.

## Files

- `Dockerfile.frontend` - Dockerfile for the FastAPI frontend server (port 8100)
- `Dockerfile.adk` - Dockerfile for the Google ADK API server (port 8000)
- `docker-compose.yml` - Docker Compose configuration to run both services together

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
   - Frontend: http://localhost:8100
   - ADK API: http://localhost:8000
   - Ollama: internal only (`http://ollama:11434` on the Compose network; not published to the host)

3. **Run in detached mode:**
   ```bash
   docker-compose up -d
   ```

4. **View logs:**
   ```bash
   docker-compose logs -f
   ```

5. **Stop services:**
   ```bash
   docker-compose down
   ```

### Using Individual Dockerfiles

#### Build Frontend Image
```bash
docker build -f Dockerfile.frontend -t ai-prompt-ctf-frontend .
```

#### Run Frontend Container
```bash
docker run -p 8100:8100 \
  -e ADK_API_URL=http://host.docker.internal:8000 \
  ai-prompt-ctf-frontend
```

#### Build ADK API Image
```bash
docker build -f Dockerfile.adk -t ai-prompt-ctf-adk .
```

#### Run ADK API Container
```bash
docker run -p 8000:8000 \
  -v $(pwd)/ctf/lancedb:/app/ctf/lancedb \
  -v $(pwd)/ctf/agents/lancedb:/app/ctf/agents/lancedb \
  ai-prompt-ctf-adk
```

## Environment Variables

### Frontend
- `ADK_API_URL` - URL of the ADK API server (default: `http://127.0.0.1:8000`)
- `OPENAI_API_KEY` - OpenAI API key (if using OpenAI models)
- `FASTAPI_ENV` - FastAPI environment (default: `production`)

### ADK API
- `OLLAMA_API_BASE` - Ollama server URL for LiteLLM (`default` profile: `http://ollama:11434`; `prod`: set to your remote host)
- `OPENSOURCE_LLM_MODEL` - Ollama model tag or LiteLLM model id (default: `qwen3:0.6b`)
- `USE_GEMINI` - Set to `1` to use Gemini instead of Ollama (`prod` profile)
- `GEMINI_MODEL_NAME` - Gemini model when `USE_GEMINI=1`
- `OPENAI_API_KEY` - OpenAI API key (use with `OPENSOURCE_LLM_MODEL=openai/...` on `prod`)

### Ollama (`default` profile only)
- `OLLAMA_MODEL` - Model to pull on startup (default: `qwen3:0.6b`, matches `OPENSOURCE_LLM_MODEL`)

### Compose
- `COMPOSE_PROFILES` - `default` or `prod` (see `.env.example`)

## Volumes

The docker-compose.yml mounts the following volumes:
- `./ctf/lancedb` - LanceDB database for vector storage
- `./ctf/agents/lancedb` - LanceDB database for agents
- `./ctf/frontend/static` - Static files (CSS, images, etc.)
- `./ctf/frontend/templates` - HTML templates
- `ollama_data` - Persisted Ollama models between restarts

## Requirements

- Docker 17.05 or higher (for multi-stage builds)
- Docker Compose (for docker-compose.yml)

## Notes

- The frontend connects to the ADK API using the `ADK_API_URL` environment variable
- In Docker Compose, services communicate using service names (e.g., `http://adk-api:8000`)
- For local development, you may need to set `ADK_API_URL=http://host.docker.internal:8000` if running frontend in Docker but ADK API locally
- With the `default` profile, Ollama runs in Docker; with `prod`, point `OLLAMA_API_BASE` at a reachable Ollama host or set `USE_GEMINI=1`

## Troubleshooting

### Frontend can't connect to ADK API
- Check that `ADK_API_URL` is set correctly
- In Docker Compose, use the service name: `http://adk-api:8000`
- For standalone containers, use `http://host.docker.internal:8000` to access host services

### ADK API can't find agents
- Ensure the `ctf/agents` directory is properly copied into the container
- Check that `sub_agents/agent.py` exists in `ctf/agents/`
- Verify that `sub_agents/` directory exists with level agents

### LanceDB errors
- Ensure volumes are properly mounted
- Check file permissions on mounted directories

