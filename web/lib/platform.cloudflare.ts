/**
 * Cloudflare Workers platform hooks (aliased in by vite.config.cloudflare.ts).
 *
 * Postgres is reached through a Hyperdrive binding named HYPERDRIVE (see
 * wrangler.jsonc). String vars and secrets (ADK_API_URL, PASSWORD_*, ...)
 * arrive on process.env via the nodejs_compat flag, so only the binding
 * needs special handling.
 */
import { env, waitUntil } from "cloudflare:workers";

export function platformDatabaseUrl(): string | undefined {
  return (env as { HYPERDRIVE?: { connectionString: string } }).HYPERDRIVE?.connectionString;
}

/**
 * Workers forbid using a socket opened by one request from another, so each
 * request gets its own Postgres client. Hyperdrive pools the real
 * connections, which keeps this cheap.
 */
export const REQUEST_SCOPED_DB = true;

/**
 * Keep the Worker alive until `promise` settles, so an agent run finishes
 * even after the player closes the tab (lib/runs.ts).
 */
export function keepAlive(promise: Promise<unknown>): void {
  waitUntil(promise);
}
