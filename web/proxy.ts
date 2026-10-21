import { NextResponse, type NextRequest } from "next/server";

import { RateLimiter, clientIp, describeLimit, isExempt, limitFor } from "./lib/rate-limit";

const limiter = new RateLimiter();

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  // Router prefetches aren't user navigations; counting them would spend the
  // tight /faq and /leaderboard budgets before anyone clicked.
  if (isExempt(pathname) || request.headers.has("next-router-prefetch")) {
    return NextResponse.next();
  }
  const limit = limitFor(pathname);
  const key = `${clientIp(request.headers)}|${request.method}|${pathname}`;
  const result = limiter.hit(key, limit);
  if (result.allowed) {
    return NextResponse.next();
  }
  return NextResponse.json(
    { error: `Rate limit exceeded: ${describeLimit(limit)}` },
    { status: 429, headers: { "Retry-After": String(result.retryAfter) } },
  );
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
