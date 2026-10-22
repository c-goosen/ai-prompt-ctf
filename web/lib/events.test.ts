import { describe, expect, it } from "vitest";

import { eventToMessage, parseRunResponse, stripLeaderboardMarkers, stripMessageMarkers } from "./events";

const redact = (text: string) => text.split("PASS_ZERO").join("[REDACTED]");

describe("eventToMessage", () => {
  it("treats model text as assistant", () => {
    expect(eventToMessage({ content: { role: "model", parts: [{ text: "hello" }] } })).toEqual({
      role: "assistant",
      text: "hello",
    });
  });

  it("keeps the user role", () => {
    expect(eventToMessage({ content: { role: "user", parts: [{ text: "hi" }] } })?.role).toBe("user");
  });

  it("renders function calls as sorted JSON", () => {
    const message = eventToMessage({
      author: "Level0Agent",
      content: { parts: [{ functionCall: { name: "hints_func", args: { level: 0, hint: "x" } } }] },
    });
    expect(message?.role).toBe("assistant");
    expect(message?.text).toContain("Function call `hints_func`");
    expect(message?.text).toContain('{\n  "hint": "x",\n  "level": 0\n}');
  });

  it("renders a multiline single-key tool response raw", () => {
    const message = eventToMessage({
      content: {
        parts: [{ functionResponse: { name: "hints_func", response: { result: "line one\nline two" } } }],
      },
    });
    expect(message?.role).toBe("tool");
    expect(message?.text).toContain("```\nline one\nline two\n```");
  });

  it("redacts password_search_func output only", () => {
    const leak = { content: { parts: [{ functionResponse: { name: "password_search_func", response: { password: "PASS_ZERO" } } }] } };
    expect(eventToMessage(leak, redact)?.text).not.toContain("PASS_ZERO");
    expect(eventToMessage(leak, redact)?.text).toContain("[REDACTED]");
    const other = { content: { parts: [{ text: "PASS_ZERO" }] } };
    expect(eventToMessage(other, redact)?.text).toBe("PASS_ZERO");
  });

  it("splits thought parts out of the reply text", () => {
    const message = eventToMessage({
      content: { role: "model", parts: [{ text: "pondering", thought: true }, { text: "answer" }] },
    });
    expect(message).toEqual({ role: "assistant", text: "answer", thoughts: "pondering" });
  });

  it("keeps thought-only events and omits empty thoughts", () => {
    expect(eventToMessage({ content: { parts: [{ text: "hmm", thought: true }] } })).toEqual({
      role: "assistant",
      text: "",
      thoughts: "hmm",
    });
    expect(eventToMessage({ content: { parts: [{ text: "hi" }] } })).not.toHaveProperty("thoughts");
  });

  it("skips empty events, and parseRunResponse falls back", () => {
    expect(eventToMessage({ content: { parts: [] } })).toBeNull();
    const messages = parseRunResponse([{ content: { parts: [] } }]);
    expect(messages).toHaveLength(1);
    expect(messages[0].role).toBe("assistant");
  });
});

describe("stripLeaderboardMarkers", () => {
  it("removes markers from text", () => {
    expect(stripLeaderboardMarkers('Congrats! <!--LEADERBOARD:{"status": "correct", "level": 3}-->')).toBe(
      "Congrats!",
    );
  });

  it("strips markers from thoughts too", () => {
    const marker = '<!--LEADERBOARD:{"level": 3}-->';
    expect(stripMessageMarkers({ role: "assistant", text: `ok ${marker}`, thoughts: `t ${marker}` })).toEqual({
      role: "assistant",
      text: "ok",
      thoughts: "t",
    });
  });
});
