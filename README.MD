# PwnGPT - Agent Hunger Games

<p align="center"><img src="web/public/images/pwn_gpt_logo.webp" alt="PwnGPT: a cartoon netrunner in a neon hoodie, with Table Mountain and Cape Town behind them" width="420"></p>

An open source prompt injection CTF. Players attack LLM agents across 16 levels to extract each level's password, learning about prompt injection, information retrieval and the security issues around LLMs along the way.

It runs on Google ADK agents with RAG, using qwen3 on Ollama by default, or Gemini or OpenAI. It was made for a company and the [BSides Cape Town](https://bsidescapetown.co.za) event ([background](https://twitter.com/crypticg00se/status/1731578440166293643)). This is v2, and it has been run at 3 events and counting.

Please use it and [add challenges](CONTRIBUTING.md).

![Quest map on the chat start screen](docs/screenshots/quest-map.png)

## Quick start

You need Docker Engine 25+ and Docker Compose v2.20+.

```bash
make run
```

Then open http://localhost:8100. The first start downloads the models, which can take several minutes. To follow it, run `docker compose logs -f adk-api`.

- **Run it without Docker:** see [Developing](docs/developing.md).
- **Run it for an event:** read [Hosting an event](DOCKER.md#hosting-an-event) first. The default setup isn't safe to expose to players.

## Features

- **16 levels, 0 to 15.** Each level has an agent guarding a password, with defences that get harder as you go: input and output guards, a hardened system prompt, multi-modal uploads (image, audio, PDF and JSON), SQL through function calling, Prompt-Guard models, code execution, web page injection, a small Ollama decision model judging every prompt, a decision model you hijack instead of an LLM, poisoned plugin descriptions, planted memories, code review injection, and finally every protection combined. Levels are tagged with OWASP Top 10 for LLM categories.
- **Quest map.** Levels are grouped into Warm-up, Easy, Medium, Hard and Insane zones that end at a boss. Your character stands at your next uncleared level. Click a node to jump to that level.
- **Siege on every solve.** A correct `/submit` sends a horde of gremlins to storm the level's tower. When it falls, the chat carries on at the next level.
- **XP and ranks.** Each cleared level gives XP based on its difficulty. Ranks go from *Script Kiddie* to *AGI Whisperer*.
- **Slash commands** with autocomplete:

  | Command | What it does |
  |---|---|
  | `/register <username> [session-id]` | Register (or switch user) from the chat |
  | `/level <0-15>` | Switch to a level. Typing "level N" in the chat also works |
  | `/start`, `/continue` | Go to level 0, or to your lowest unsolved level |
  | `/hint` | Ask the current level for a hint |
  | `/submit <answer>` | Submit a password |
  | `/whoami` | Show your username, session ID, rank, XP and next level |
  | `/challenges [level]` | List the levels or show one briefing |
  | `/leaderboard` | Show the top 10 players |
  | `/newsession` | Start a fresh conversation (your progress is kept) |
  | `/faq`, `/discord`, `/help` | Show the FAQ topics, the Discord link and the command list |
  | `/skills …` | Save your own reusable prompts and run them as `/<name>` |

- **Live leaderboard** with stat cards and a recent-completions feed. It refreshes every 30 seconds. Only the agent's `submit_answer_func` can record a solve.

  ![Live leaderboard with stat cards, player rankings and recent completions](docs/screenshots/leaderboard.png)

- **Bookmarkable sessions** at `/ctf/<username>/<session-id>`. At events, the session ID can be your Quicket code.
- **No accounts.** A username is claimed on first registration, which gives your browser an httpOnly ownership token. Chat history and leaderboard progress are tied to it.

## Screenshots

| | |
|---|---|
| ![Start screen before registering](docs/screenshots/home.png) | ![Slash command autocomplete](docs/screenshots/slash-commands.png) |
| Start screen before registering | Slash command autocomplete |
| ![A guardrail blocking a prompt injection](docs/screenshots/chat-level.png) | ![Level briefing from /challenges](docs/screenshots/chat-commands.png) |
| A guardrail blocking a direct ask on level 1 | `/challenges 1` briefing in the chat |
| ![Challenges page](docs/screenshots/challenges.png) | ![Gremlins topple the level 0 tower](docs/screenshots/siege.png) |
| Challenges with difficulty and OWASP tags | The siege after `/submit PASS_ZERO` |

## Architecture

```
Browser <-> Web app (Next.js 16.4 on vinext, web/) <-> Google ADK API (Python, ctf/agents) <-> LLM
                       \                                  /
                        +------ Postgres (leaderboard) ---+
```

- **Web app** (`web/`): Next.js 16.4 App Router, built and served with [vinext](https://github.com/cloudflare/vinext) (Vite), styled with Tailwind CSS v4, shadcn/ui and [Watermelon UI](https://ui.watermelon.sh) animations. It renders the UI and owns everything except the agent: registration and username ownership, the chat proxy to ADK, chat history, the leaderboard, FAQ and challenges, rate limiting and the health check. It runs as a standalone Node server (Docker) or on [Cloudflare Workers](web/README.md#cloudflare-workers).
- **Google ADK API** (`ctf/agents`): the multi-agent CTF (coordinator + one agent per level), guardrails and tools. It records level completions when `submit_answer_func` accepts a password.
- **Postgres**: the shared leaderboard and player-ownership tables. Without `POSTGRES_DB_URI`, both sides fall back to the SQLite file `ctf/leaderboard.db`.
- **LanceDB**: the vector store for the RAG levels.

### Agent design

The CTF uses a coordinator pattern, where a root agent delegates to level-specific agents:

![Agent Design Map](agent-design-map.png)

*The agent structure graph from the ADK dev UI (`uv run adk web`, app `sub_agents`): solid arrows are sub-agents, dashed arrows are tools.*

- **CTFSubAgentsRoot**: main coordinator agent that routes users to appropriate level agents
- **Level0Agent through Level15Agent**: individual challenge agents with progressive security measures
- **Function tools**: functions like `submit_answer_func`, `password_search_func`, `hints_func`, `sql_query`, `execute_python_code`, `web_search` and `web_scrape` that agents can call
- **Level routing**: "level N" from any agent hands the player to that level before the guards run, and each level greets the player on arrival

## Docs

| To | Read |
|---|---|
| Play: levels and help | [Challenges](web/content/challenges.md), [FAQ](web/content/faq.md) |
| Run or host it with Docker | [DOCKER.md](DOCKER.md) |
| Run it locally and debug a level | [Developing](docs/developing.md) |
| Add a level | [Adding a level](docs/adding-a-level.md) |
| Contribute | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Understand the agents and protections | [ctf/agents/README.md](ctf/agents/README.md) |
| Understand how the web app talks to the agents | [ADK_INTEGRATION.md](ADK_INTEGRATION.md) |
| Work on the web app, or deploy it to Workers | [web/README.md](web/README.md) |
| Write agent evals | [ctf/tests/eval/README.md](ctf/tests/eval/README.md) |
| See what changed, and what's planned | [CHANGELOG.md](CHANGELOG.md), [TODO.md](TODO.md) |

## Resources and cost

The Hugging Face guard models take about 1.6 GB of disk, and the Ollama models need their own disk and memory on top. Everything can run locally, so the cost depends on your hosting and on whether you use a paid LLM API. [This thread](https://twitter.com/crypticg00se/status/1731578440166293643) covers an earlier event. Up-to-date memory figures haven't been measured for this version.

## Who made this

Hacker, DevSecOps, builder, AI/ML prompt injector and curious person. I give myself ridiculous challenges like building this. [WHOAMI](https://github.com/c-goosen)

## License

[MIT](LICENSE)
