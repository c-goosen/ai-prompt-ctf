---
name: add-ctf-level
description: Add a new CTF challenge level (agent, password, coordinator wiring, docs). Use when the user wants to add a level, create a new challenge, or add a protection/guard to a new level.
---

# Add a CTF level

A level is wired up in several places. Do all of them, using the next level number `N` (currently `FINAL_LEVEL` in `ctf/app_config.py` + 1).

## 1. Agent
Create `ctf/agents/sub_agents/level_N_agent.py` subclassing `BaseCTFAgent` (`ctf/agents/sub_agents/base_agent.py`).

- Copy the shape of `level_5_agent.py` (tools only) or `level_10_agent.py` (callbacks + planner).
- Module docstring: level name, what the attack is, and the OWASP LLM Top 10 category.
- `system_prompt = get_system_prompt_one() + """..."""`
- `super().__init__(level=N, system_prompt=..., name="LevelNAgent", tools=[...])`
- Tools live in `ctf/agents/tools.py`; `BaseCTFAgent.get_base_tools()` already supplies the common ones.

### Protections
Bind `level=N` with `functools.partial` and pass as callback lists:
- `before_model_callback`: `guard_rail_input_injection` (`guard_rails.py`), `ProtectionUtils.llm_guard_prompt_injection_meta` / `_goose` (`protection_utils.py`)
- `after_model_callback` / `after_tool_callback`: `ProtectionUtils.detect_password_leak`
- Lower-level checks (input filters, output regex, text normalization) are in `ctf/llm_guard/protections.py`; reuse them rather than writing new filters.

## 2. Coordinator — `ctf/agents/sub_agents/agent.py`
- Import `LevelNAgent` and append `LevelNAgent()` to `level_agents`.
- Add a `- **Level N**: ...` line to the instruction's challenge list.
- Update the "N exciting levels" count in the welcome message.

### Level router — `ctf/agents/sub_agents/level_router.py`
- Raise `MAX_LEVEL` to N, or "level N" and `/level N` won't route.
- Add `N: "<title>"` to `LEVEL_TITLES` (used by the greeting a level agent sends on arrival).
- `BaseCTFAgent` already wires the greeting, level switching, `submit answer:` and hint routing for every level. Keep the new agent's guards in `before_model_callback`, so they run after level switching and submits.

## 3. Config — `ctf/app_config.py`
- Add `N: os.getenv("PASSWORD_<WORD>", "PASS_<WORD>")` to `PASSWORDS`.
- Set `FINAL_LEVEL = N`.

## 4. Web app (`web/`)
- `web/lib/config.ts`: add `"PASSWORD_<WORD>"` to `PASSWORD_ENV_NAMES` (used to redact the
  RAG tool's output) and set `FINAL_LEVEL = N` (leaderboard totals).
- `docker-compose.yml`: add `PASSWORD_<WORD>` to `x-shared-env` so the agent and web app agree.
- `web/lib/slash.ts`: raise `MAX_LEVEL` (the `/level` range, `/challenges`, the quest map and XP all use it).
- `web/lib/progress.ts`: check the XP per difficulty and the rank thresholds still make sense. The new final level
  becomes the 1500 XP boss, and `difficulty()` in `web/lib/challenges.ts` re-spreads the other levels.
- `web/components/game/quest-map.tsx`: the map is laid out for levels 0-10 (two rows ending at the boss), so add
  a node position for the new level.
- `web/content/faq.md`: the level lists, the XP and rank tables, and the technique sections.
- `web/cloudflare/wrangler.jsonc` comment: the secret list for Workers deploys.

## 5. Other hard-coded counts
- `ctf/agents/tools.py`: "completed all N levels" message.
- `grep -rn "11 levels\|Level10" --include=*.py --include=*.ts --include=*.tsx --include=*.md --include=*.MD . --exclude-dir=node_modules` to catch stragglers.

## 6. Docs
- `web/content/challenges.md`: new `# Level N:` section matching existing ones (shown on `/challenges`).
- `README.MD`: add `PASSWORD_<WORD>=` to the password list.
- `ctf/agents/ADK_WEB_README.md`: file tree and agent range.

## 7. Verify
- `ctf/tests/test_vals.py` parametrizes on `FINAL_LEVEL`, so it covers the new level automatically.
- Add an evalset for the level with the `ctf-eval` skill if behaviour matters.
- Run `make format`, then the `ctf-check` skill (both the Python and web checks).
