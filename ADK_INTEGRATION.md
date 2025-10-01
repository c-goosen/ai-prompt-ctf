# ADK API Integration

This document describes the integration between the CTF frontend and the Google ADK API server.

## Overview

The frontend has been updated to use the ADK REST API instead of directly calling FastAPI code. Each level in the frontend now makes API calls to `http://127.0.0.1:8000` (the ADK server).

## Architecture

```
Frontend (Port 8100) -> ADK API Server (Port 8000) -> Level Agents
```

### Components

1. **Frontend Server** (`ctf/frontend/main.py`): FastAPI server serving the web interface
2. **ADK API Server**: Google ADK web server exposing REST API endpoints
3. **Level Agents** (`ctf/agents/sub_agents/`): Individual challenge agents for each level

## API Integration Details

### Request Flow

1. User submits form in frontend (HTMX POST to `/v1/chat/completions`)
2. Frontend processes form data and applies protection checks
3. Frontend ensures session exists:
   - Checks if session exists: `GET /apps/sub_agents/users/{user_id}/sessions/{session_id}`
   - Creates session if needed: `POST /apps/sub_agents/users/{user_id}/sessions/{session_id}`
4. Frontend calls ADK API at `http://127.0.0.1:8000/run` with:
   - `appName`: "sub_agents" (contains all level agents)
   - `userId`: From cookie identity
   - `sessionId`: `{user_id}-level-{level}`
   - `newMessage`: User's input text prefixed with level
5. ADK API routes to appropriate level agent
6. Agent processes request and returns response
7. Frontend extracts response text and returns HTML

### ADK API Payload Format

```json
{
  "appName": "sub_agents",
  "userId": "user_123",
  "sessionId": "user_123-level-0",
  "newMessage": {
    "parts": [{"text": "Level 0: What is the password?"}],
    "role": "user"
  },
  "streaming": false
}
```

### Response Processing

The ADK API returns an array of events. The frontend extracts text from:
```json
[
  {
    "content": {
      "parts": [{"text": "Response text here"}]
    }
  }
]
```

## Running the System

### 1. Install Dependencies

```bash
uv sync
```

### 2. Start ADK Server

```bash
cd ctf/agents
uv run adk web
```

This starts the ADK server on `http://127.0.0.1:8000`

### 3. Start Frontend Server

```bash
uv run ctf/frontend/main.py
```

This starts the frontend on `http://127.0.0.1:8100`

### 4. Test Integration

Test the ADK API directly:
```bash
# Test session creation
curl -X POST "http://localhost:8000/apps/sub_agents/users/test_user/sessions/test_session" \
  -H "Content-Type: application/json" -d "null"

# Test agent run
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"appName":"sub_agents","userId":"test_user","sessionId":"test_session","newMessage":{"parts":[{"text":"Level 0: Hello, what is the password?"}],"role":"user"},"streaming":false}'
```

Test the frontend integration by visiting `http://127.0.0.1:8100` and trying any level.

## Key Changes Made

### Frontend Routes (`ctf/frontend/routes/chat.py`)

- **Removed**: Direct agent instantiation and execution
- **Added**: `call_adk_api()` function to make HTTP requests to ADK server
- **Added**: `ensure_session_exists()` function for automatic session management
- **Updated**: `chat_completion()` endpoint to use ADK API with session management
- **Preserved**: File upload handling, protection checks, and HTML response formatting

### Frontend Routes (`ctf/frontend/routes/challenges.py`)

- **Added**: `get_session_history()` function to retrieve chat history from ADK API
- **Updated**: Session-aware history loading for each level
- **Improved**: Graceful fallback when session history is unavailable

### Dependencies (`pyproject.toml`)

- **Updated**: `httpx>=0.28.1` for HTTP client functionality

### Session Management

- **Automatic Creation**: Sessions are created automatically for each user and level
- **Session Format**: `{user_id}-level-{level}` (e.g., "user123-level-0")
- **User ID**: Uses cookie identity (`anon_user_identity`)
- **Persistent State**: Session state is managed by ADK server (no longer using local memory)
- **Per-Level Isolation**: Each level has its own session for proper isolation

## Agent Mapping

All levels are handled by the `sub_agents` app, which contains individual level agents:

| Level | Description |
|-------|-------------|
| 0 | Basic prompt injection |
| 1 | Input injection challenges |
| 2 | Output protection challenges |
| 3 | Advanced prompt engineering |
| 4 | Vision multi-modal injection |
| 5 | Audio multi-modal injection |
| 6 | Function calling injection |
| 7 | Prompt-Guard protection |
| 8 | Prompt-Goose protection |
| 9 | Chain of Thought challenges |
| 10 | Maximum security |

The level is specified in the message content (e.g., "Level 0: What is the password?") and the sub_agents app routes to the appropriate level agent.

## Error Handling

- **Connection Errors**: Graceful fallback with user-friendly error messages
- **API Errors**: Logged and handled with fallback responses
- **Protection Checks**: Still applied at frontend level before calling ADK API

## Future Enhancements

1. **Session History**: Implement ADK API calls to retrieve chat history
2. **Streaming**: Enable streaming responses using `/run_sse` endpoint
3. **Error Recovery**: Enhanced error handling and retry logic
4. **Monitoring**: Add observability for API calls and performance metrics

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure ADK server is running on port 8000
2. **Agent Not Found**: Verify agent names match exactly (case-sensitive)
3. **Timeout Errors**: Check if agents are taking too long to respond
4. **Session Issues**: Clear browser cookies if session state is corrupted

### Debug Commands

```bash
# Check ADK server status
curl http://127.0.0.1:8000/docs

# Test ADK API directly
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{"app_name":"Level0Agent","user_id":"test","session_id":"test-session","new_message":{"parts":[{"text":"Hello"}],"role":"user"},"streaming":false}'

# Check frontend server
curl http://127.0.0.1:8100/health
```
