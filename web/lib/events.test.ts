import { describe, expect, it } from "vitest";

import {
  eventToMessage,
  parseRunResponse,
  solvedLevels,
  splitToolSections,
  stripLeaderboardMarkers,
  stripMessageMarkers,
} from "./events";

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

describe("ADK error events", () => {
  it("turns an error-only event into a notice", () => {
    expect(eventToMessage({ errorCode: "MALFORMED_FUNCTION_CALL", errorMessage: "bad args" })).toEqual({
      role: "assistant",
      text: "The model made an invalid tool call. Please try again.",
    });
  });

  it("keeps the thoughts of a thought-only turn and explains the missing answer", () => {
    expect(
      eventToMessage({
        errorCode: "MODEL_RETURNED_NO_CONTENT",
        content: { role: "model", parts: [{ text: "hmm", thought: true }] },
      }),
    ).toEqual({
      role: "assistant",
      text: "The model finished without an answer. Try rephrasing your message.",
      thoughts: "hmm",
    });
  });

  it("falls back to ADK's message for unknown codes", () => {
    expect(eventToMessage({ errorCode: "SAFETY", errorMessage: "blocked" })?.text).toBe(
      "The model failed (SAFETY): blocked",
    );
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

describe("solvedLevels", () => {
  const submitResponse = (result: string, name = "submit_answer_func") => ({
    content: { role: "user", parts: [{ functionResponse: { name, response: { result } } }] },
  });
  const correct = (level: number) =>
    `✅ Correct answer! <!--LEADERBOARD:{"status": "correct", "level": ${level}}-->`;

  it("reads the level submit_answer_func accepted", () => {
    const messages = [submitResponse(correct(0)), submitResponse(correct(3))].map((event) => eventToMessage(event)!);
    expect(solvedLevels(messages)).toEqual([0, 3]);
  });

  it("ignores wrong answers, other tools and markers in model text", () => {
    const events = [
      submitResponse("❌ Incorrect answer."),
      submitResponse(correct(4), "hints_func"),
      { content: { role: "model", parts: [{ text: correct(10) }] } },
    ];
    expect(solvedLevels(events.map((event) => eventToMessage(event)!))).toEqual([]);
  });

  it("is dropped with the markers before messages reach the browser", () => {
    const message = eventToMessage(submitResponse(correct(2)))!;
    expect(message.solved).toBe(2);
    expect(stripMessageMarkers(message)).not.toHaveProperty("solved");
  });
});

describe("splitToolSections", () => {
  it("separates tool calls and responses from text", () => {
    const text = [
      "Let me check.",
      "Function call `hints_func`",
      "```json",
      '{\n  "level": 1\n}',
      "```",
      "Tool response `hints_func`",
      "```",
      "Try asking nicely.",
      "```",
      "Done.",
    ].join("\n");
    expect(splitToolSections(text)).toEqual([
      { kind: "text", text: "Let me check." },
      { kind: "tool", label: "Function call", name: "hints_func", body: '```json\n{\n  "level": 1\n}\n```' },
      { kind: "tool", label: "Tool response", name: "hints_func", body: "```\nTry asking nicely.\n```" },
      { kind: "text", text: "Done." },
    ]);
  });

  it("leaves plain messages whole", () => {
    expect(splitToolSections("Just text, with `code`.")).toEqual([{ kind: "text", text: "Just text, with `code`." }]);
  });
});
