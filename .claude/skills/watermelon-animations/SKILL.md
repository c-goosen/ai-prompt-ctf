---
name: watermelon-animations
description: Find Watermelon UI animated components and port them to this Jinja/HTMX/Tailwind-CDN frontend as vanilla CSS/JS. Use when adding or changing UI animations, micro-interactions, or when the user mentions Watermelon.
---

# Watermelon UI animations for PwnGPT

[Watermelon UI](https://ui.watermelon.sh/animated-components) ships ~130 animated
components. They are **React + `motion/react`** (a few use `framer-motion`) and
are normally installed with `npx shadcn add`. This frontend is **Jinja + HTMX 4 +
Tailwind CDN + DaisyUI 4** with no React and no build step, so components are
**ported** to plain CSS and a little vanilla JS. Never run `npx shadcn` here.

The registry is MIT licensed: keep the attribution header in the files below.

## 1. Find a component

All endpoints are public, read-only and need no API key.

```bash
# Search (max 50 results per call and there is no offset: narrow with query/category)
curl -s "https://ui.watermelon.sh/api/catalog/entries?kind=animated-components&query=copy&limit=50" \
  | jq -r '.entries[] | "\(.slug)\t\(.category)\t\(.description)"'

# Every animated-component slug
curl -s https://ui.watermelon.sh/sitemap.xml | grep -o 'animated-components/[a-z0-9-]*' | sort -u

# Read the source (TSX) of one component
curl -s https://registry.watermelon.sh/r/<slug>.json | jq -r '.files[].content'
```

Preview: `https://ui.watermelon.sh/animated-components/<slug>`.
Optional MCP (ask the user to run it, it changes their config):
`claude mcp add --transport http watermelon https://mcp.watermelon.sh/mcp`.

Pick components that fit a dark neon chat UI. Skip ones whose value is mostly
React state (forms, dashboards); port the *motion*, not the markup.

## 2. Port motion to CSS/JS

| motion/react | Here |
|---|---|
| `initial` / `animate` / `exit` | `@keyframes` + a class added by JS |
| `AnimatePresence` | add/remove a class on `htmx:after:swap`; clean up on `animationend` |
| `transition: {type:'spring'}` (bouncy) | `cubic-bezier(0.34, 1.56, 0.64, 1)`, 300-450ms |
| spring with `bounce: 0` | `cubic-bezier(0.2, 0, 0, 1)`, 300-450ms |
| `layoutId` shared element | one absolutely positioned element moved with `transform` / `height` transitions |
| `whileHover` / `whileTap` | `:hover` / `:active` transforms |
| `filter: blur()` keyframes | same, in `@keyframes` |
| staggered children | inline `style="--i: N"` + `animation-delay: calc(var(--i) * 30ms)` |
| `repeat: Infinity` | `animation-iteration-count: infinite` |

## 3. Project conventions

- CSS: `ctf/frontend/static/assets/css/animations.css`. JS:
  `ctf/frontend/static/assets/js/animations.js` (one IIFE guarded by
  `window.__pwnAnimations`). Both are loaded from `templates/base.html`.
  Start each port with a `/* watermelon: <slug> */` section comment.
- Colours come from the neon palette in `pwngpt.css`: `#3cfcd1` (teal),
  `#ff2fd5` (pink), `rgba(92, 36, 255, …)` (violet), text `#e8e6ff`.
- Every animation needs a `@media (prefers-reduced-motion: reduce)` override;
  JS checks the `reduceMotion` flag before starting timers.
- HTMX 4 event names: `htmx:before:request`, `htmx:after:request`,
  `htmx:after:swap`, `htmx:response:error` (not the htmx 1/2 `htmx:afterSwap`).
- Chat content is rendered by `<md-block>` *after* the swap, so react to new
  `pre`/`code` nodes with a `MutationObserver`, not straight after the swap.
- `navigator.clipboard` only exists in secure contexts; the app is often served
  over plain http on `0.0.0.0`, so keep the `execCommand('copy')` fallback.
- djlint (`make ci-lint`) rejects `type=` on `<script>`/`<style>` (H024).

## 4. Checklist

1. Port into `animations.css` / `animations.js`, then add classes or hooks in templates.
2. `make ci-lint` and `PYTEST_CURRENT_TEST=true make ci-test`.
3. Run the app (see the `run-ctf` skill; a quick option is
   `PYTEST_CURRENT_TEST=1 uv run uvicorn ctf.frontend.app:app --port 8101`) and
   check the animation in Chrome. Record a GIF of the interaction, and check it
   again with DevTools' "Emulate prefers-reduced-motion: reduce".
