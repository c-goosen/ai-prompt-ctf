# Changelog

All notable changes to PwnGPT. Dates are when the work landed on the `nextjs-migration` branch.

## [Unreleased]

### Added
- **Four agentic levels and a decision-model level.** Hold the Fort moves from level 10 to **level 15** and stays
  the boss (1,500 XP). Existing level 10 completions move to level 15 automatically, once, when the agent
  starts (recorded in `leaderboard_migrations`). Move the old `PASSWORD_TEN` to `PASSWORD_FIFTEEN` and set new
  ones for 10-14; the agent warns at start-up if two levels share a password.
  - **Level 10: Decision Model Protection.** Before the agent sees a prompt, a small Ollama decision model
    (`d1-omni:600m`, the smallest in [Ollama's decision category](https://ollama.com/search?c=decision) up to
    8 GB) scores the chance that it's after the password or overriding the agent. It's called through
    `/v1/systemone` (Ollama 0.40+) and blocks at `DECISION_THRESHOLD` (default 0.5). The block message shows the
    score, and the guard fails closed if the model is unavailable. `DECISION_MODEL` can be any decision model,
    such as `laya`. Compose's `ollama-init` pulls it.
  - **Level 11: Triage Hijack.** No LLM: the decision model chooses a helpdesk's next action from a ticket the
    player writes, and `open_vault` sends the code. Every attempt shows each action's probability. Based on
    [Decision Hijacking](https://arxiv.org/abs/2609.28613) (arXiv 2609.28613).
  - **Level 12: Poisoned Plugin.** Plugin descriptions skip the chat guard and become trusted instructions;
    whatever the assistant passes to `call_plugin` is echoed back from the plugin's "server".
  - **Level 13: False Memories.** Chat about the vault is blocked, but `remember: <fact>` writes unscreened
    memories that are loaded back as trusted facts.
  - **Level 14: Trojan Review.** A code reviewer with the repo's deploy key follows instructions hidden in the
    code's comments. Messages without code are refused and the note outside the code block is screened; the
    code itself is not.
  - Hold the Fort (15) also runs the decision-model guard. The quest map has 16 towers, the XP spread is
    re-balanced, and the top rank now needs 6,400 XP.
- **Quest map.** The chat start screen has a "Your run" map with every level split into
  Warm-up, Easy, Medium, Hard and Insane zones, ending at a boss level. Your character walks to the lowest level you
  haven't cleared yet. Click any node to jump to that level. Visitors who haven't registered see the map without
  progress.
- **XP and ranks.** Each level is worth XP based on its difficulty (100-800, or 1500 for the boss). Ranks go
  Script Kiddie → Prompt Wrangler → Jailbreaker → Red Teamer → AGI Whisperer. A badge in the header shows your rank
  and XP.
- **Siege animation on every correct submit.** Gremlins march in and attack the level's tower (or the final
  level's fortress) until it collapses under their flag. A banner then shows the XP gained (first clears only), any new
  rank and the next level, and the chat continues on that level. It also plays for level 0 and for re-solves. The
  chat route returns `solved`, read from `submit_answer_func`'s tool response; a marker in model text doesn't
  count.
- **Deterministic `/submit`.** "submit answer: X" is routed straight to `submit_answer_func` without a model call.
  A level agent checks the answer against its own level, before the guards run. The coordinator checks it against
  the level whose password it matches. Previously the small model sometimes guessed the wrong level, so correct
  answers failed.
- **Recent solves.** The start screen lists the latest level completions across all players.
- **Bookmarkable sessions.** `/ctf/<session-id>` opens a specific conversation.
- **New slash commands:**
  - `/register <username> [session-id]` registers from the chat, under the register page's rate limit.
  - `/start` goes to level 0, and `/continue` goes to your lowest unsolved level.
  - `/whoami` shows your username, session ID, completed levels, rank and next level.
  - `/challenges [level]` lists every level or shows one level's briefing.
  - `/faq` lists the FAQ topics.
  - `/discord` gives the Discord link.
  - `/leaderboard` renders the top 10 in the chat instead of asking the agent.
- **Changing levels from inside a level.** Typing "level N" inside any level agent moves you to level N before the
  guards run, so a guard can't block you from leaving.
- **`web_search` tool for level 9.** It replaces ADK's `google_search` and returns titles, URLs and snippets that
  the agent can pass to `web_scrape`.
- `make prepare-flags` seeds the level passwords for a local agent. It runs from `ctf/agents` like the container
  does, so the agent finds the LanceDB table and `users.db`. Docker seeds on start instead.

### Changed
- `/challenges`, `/faq` and `/discord` work before you register.
- Web search uses `ddgs` and tries DuckDuckGo, Yahoo and Google in turn. The old package picked a random backend,
  and some backends time out.
- The `google-adk[eval]` extra moved to the dev dependency group.
- Docker Compose now seeds the passwords on every start (`PREPARE_FLAGS=1`) and keeps LanceDB in a named
  `lancedb_data` volume instead of bind mounts.
- The FAQ (`/faq`) has new Commands, Scoring and ranks, and Troubleshooting sections. It now uses the right tool
  names and gives level-specific techniques for levels 5, 8 and 9. The challenge briefings no longer mention
  OpenAI or GPT-4o. The developer docs (`ADK_INTEGRATION.md`, `web/README.md`, `ctf/agents/*.md`, `DOCKER.md`)
  describe `/run_sse` streaming, run tracking, model-free routing and the real agent layout.
- Challenge difficulty is defined once in `web/lib/challenges.ts` and shared by the challenges page and the
  quest map.

### Fixed
- Hints listed `password_search_func` on every level, including levels 5, 8 and 11-14, which don't have it.
  Each level's hints now list that level's own tools.
- A correct submit on a guarded level (such as Hold the Fort) could end with a block notice: the model's
  follow-up re-ran the input guards on the submit message, and the output guards blocked it repeating the
  password the player had just typed. Input guards now screen only the player's own turn, not the model's
  follow-up to a tool result, and output guards allow a password the player sent that turn.
- Solving the final level without having cleared every level crashed the agent run. `submit_answer_func` tried to
  transfer the player to a level after the last one, which doesn't exist. It now stays on the final level and
  says which levels are left.
- `password_search_func` (the RAG levels) returned "Error searching the database" in Docker. Results were read
  with `.to_pandas()`, and pandas was only installed as a side effect of `google-adk[eval]`, which is now a dev-only
  dependency. Results are now read with `.to_list()`, so pandas isn't needed.

### Removed
- The old chat welcome screen (`web/components/chat/welcome.tsx`), replaced by the quest-map start screen.

## 2026-10-27 to 2026-10-28

### Added
- Slash commands with autocomplete (`/help`, `/level`, `/newsession`, `/hint`, `/submit`, `/leaderboard`).
- **Skills.** Players can save reusable prompts with `/skills install <name> <instructions>` or by uploading a
  `SKILL.md`. They run as `/<name>` and are removed with `/skills remove`.
- The coordinator routes "level N" requests directly to the level agent. Each level greets the player after a
  handover.
- Guardrail fixes, with tests covering the guards and the level router.
- The leaderboard has stat cards and a recent-completions feed, and it refreshes every 30 seconds.
- The challenges page has difficulty meters, OWASP LLM Top 10 tags and level quick links.
- The register page and the sidebar were redesigned. New PwnGPT logo, icon and footer.
- Agents built with `thinking_planner` return the model's thoughts with each response. Other agents drop qwen3's
  thought parts.

## 2026-10-21: Next.js migration

### Added
- New web app in `web/`: Next.js 16.4 on vinext (Vite), Tailwind CSS v4, shadcn/ui and Watermelon UI animations.
- The web app took over registration, username ownership tokens, the chat proxy to ADK `/run`, chat history,
  the leaderboard, the FAQ, the challenges, rate limiting and `/health`.
- The web app runs in Docker beside the agent and shares Postgres with it.
- Cloudflare Workers deployment target.

### Removed
- The FastAPI frontend and the frontend-only Python under `ctf/`.

### Changed
- The per-IP rate limiter now resolves the client IP more strictly, and the post-migration config was tidied.
- CI builds the web app with the Node version in `web/.nvmrc`.

## Earlier

- Version 2 was rebuilt on Google ADK, with a coordinator agent and one agent per level (0-10), LanceDB RAG, Hugging
  Face guard models and Ollama `qwen3` support. It has been run at BSides Cape Town and other events.
- Dependency bumps and lint fixes.
