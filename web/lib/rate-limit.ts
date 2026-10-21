/**
 * Fixed-window per-IP rate limiting, keeping the limits the FastAPI app had
 * (slowapi), which exist to keep LLM costs down.
 *
 * State is per server instance (in memory). That is fine for the single
 * Docker container; on Cloudflare Workers each isolate counts separately,
 * so treat it as best effort there.
 */

export interface Limit {
  requests: number;
  windowMs: number;
}

const SECOND = 1_000;
const MINUTE = 60 * SECOND;

/** Default for any route not listed below (slowapi default_limits). */
export const DEFAULT_LIMIT: Limit = { requests: 15, windowMs: MINUTE };

/** Per-route limits, matched on exact pathname. */
export const ROUTE_LIMITS: Record<string, Limit> = {
  "/": { requests: 1, windowMs: SECOND },
  "/faq": { requests: 1, windowMs: MINUTE },
  "/challenges": { requests: 60, windowMs: MINUTE },
  "/leaderboard": { requests: 5, windowMs: MINUTE },
  "/register": { requests: 5, windowMs: MINUTE },
  "/api/register": { requests: 5, windowMs: MINUTE },
};

/** Paths that are never limited: health checks and static assets. */
export function isExempt(pathname: string): boolean {
  return (
    pathname === "/health" ||
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/assets/") ||
    pathname.startsWith("/images/") ||
    pathname === "/favicon.ico"
  );
}

export function limitFor(pathname: string): Limit {
  return ROUTE_LIMITS[pathname] ?? DEFAULT_LIMIT;
}

export class RateLimiter {
  private windows = new Map<string, { start: number; count: number }>();

  constructor(private readonly maxKeys = 10_000) {}

  /** Record a hit; returns the seconds to wait if the limit is exceeded. */
  hit(key: string, limit: Limit, now = Date.now()): { allowed: true } | { allowed: false; retryAfter: number } {
    const current = this.windows.get(key);
    if (!current || now - current.start >= limit.windowMs) {
      if (this.windows.size >= this.maxKeys) {
        this.evictExpired(now, limit.windowMs);
      }
      this.windows.set(key, { start: now, count: 1 });
      return { allowed: true };
    }
    if (current.count < limit.requests) {
      current.count += 1;
      return { allowed: true };
    }
    return {
      allowed: false,
      retryAfter: Math.max(1, Math.ceil((current.start + limit.windowMs - now) / 1000)),
    };
  }

  private evictExpired(now: number, windowMs: number) {
    for (const [key, value] of this.windows) {
      if (now - value.start >= windowMs) {
        this.windows.delete(key);
      }
    }
    if (this.windows.size >= this.maxKeys) {
      this.windows.clear();
    }
  }
}

/** Client IP, preferring X-Forwarded-For like slowapi's get_ipaddr. */
export function clientIp(headers: Headers): string {
  const forwarded = headers.get("x-forwarded-for");
  if (forwarded) {
    return forwarded.split(",")[0].trim();
  }
  return headers.get("cf-connecting-ip") ?? headers.get("x-real-ip") ?? "unknown";
}

export function describeLimit(limit: Limit): string {
  const unit = limit.windowMs === SECOND ? "second" : "minute";
  return `${limit.requests} per 1 ${unit}`;
}
