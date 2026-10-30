---
name: watermelon-animations
description: Find Watermelon UI animated components and add them to the PwnGPT web app (web/, Next.js 16.4 on vinext + Tailwind v4 + shadcn/ui), installed from the Watermelon registry and adapted to the neon theme. Use when adding or changing UI animations or micro-interactions, or when the user mentions Watermelon.
---

# Watermelon UI animations for PwnGPT

[Watermelon UI](https://ui.watermelon.sh/animated-components) ships ~130 animated
React components built on `motion/react` and Tailwind, distributed as a shadcn
registry. The web app (`web/`) is React + Tailwind v4 + shadcn/ui, so components
install directly. The registry is MIT licensed: keep the "Adapted from
Watermelon UI" attribution comment at the top of each file.

Already in use (`web/components/watermelon/`): `fluid-tabs` (sidebar nav pill),
`inline-toast` (chat message entrance), `labeled-progress-indicator` (chat
loader), `copy-confirm` (code blocks, session ID), `shimmer-button` (send,
register, start chatting).

## 1. Find a component

All endpoints are public, read-only and need no API key.

```bash
# Search (max 50 results per call and there is no offset: narrow with query/category)
curl -s "https://ui.watermelon.sh/api/catalog/entries?kind=animated-components&query=copy&limit=50" \
  | jq -r '.entries[] | "\(.slug)\t\(.category)\t\(.description)"'

# Every animated-component slug
curl -s https://ui.watermelon.sh/sitemap.xml | grep -o 'animated-components/[a-z0-9-]*' | sort -u

# Read the source and dependencies before installing
curl -s https://registry.watermelon.sh/r/<slug>.json | jq -r '.dependencies, (.files[].content)'
```

Preview: `https://ui.watermelon.sh/animated-components/<slug>`.
Optional MCP (ask the user to run it, it changes their config):
`claude mcp add --transport http watermelon https://mcp.watermelon.sh/mcp`.

## 2. Install

```bash
cd web
pnpm dlx shadcn@4.22.1 add -y https://registry.watermelon.sh/r/<slug>.json
```

Files land in `web/components/watermelon/<slug>.tsx`. Then:

- **Pin new dependencies exactly** in `web/package.json` (shadcn adds `^` ranges), and re-run `pnpm install`.
- **Normalise imports:** use `motion/react` (some components import `framer-motion`) and `lucide-react` icons
  (some use `react-icons`). Then `pnpm remove` whatever is no longer used.
- **Make it a real component:** registry files are demos with hard-coded data and layout wrappers
  (`h-screen`, centred containers). Turn them into props-driven components and drop the wrapper, but keep
  the motion specs (spring stiffness/damping, blur keyframes) that make the component what it is.

## 3. Theme and conventions

- Colours come from the neon tokens in `web/app/globals.css`: `neon-teal` (#3cfcd1), `neon-pink` (#ff2fd5),
  `neon-violet` (#5c24ff), plus the shadcn tokens (`bg-card`, `text-muted-foreground`, `border-border`, …).
  Replace the components' light greys and `dark:` variants; the app is dark only.
- Respect reduced motion: `useReducedMotion()` from `motion/react` for JS-driven loops, `motion-reduce:` for CSS.
- Accessibility: icon-only buttons need `aria-label`; live regions (loaders, chat) use `role="status"` / `aria-live`.
- **Anything importing the `radix-ui` barrel (e.g. `Slot` for `asChild`) must be `"use client"`.** Importing it into
  the RSC environment makes the vinext 1.3 production build spin indefinitely (see `shimmer-button.tsx`).
- Clipboard: `navigator.clipboard` only exists in secure contexts and the app is often served over plain http,
  so keep the `execCommand('copy')` fallback in `copy-confirm.tsx`.
- `next/link` in navigation: `prefetch={false}`. Prefetches don't count against the rate limits (`web/proxy.ts`),
  but they'd still trigger needless server renders.

## 4. Checklist

1. Install, pin, adapt, theme.
2. `pnpm --dir web lint && pnpm --dir web typecheck && pnpm --dir web test`.
3. `pnpm --dir web build && pnpm --dir web build:next && pnpm --dir web build:cf` (a hang in the vinext build
   usually means a client-only module reached a server component; see above).
4. Check it in the browser (`run-ctf` skill: `make web-dev`), including phone width and reduced motion.
