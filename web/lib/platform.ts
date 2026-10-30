/**
 * Platform hooks. This is the Node (Docker / local) version; the Cloudflare
 * build aliases "@/lib/platform" to platform.cloudflare.ts instead
 * (see vite.config.cloudflare.ts).
 */

/** A database URL supplied by the platform rather than the environment. */
export function platformDatabaseUrl(): string | undefined {
  return undefined;
}

/** Whether DB connections must be opened per request (not shared). */
export const REQUEST_SCOPED_DB = false;

/**
 * Keep the server working on `promise` after the response is sent. Node keeps
 * running pending work on its own, so there is nothing to do here.
 */
export function keepAlive(promise: Promise<unknown>): void {
  void promise;
}
