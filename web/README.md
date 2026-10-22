# PwnGPT web app

The CTF's web UI and all non-agent server logic: Next.js 16.4 (App Router) built and served with
[vinext](https://github.com/cloudflare/vinext) on Vite, styled with Tailwind CSS v4, shadcn/ui and
[Watermelon UI](https://ui.watermelon.sh) components (`components/watermelon/`). The agents themselves are the
Python Google ADK app in `../ctf/agents`.

## Commands

Node version: `.nvmrc` (24.18.0; CI reads it too). With nvm, run `nvm use` in `web/`.

```bash
pnpm install
pnpm dev          # http://localhost:3000 (vinext dev server)
pnpm lint         # eslint (next config)
pnpm typecheck    # tsc
pnpm test         # vitest
pnpm build        # standalone Node server → dist/standalone (node dist/standalone/server.js)
pnpm build:next   # the same app built with next build (Next.js 16.4 compatibility check)
pnpm build:cf     # Cloudflare Worker → dist/server, dist/client
pnpm preview:cf   # run the built Worker locally in workerd (:8787)
pnpm deploy:cf    # build and deploy the Worker
```

`content/*.md` (FAQ, challenges) are compiled to `content/*.generated.ts` by `scripts/build-content.mjs`, which
the scripts above run first.

## Layout

| Path | What |
|---|---|
| `app/` | Pages (`/`, `/ctf`, `/leaderboard`, `/register`, `/faq`, `/challenges`) and route handlers (`/v1/chat/completions`, `/api/register`, `/api/chat/history`, `/session/[username]/[sessionId]`, `/health`) |
| `components/` | UI; `components/watermelon/` holds the adapted Watermelon components |
| `lib/` | Server logic: `adk` (ADK client), `identity` + `register` (username ownership), `events` + `redact` (message parsing), `leaderboard`, `db` (Postgres or SQLite), `rate-limit`, `config` |
| `proxy.ts` | Per-IP rate limits |
| `cloudflare/wrangler.jsonc` | Workers config (kept out of the project root on purpose: vinext treats a root wrangler config as Cloudflare-only) |

## Configuration

| Variable | Default | |
|---|---|---|
| `ADK_API_URL` | `http://127.0.0.1:8000` | ADK API server |
| `POSTGRES_DB_URI` | (unset → SQLite `../ctf/leaderboard.db`) | Must be the same database the agent writes |
| `PASSWORD_ZERO` … `PASSWORD_TEN` | `PASS_ZERO` … | Level passwords, used to redact RAG tool output |
| `CTF_NAME`, `CTF_SUBTITLE`, `DISCORD_URL` | see `lib/config.ts` | Branding |
| `COOKIE_SECURE` | on in production | Set `0` when serving production builds over plain http |
| `HOST`, `PORT` | `0.0.0.0`, `3000` | Standalone server bind address |

## Cloudflare Workers

The Worker runs the web app only; the ADK agent stays on a server reachable over HTTPS (for example via a
Cloudflare Tunnel).

1. Create a Hyperdrive config for the Postgres database the agent uses, and add its binding to
   `cloudflare/wrangler.jsonc` as `HYPERDRIVE`:
   ```bash
   npx wrangler hyperdrive create pwngpt-db --connection-string="postgresql://user:pass@host:5432/ctf"
   ```
2. Set `vars.ADK_API_URL` in `cloudflare/wrangler.jsonc`, and the passwords as secrets:
   `npx wrangler secret put PASSWORD_ZERO` (… `PASSWORD_TEN`).
3. `pnpm deploy:cf`.

On Workers each request opens its own Postgres client (Workers can't share sockets between requests; Hyperdrive
pools the real connections), and the in-memory rate limiter is per isolate, so treat it as best effort.

## Notes

- Keep `radix-ui` imports in client components only: importing the barrel into a server component makes the
  vinext 1.3 build spin indefinitely.
- Chat messages are rendered with `react-markdown` without raw HTML.
