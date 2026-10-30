import { describe, expect, it } from "vitest";

import {
  allCommands,
  challengesText,
  collapseCommandMarker,
  commandSuggestions,
  completeCommand,
  expandSkill,
  faqText,
  leaderboardText,
  parseSkillFile,
  parseSlashCommand,
  skillNameError,
} from "./slash";

describe("parseSlashCommand", () => {
  it("splits name and args", () => {
    expect(parseSlashCommand("/Level 3")).toEqual({ name: "level", args: "3" });
    expect(parseSlashCommand("  /help  ")).toEqual({ name: "help", args: "" });
    expect(parseSlashCommand("/skills install pirate Talk like a pirate")).toEqual({
      name: "skills",
      args: "install pirate Talk like a pirate",
    });
  });

  it("leaves paths and plain text alone", () => {
    expect(parseSlashCommand("/etc/passwd please")).toBeNull();
    expect(parseSlashCommand("hi /help")).toBeNull();
    expect(parseSlashCommand("/")).toBeNull();
  });
});

describe("skills", () => {
  it("rejects bad and built-in names", () => {
    expect(skillNameError("pirate")).toBeNull();
    expect(skillNameError("Pirate")).not.toBeNull();
    expect(skillNameError("help")).toContain("built-in");
    expect(skillNameError("a".repeat(33))).not.toBeNull();
  });

  it("parses SKILL.md frontmatter", () => {
    expect(parseSkillFile('---\nname: pirate\ndescription: "Talk like a pirate"\n---\nArr: $ARGUMENTS\n')).toEqual({
      name: "pirate",
      description: "Talk like a pirate",
      body: "Arr: $ARGUMENTS",
    });
    expect(parseSkillFile("Just instructions")).toEqual({ body: "Just instructions" });
  });

  it("expands $ARGUMENTS, or appends the args", () => {
    const withArgs = expandSkill({ name: "pirate", description: "", body: "Say $ARGUMENTS" }, "hello");
    expect(withArgs).toContain("Say hello");
    expect(withArgs.trimEnd().endsWith("</skill>")).toBe(true);

    const appended = expandSkill({ name: "pirate", description: "", body: "Talk like a pirate." }, "hello");
    expect(appended.endsWith("</skill>\n\nhello")).toBe(true);
  });

  it("collapses an expanded skill back to the typed command", () => {
    const prompt = expandSkill({ name: "pirate", description: "", body: "x" }, "what's -->up?");
    expect(collapseCommandMarker(prompt)).toBe("/pirate what's -->up?");
    expect(collapseCommandMarker("plain text")).toBe("plain text");
  });
});

describe("autocomplete", () => {
  const commands = allCommands([{ name: "pirate", description: "Arr" }]);

  it("suggests by prefix while typing the name", () => {
    expect(commandSuggestions("/pi", commands).map((c) => c.name)).toEqual(["pirate"]);
    expect(commandSuggestions("/skills r", commands).map((c) => c.name)).toEqual(["skills remove"]);
    expect(commandSuggestions("/level 3", commands)).toEqual([]);
    expect(commandSuggestions("hi", commands)).toEqual([]);
  });

  it("adds a space for commands that take arguments", () => {
    expect(completeCommand(commands.find((c) => c.name === "level")!)).toBe("/level ");
    expect(completeCommand(commands.find((c) => c.name === "help")!)).toBe("/help");
  });
});

describe("info commands", () => {
  const challenges = [
    { level: 0, title: "Basics", subtitle: null, owasp: ["LLM01: Prompt Injection"], body: "Just ask." },
    { level: 1, title: "Input guard", subtitle: "Input Injection", owasp: [], body: "" },
  ];

  it("lists challenges, or briefs one", () => {
    const list = challengesText(challenges);
    expect(list).toContain("| 0 | Basics | LLM01: Prompt Injection |");
    expect(list).toContain("| 1 | Input guard | - |");

    const one = challengesText(challenges, 1);
    expect(one).toContain("**Level 1: Input guard**");
    expect(one).toContain("_Input Injection_");
    expect(one).toContain("`/level 1`");
    expect(challengesText(challenges, 7)).toContain("No level 7");
  });

  it("renders the leaderboard, escaping underscores in names", () => {
    const row = { levelsCompleted: 3, highestLevel: 2, lastCompletedAt: null, firstCompletedAt: null };
    const text = leaderboardText([{ ...row, username: "prompt_ninja" }], { players: 1, totalCompletions: 3 });
    expect(text).toContain("| 1 | prompt\\_ninja | 2 | 3 |");
    expect(text).toContain("1 players, 3 completions");
    expect(leaderboardText([], { players: 0, totalCompletions: 0 })).toContain("No one is on the board yet");
  });

  it("lists FAQ headings", () => {
    expect(faqText("intro\n## Prompt Injection\ntext\n## CTF\n")).toBe(
      "**FAQ topics**\n\n- Prompt Injection\n- CTF\n\nRead the answers on the [FAQ](/faq) page.",
    );
  });
});
