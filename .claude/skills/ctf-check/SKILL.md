---
name: ctf-check
description: Apply formatting, then run the same lint, type and test checks as CI locally, for the Python agent (black, flake8, pytest) and the Next.js web app (eslint, tsc, vitest, vinext/Next/Workers builds). Use before committing or pushing, or when the user asks to format code or run checks, lint, or tests.
---

# Run CI checks locally

Mirrors `.github/workflows/ci.yml`: a Python job (`make ci-lint`, `make ci-test`) and a `web` job.

## Python agent
1. `uv sync --dev --locked` — black's style changes between releases, so an out-of-date local version can pass files that CI rejects.
2. `make format` — applies black in place. A black bump in `uv.lock` can reformat files you didn't touch; commit those too, or CI fails.
3. `make ci-lint` — `black --check`, `flake8` (both skip `web/`)
   - Fix flake8 findings by hand; don't add `# noqa` unless the line is a long prompt string (existing convention).
4. Tests with CI's environment:
   ```bash
   OPENAI_API_KEY="" HUGGINGFACE_API_KEY="" PYTEST_CURRENT_TEST=true make ci-test
   ```
   `ctf/tests/test_vals.py` (marked `adk_api`) needs a running agent and is deselected by default.
   `ctf/tests/eval/` needs a live model — see the `ctf-eval` skill.

## Web app (`web/`)
```bash
pnpm --dir web install --frozen-lockfile
pnpm --dir web lint
pnpm --dir web typecheck
pnpm --dir web test          # vitest: validation, ownership/IDOR, register, events, leaderboard, rate limits
pnpm --dir web build         # vinext → dist/standalone (Docker)
pnpm --dir web build:next    # Next.js 16.4 compatibility build
pnpm --dir web build:cf      # vinext → Cloudflare Worker
```
`make lint` / `make test` run both stacks; `make web-build` runs the first two builds.

Optional: `make security` (bandit). This CTF contains intentionally vulnerable code, so findings are reviewed manually, not treated as failures.

Report which steps passed or failed with the relevant output.
