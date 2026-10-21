import { describe, expect, it } from "vitest";

import { RateLimiter, clientIp, isExempt, limitFor } from "./rate-limit";

describe("rate limiting", () => {
  it("allows up to the limit within a window, then reports retry-after", () => {
    const limiter = new RateLimiter();
    const limit = limitFor("/faq"); // 1 per minute
    expect(limiter.hit("ip|GET|/faq", limit, 0).allowed).toBe(true);
    const second = limiter.hit("ip|GET|/faq", limit, 1_000);
    expect(second).toEqual({ allowed: false, retryAfter: 59 });
    expect(limiter.hit("ip|GET|/faq", limit, 60_000).allowed).toBe(true);
  });

  it("uses the 15/minute default for unlisted routes", () => {
    expect(limitFor("/v1/chat/completions")).toEqual({ requests: 15, windowMs: 60_000 });
  });

  it("exempts health checks and static assets", () => {
    expect(isExempt("/health")).toBe(true);
    expect(isExempt("/_next/static/chunk.js")).toBe(true);
    expect(isExempt("/faq")).toBe(false);
  });

  it("ignores client-supplied X-Forwarded-For entries", () => {
    // nginx appends the real client address to whatever the client sent.
    expect(clientIp(new Headers({ "x-forwarded-for": "6.6.6.6, 1.2.3.4" }))).toBe("1.2.3.4");
    expect(
      clientIp(new Headers({ "x-forwarded-for": "6.6.6.6", "x-real-ip": "1.2.3.4" })),
    ).toBe("1.2.3.4");
    expect(clientIp(new Headers({ "cf-connecting-ip": "5.5.5.5", "x-real-ip": "1.2.3.4" }))).toBe("5.5.5.5");
  });
});
