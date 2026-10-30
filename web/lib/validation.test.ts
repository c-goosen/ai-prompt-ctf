import { describe, expect, it } from "vitest";

import { isValidSessionId, isValidUsername } from "./validation";

describe("identifier validation", () => {
  it.each(["pytest-ab12_c.d", "a", "x".repeat(32), "_lead"])("accepts username %s", (name) => {
    expect(isValidUsername(name)).toBe(true);
  });

  it.each(["../x", "a/b", "..", ".hidden", "x".repeat(33), "a b", "a?b=c", "", 42, undefined])(
    "rejects username %s",
    (name) => {
      expect(isValidUsername(name)).toBe(false);
    },
  );

  it("accepts UUID session ids and rejects path-like ones", () => {
    expect(isValidSessionId("0f8fad5b-d9cb-469f-a165-70867728950e")).toBe(true);
    expect(isValidSessionId("a/b")).toBe(false);
    expect(isValidSessionId("../../bob/sessions/x")).toBe(false);
    expect(isValidSessionId("x".repeat(65))).toBe(false);
  });
});
