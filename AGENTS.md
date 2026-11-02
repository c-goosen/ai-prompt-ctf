# AGENTS.md

PwnGPT is a prompt injection CTF with 16 levels (0-15). Players attack LLM agents to extract a password at each level.

## Stack

| Path | What | Tooling |
|---|---|---|
| `ctf/agents/` | Level agents, built with Google ADK | Python 3.13-3.14, `uv` |
| `ctf/llm_guard/` | Input and output protections used by the levels | `uv` |
| `ctf/tests/` | Python tests | `pytest` |
| `web/` | UI and non-agent server logic: Next.js 16.4 on vinext (Vite), Tailwind v4, shadcn/ui | Node 24, `pnpm` |

- Models run through Ollama (`qwen3:0.6b`) by default, or Gemini or OpenAI. LanceDB is the vector store.
- Use `uv` for all Python dependencies (`uv add`, `uv remove`, `uv sync`), never `pip` or `poetry`.
- Use `pnpm` for `web/`, never `npm` or `yarn`.

## Before you commit

CI runs on every push and checks both stacks. Run the checks for whatever you changed.

**Python**
```bash
uv sync --dev --locked
make format    # black, in place
make ci-lint   # black --check and flake8
OPENAI_API_KEY="" HUGGINGFACE_API_KEY="" PYTEST_CURRENT_TEST=true make ci-test
```

- Black's style changes between releases. A black bump in `uv.lock` can reformat files you didn't touch; commit those too, or CI fails.
- Fix flake8 findings by hand. Only add `# noqa` to a long prompt string.

**Web**
```bash
pnpm --dir web install --frozen-lockfile
pnpm --dir web lint
pnpm --dir web typecheck
pnpm --dir web test
pnpm --dir web build
pnpm --dir web build:next
pnpm --dir web build:cf
```

`web/` has no code formatter, so follow the style of the file you're editing.

## Run it

```bash
make run                 # full stack in Docker; web app on http://localhost:8100
```

Without Docker, the agent needs `ollama serve` and `ollama pull qwen3:0.6b` first (or `USE_GEMINI=1`). Levels 10, 11 and 15 also need `ollama pull d1-omni:600m`, even on Gemini. Then run these in two terminals:
```bash
make prepare-flags && cd ctf/agents && uv run adk web --host 127.0.0.1 --port 8000
make web-install && make web-dev    # http://localhost:3000
```

## Things to know

- **The vulnerabilities are the product.** Level agents, their prompts and their tools are meant to be attackable at each level's difficulty. Don't harden them, or treat `make security` (bandit) findings as bugs, unless asked.
- **Keep passwords out of the repo.** Levels read them from `PASSWORD_*` environment variables, and the `PASS_*` defaults are for local use only. Never commit `.env`.
- **Some tests are skipped by default.** `adk_api` tests need a running agent and `llm_eval` tests need a real model, so a green `make ci-test` doesn't cover agent behaviour.
- **Eval scores are noisy.** Small models vary between runs, so don't loosen thresholds just to make a case pass.
- **Adding a level touches many files**, across the agent, router, config, web app, compose and docs. Follow the playbook below rather than working from one existing level.

## Playbooks

These task guides are plain Markdown, and most were written for Claude Code. Read the matching one before starting that task. Mentions of "the `ctf-check` skill" and similar refer to the other guides in this table.

| Task | Guide |
|---|---|
| Add a CTF level | `docs/adding-a-level.md` |
| Run CI checks locally | `.claude/skills/ctf-check/SKILL.md` |
| Write or run agent evals | `.claude/skills/ctf-eval/SKILL.md` |
| Remove AI-generated slop from a branch | `.claude/skills/deslop/SKILL.md` |
| Run the stack, including the Cloudflare preview | `.claude/skills/run-ctf/SKILL.md` |
| Add UI animations | `.claude/skills/watermelon-animations/SKILL.md` |

## More docs

- `README.MD`: project overview
- `CONTRIBUTING.md`: how to contribute
- `docs/developing.md`: local setup and debugging with the ADK dev UI
- `ADK_INTEGRATION.md`: how the web app and agents connect
- `DOCKER.md`: Compose setup and hosting an event
- `web/README.md`: web app details
- [Google ADK docs](https://google.github.io/adk-docs/)
