import { afterEach, describe, expect, it, vi } from "vitest";

import { FINAL_LEVEL, adkApiUrl, adkRunMaxMs, adkRunTimeoutMs, levelPasswords } from "./config";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("config", () => {
  it("defaults and trims the ADK API URL", () => {
    vi.stubEnv("ADK_API_URL", "");
    expect(adkApiUrl()).toBe("http://127.0.0.1:8000");
    vi.stubEnv("ADK_API_URL", "http://adk:8000//");
    expect(adkApiUrl()).toBe("http://adk:8000");
  });

  it("falls back to the default run timeouts for invalid values", () => {
    for (const value of ["", "abc", "0", "-5"]) {
      vi.stubEnv("ADK_RUN_TIMEOUT_MS", value);
      vi.stubEnv("ADK_RUN_MAX_MS", value);
      expect(adkRunTimeoutMs()).toBe(180_000);
      expect(adkRunMaxMs()).toBe(600_000);
    }
    vi.stubEnv("ADK_RUN_TIMEOUT_MS", "1500");
    expect(adkRunTimeoutMs()).toBe(1500);
  });

  it("defaults level passwords like app_config.py", () => {
    vi.stubEnv("PASSWORD_ZERO", "");
    vi.stubEnv("PASSWORD_TEN", "s3cret");
    const passwords = levelPasswords();
    expect(Object.keys(passwords)).toHaveLength(FINAL_LEVEL + 1);
    expect(passwords[0]).toBe("PASS_ZERO");
    expect(passwords[5]).toBe("PASS_FIVE");
    expect(passwords[10]).toBe("s3cret");
  });
});
