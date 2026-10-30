// Minimal declaration so `tsc` can check lib/platform.cloudflare.ts without
// pulling Workers types into the Node build.
declare module "cloudflare:workers" {
  export const env: Record<string, unknown>;
  export function waitUntil(promise: Promise<unknown>): void;
}
