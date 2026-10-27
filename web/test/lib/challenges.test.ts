import { describe, expect, it } from "vitest";

import challengesMarkdown from "@/content/challenges.generated";
import { parseChallenges } from "@/lib/challenges";
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
