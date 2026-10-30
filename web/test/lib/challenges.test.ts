import { describe, expect, it } from "vitest";

import challengesMarkdown from "@/content/challenges.generated";
import { DIFFICULTY, difficulty, parseChallenges } from "@/lib/challenges";
import { FINAL_LEVEL } from "@/lib/config";

describe("parseChallenges", () => {
  it("splits levels and pulls out subtitle and OWASP tags", () => {
    const [level] = parseChallenges(
      "# Level 2: Output\n\n## Output Protection\nLLM02: Insecure Output Handling\nOWASP LLM06: Disclosure\n\nBody text.\n",
    );
    expect(level).toEqual({
      level: 2,
      title: "Output",
      subtitle: "Output Protection",
      owasp: ["LLM02: Insecure Output Handling", "LLM06: Disclosure"],
      body: "Body text.",
    });
  });

  it("parses every level in content/challenges.md", () => {
    const levels = parseChallenges(challengesMarkdown).map((challenge) => challenge.level);
    expect(levels).toEqual(Array.from({ length: FINAL_LEVEL + 1 }, (_, index) => index));
  });
});

describe("difficulty", () => {
  it("spreads levels evenly from Warm-up to Insane", () => {
    const tiers = Array.from({ length: FINAL_LEVEL + 1 }, (_, level) => difficulty(level, FINAL_LEVEL));
    expect(tiers).toEqual([1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]);
    expect(DIFFICULTY[tiers[FINAL_LEVEL] - 1]).toBe("Insane");
  });
});
