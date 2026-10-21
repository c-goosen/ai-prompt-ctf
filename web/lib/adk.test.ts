import { afterEach, describe, expect, it, vi } from "vitest";

import { json, mockAdk } from "@/test/helpers";

import { getSessionHistory } from "./adk";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getSessionHistory", () => {
  it("strips leaderboard markers and redacts password search output", async () => {
    mockAdk(() =>
      json({
        events: [
          { content: { role: "user", parts: [{ text: "hi" }] } },
          {
            content: {
              parts: [{ functionResponse: { name: "password_search_func", response: { password: "PASS_ZERO" } } }],
            },
          },
          { content: { role: "model", parts: [{ text: 'Done <!--LEADERBOARD:{"status": "correct", "level": 0}-->' }] } },
          { content: { role: "model", parts: [{ text: '<!--LEADERBOARD:{"level": 1}-->' }] } },
        ],
      }),
    );
    const history = await getSessionHistory("alice", "s1");
    expect(history.map((m) => m.text)).toEqual([
      "hi",
      expect.stringContaining("[REDACTED]"),
      "Done",
    ]);
  });

  it("returns an empty history when ADK is down", async () => {
    mockAdk(() => {
      throw new Error("ECONNREFUSED");
    });
    vi.spyOn(console, "warn").mockImplementation(() => {});
    expect(await getSessionHistory("alice", "s1")).toEqual([]);
  });
});
