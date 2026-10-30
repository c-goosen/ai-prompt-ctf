import { NextRequest } from "next/server";
import { afterEach, beforeEach, vi } from "vitest";

import { openSqliteForTesting, setDbForTesting, type Db } from "@/lib/db";

/** Fresh in-memory SQLite database per test, wired in as the app's DB. */
export function useTestDb(): { db: () => Db } {
  let db: Db;
  beforeEach(async () => {
    db = await openSqliteForTesting();
    setDbForTesting(db);
  });
  afterEach(async () => {
    setDbForTesting(null);
    await db.close();
  });
  return { db: () => db };
}

/** Replace global fetch (the ADK API) with a recording mock. */
export function mockAdk(handler: (url: string, init?: RequestInit) => Response | Promise<Response>) {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const fetchMock = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    calls.push({ url, init });
    return handler(url, init);
  });
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

export function request(
  path: string,
  init: { method?: string; cookies?: Record<string, string>; body?: BodyInit; json?: unknown } = {},
): NextRequest {
  const headers = new Headers();
  if (init.cookies) {
    headers.set(
      "cookie",
      Object.entries(init.cookies)
        .map(([key, value]) => `${key}=${value}`)
        .join("; "),
    );
  }
  let body = init.body;
  if (init.json !== undefined) {
    headers.set("content-type", "application/json");
    body = JSON.stringify(init.json);
  }
  return new NextRequest(`http://localhost${path}`, { method: init.method ?? "GET", headers, body });
}

export const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });

/** An ADK /run_sse response streaming the given events. */
export const sse = (events: unknown[]) =>
  new Response(events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(""), {
    headers: { "content-type": "text/event-stream" },
  });
