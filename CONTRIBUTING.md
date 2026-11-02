# Contributing

New challenges, fixes and docs are all welcome.

1. **Set up:** follow [Developing](docs/developing.md).
2. **Add a challenge:** follow [Adding a level](docs/adding-a-level.md).
3. **Run the checks:** the commands CI runs are listed under [Before you commit](AGENTS.md#before-you-commit). Python formatting is enforced, so run `make format` first.

Level agents are vulnerable on purpose, at each level's difficulty. If you find a way to beat a level, that's the game, not a bug. Do report a way to get a password or a leaderboard credit that goes around the level, such as a flaw in the web app.

Never commit real event passwords or a `.env` file.
