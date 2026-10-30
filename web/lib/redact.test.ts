import { afterEach, describe, expect, it, vi } from "vitest";

import { redactPasswords } from "./redact";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("redactPasswords", () => {
  it("redacts every level's password by default", () => {
    vi.stubEnv("PASSWORD_ONE", "hunter2");
    expect(redactPasswords("PASS_ZERO and hunter2, hunter2!")).toBe("[REDACTED] and [REDACTED], [REDACTED]!");
  });

  it("only redacts the given level's password", () => {
    expect(redactPasswords("PASS_ONE PASS_TWO", 2)).toBe("PASS_ONE [REDACTED]");
  });

  it("leaves empty and password-free text alone", () => {
    expect(redactPasswords("")).toBe("");
    expect(redactPasswords("nothing here")).toBe("nothing here");
    expect(redactPasswords("PASS_ONE", 99)).toBe("PASS_ONE");
  });
});
