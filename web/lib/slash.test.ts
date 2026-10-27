import { describe, expect, it } from "vitest";

import {
  allCommands,
  collapseCommandMarker,
  commandSuggestions,
  completeCommand,
  expandSkill,
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
