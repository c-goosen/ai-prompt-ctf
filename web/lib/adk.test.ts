import { afterEach, describe, expect, it, vi } from "vitest";

import { json, mockAdk, sse } from "@/test/helpers";

import { getSessionHistory, runAgent } from "./adk";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

/** ADK double: sessions exist, /run_sse answers with `run`. */
const adkRun = (run: (init?: RequestInit) => Response) =>
  mockAdk((url, init) => (url.endsWith("/run_sse") ? run(init) : json({ id: "s", events: [] })));

describe("runAgent", () => {
  it("keeps the messages received before a mid-run error", async () => {
    adkRun(() =>
      sse([
        { content: { parts: [{ functionCall: { name: "hints_func", args: {} } }] } },
        { error: "AttributeError: boom" },
      ]),
    );
    vi.spyOn(console, "error").mockImplementation(() => {});
    const messages = await runAgent("alice", "s1", "hint please");
    expect(messages.map((m) => m.text)).toEqual([
      expect.stringContaining("Function call `hints_func`"),
      "Sorry, there was an error processing your request. Please try again.",
    ]);
  });

  it("throws when the run fails before any message", async () => {
    adkRun(() => sse([{ error: "AttributeError: boom" }]));
    await expect(runAgent("alice", "s1", "hi")).rejects.toThrow("AttributeError: boom");
  });

  it("times out a stream that goes quiet, keeping what arrived", async () => {
    vi.stubEnv("ADK_RUN_TIMEOUT_MS", "50");
    vi.spyOn(console, "error").mockImplementation(() => {});
    adkRun((init) => {
      const encoder = new TextEncoder();
      const body = new ReadableStream<Uint8Array>({
        start(controller) {
          const event = { content: { role: "model", parts: [{ text: "partial answer" }] } };
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
          init?.signal?.addEventListener("abort", () => controller.error(init.signal!.reason));
        },
      });
      return new Response(body, { headers: { "content-type": "text/event-stream" } });
    });
    const messages = await runAgent("alice", "s1", "hi");
    expect(messages.map((m) => m.text)).toEqual([
      "partial answer",
      "Sorry, the agent took too long to respond. Please try again.",
    ]);
  });
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
