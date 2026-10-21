import { afterEach, describe, expect, it, vi } from "vitest";

import { GET as health } from "@/app/health/route";
import { json, mockAdk } from "@/test/helpers";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("/health", () => {
  it("is healthy when ADK /health answers", async () => {
    mockAdk(() => json({ status: "ok" }));
    const body = await (await health()).json();
    expect(body).toMatchObject({ health: "ok", status: "healthy" });
  });

  it("falls back to /list-apps when /health is missing", async () => {
    const calls = mockAdk((url) => (url.endsWith("/health") ? json({}, 404) : json(["sub_agents"])));
    const body = await (await health()).json();
    expect(body.status).toBe("healthy");
    expect(calls.map((call) => new URL(call.url).pathname)).toEqual(["/health", "/list-apps"]);
  });

  it("reports degraded when ADK is unreachable", async () => {
    mockAdk(() => {
      throw new Error("connect ECONNREFUSED");
    });
    const body = await (await health()).json();
    expect(body).toMatchObject({ health: "ok", status: "degraded" });
    expect(body.services.adk_api.error).toContain("ECONNREFUSED");
  });
});
