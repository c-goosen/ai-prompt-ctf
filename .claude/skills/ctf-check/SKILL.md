---
name: ctf-check
description: Run the same lint and test checks as CI locally (black, flake8, djlint, pytest). Use before committing or pushing, or when the user asks to run checks, lint, or tests.
---

# Run CI checks locally

Mirrors `.github/workflows/ci.yml` (`make ci-lint`, `make ci-test`).

1. `uv sync --dev --locked`
2. `make lint` — `black --check`, `flake8`, `djlint ctf/frontend/templates/ --lint`
   - If black or djlint formatting fails: `make format`, then re-run `make lint`.
   - Fix flake8 findings by hand; don't add `# noqa` unless the line is a long prompt string (existing convention).
3. Tests with CI's environment:
   ```bash
   OPENAI_API_KEY="" HUGGINGFACE_API_KEY="" PYTEST_CURRENT_TEST=true make test
   ```
   For a quick loop, target files: `uv run pytest ctf/tests/test_app.py -x`.
   `ctf/tests/eval/` needs a live model — see the `ctf-eval` skill; exclude it with `--ignore=ctf/tests/eval` if Ollama isn't running.

Optional: `make security` (bandit). This CTF contains intentionally vulnerable code, so findings are reviewed manually, not treated as failures.

Report which steps passed or failed with the relevant output.
