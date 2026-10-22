import { afterEach, describe, expect, it, vi } from "vitest";

import { POST as register } from "@/app/api/register/route";
import { getLeaderboard } from "@/lib/leaderboard";
import { json, mockAdk, request, useTestDb } from "@/test/helpers";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("JSON registration", () => {
  useTestDb();

  it.each(["../x", "a/b", "..", ".hidden", "x".repeat(33), "a b", "a?b=c"])(
    "rejects unsafe username %s",
    async (username) => {
      const calls = mockAdk(() => json({}));
      const response = await register(request("/api/register", { method: "POST", json: { username } }));
      expect(response.status).toBe(400);
      expect((await response.json()).detail).toBe("Invalid username");
      expect(calls).toEqual([]);
    },
  );

  it("rejects an unsafe session id and a missing username", async () => {
    mockAdk(() => json({}));
    const badSession = await register(
      request("/api/register", { method: "POST", json: { username: "erin", session_id: "../escape" } }),
    );
    expect((await badSession.json()).detail).toBe("Invalid session ID");
    const missing = await register(request("/api/register", { method: "POST", json: {} }));
    expect(missing.status).toBe(400);
    expect((await missing.json()).detail).toBe("Username is required");
  });

  it("registers, sets httpOnly cookies, and blocks takeover", async () => {
    mockAdk(() => json({ id: "s" }));
    const first = await register(request("/api/register", { method: "POST", json: { username: "alice" } }));
    expect(first.status).toBe(200);
    const body = await first.json();
    expect(body.player_token).toMatch(/^[A-Za-z0-9_-]{43}$/);
    const cookies = first.headers.getSetCookie().join("\n");
    expect(cookies).toMatch(/player_token=[^;]+;.*HttpOnly/i);
    expect(cookies).toMatch(/anon_user_identity=alice/);
    expect((await getLeaderboard()).map((row) => row.username)).toEqual(["alice"]);

    const takeover = await register(request("/api/register", { method: "POST", json: { username: "alice" } }));
    expect(takeover.status).toBe(409);
  });

  it("releases a new claim when ADK session creation fails", async () => {
    mockAdk(() => json({ detail: "boom" }, 500));
    const failed = await register(request("/api/register", { method: "POST", json: { username: "frank" } }));
    expect(failed.status).toBe(502);

    mockAdk(() => json({ id: "s" }));
    const retry = await register(request("/api/register", { method: "POST", json: { username: "frank" } }));
    expect(retry.status).toBe(200);
  });
});

describe("registration without a database", () => {
  it("returns 503 instead of crashing", async () => {
    const { setDbForTesting } = await import("@/lib/db");
    setDbForTesting({
      dialect: "sqlite",
      query: async () => {
        throw new Error("database is down");
      },
      close: async () => {},
    });
    vi.spyOn(console, "error").mockImplementation(() => {});
    mockAdk(() => json({}));
    const response = await register(request("/api/register", { method: "POST", json: { username: "gina" } }));
    expect(response.status).toBe(503);
    setDbForTesting(null);
  });
});
