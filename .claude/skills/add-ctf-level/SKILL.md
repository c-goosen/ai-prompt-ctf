---
name: add-ctf-level
description: Add a new CTF challenge level (agent, password, coordinator wiring, docs). Use when the user wants to add a level, create a new challenge, or add a protection/guard to a new level.
---

# Add a CTF level

Read `docs/adding-a-level.md` and do every step in it. It's the single checklist, so make any corrections there rather than here.

Then:
- Add an evalset for the level with the `ctf-eval` skill if behaviour matters.
- Run the `ctf-check` skill for both the Python and web checks.
