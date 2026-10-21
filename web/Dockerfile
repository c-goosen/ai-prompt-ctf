# PwnGPT web app (Next.js 16.4 API on vinext), built as a standalone Node server.
# Build context is web/ (see docker-compose.yml).

FROM node:24-slim AS build
RUN npm install -g pnpm@11.21.0
WORKDIR /app

# Dependencies first for better layer caching.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM node:24-slim AS production
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=8100
WORKDIR /app

# dist/standalone holds server.js, the client/server bundles, public/ and the
# runtime node_modules it needs, so nothing else from the build is copied.
COPY --from=build --chown=node:node /app/dist/standalone ./

USER node
EXPOSE 8100/tcp
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:8100/health').then((r) => process.exit(r.ok ? 0 : 1), () => process.exit(1))"]
CMD ["node", "server.js"]
