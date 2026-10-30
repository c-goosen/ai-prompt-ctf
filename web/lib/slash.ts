/**
 * Slash commands typed into the chat ("/help", "/level 3", "/my-skill args").
 * Pure parsing and formatting, shared by the chat route and the input's
 * autocomplete, so it is unit tested directly.
 */

import type { Challenge } from "./challenges";
import type { LeaderboardRow, LeaderboardSummary } from "./leaderboard";

export interface SlashCommand {
  /** Lower-cased name without the slash. */
  name: string;
  args: string;
}

export interface CommandInfo {
  name: string;
  usage: string;
  description: string;
}

/** A player-installed skill: named instructions expanded into the prompt. */
export interface Skill {
  name: string;
  description: string;
  body: string;
}

export const MAX_LEVEL = 10;
export const MAX_SKILLS = 20;
export const MAX_SKILL_BODY = 8_000;
export const MAX_SKILL_DESCRIPTION = 200;

export const BUILTIN_COMMANDS: CommandInfo[] = [
  { name: "help", usage: "/help", description: "Show commands and your installed skills" },
  {
    name: "register",
    usage: "/register <username> [session-id]",
    description: "Register (or switch to) a username, like the register page",
  },
  { name: "level", usage: `/level <0-${MAX_LEVEL}>`, description: "Switch to a challenge level" },
  { name: "start", usage: "/start", description: "Go to level 0, the warm-up" },
  { name: "continue", usage: "/continue", description: "Jump to your lowest unfinished level" },
  { name: "newsession", usage: "/newsession", description: "Start a fresh conversation (keeps your progress)" },
  { name: "hint", usage: "/hint", description: "Ask for a hint for the current level" },
  { name: "submit", usage: "/submit <answer>", description: "Submit a flag or password" },
  { name: "leaderboard", usage: "/leaderboard", description: "Show the top players" },
  { name: "whoami", usage: "/whoami", description: "Show your username, session ID and progress" },
  {
    name: "challenges",
    usage: "/challenges [level]",
    description: "List the challenges, or show one level's briefing",
  },
  { name: "faq", usage: "/faq", description: "Show the FAQ topics" },
  { name: "discord", usage: "/discord", description: "Get the Discord link" },
  { name: "skills", usage: "/skills", description: "List your installed skills" },
  {
    name: "skills install",
    usage: "/skills install <name> <instructions>",
    description: "Install a skill (or attach a SKILL.md and send /skills install)",
  },
  { name: "skills show", usage: "/skills show <name>", description: "Show a skill's instructions" },
  { name: "skills remove", usage: "/skills remove <name>", description: "Uninstall a skill" },
];

const BUILTIN_NAMES = new Set(BUILTIN_COMMANDS.map((command) => command.name.split(" ")[0]));

// "/etc/passwd" doesn't match (the name must end at whitespace), so paths
// and other slash-led text still go to the agent as a normal message.
const COMMAND_PATTERN = /^\/([a-z][a-z0-9-]*)(?:\s+([\s\S]*))?$/i;
const SKILL_NAME_PATTERN = /^[a-z][a-z0-9-]{0,31}$/;

export function parseSlashCommand(text: string): SlashCommand | null {
  const match = COMMAND_PATTERN.exec(text.trim());
  return match ? { name: match[1].toLowerCase(), args: (match[2] ?? "").trim() } : null;
}

export function isBuiltinCommand(name: string): boolean {
  return BUILTIN_NAMES.has(name);
}

/** Why a skill name can't be used, or null if it can. */
export function skillNameError(name: string): string | null {
  if (!SKILL_NAME_PATTERN.test(name)) {
    return "Skill names are 1-32 characters: lowercase letters, digits or '-', starting with a letter.";
  }
  if (isBuiltinCommand(name)) {
    return `\`/${name}\` is a built-in command, so pick another name.`;
  }
  return null;
}

/**
 * Parse a SKILL.md: optional `---` frontmatter with `name:` and
 * `description:`, then the instructions.
 */
export function parseSkillFile(text: string): { name?: string; description?: string; body: string } {
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/.exec(text.trim());
  if (!match) {
    return { body: text.trim() };
  }
  const fields: Record<string, string> = {};
  for (const line of match[1].split(/\r?\n/)) {
    const field = /^([A-Za-z_-]+)\s*:\s*(.*)$/.exec(line);
    if (field) {
      fields[field[1].toLowerCase()] = field[2].trim().replace(/^(["'])(.*)\1$/, "$2");
    }
  }
  return { name: fields.name || undefined, description: fields.description || undefined, body: match[2].trim() };
}

/** The first line of the instructions, as a description when none is given. */
export function describeSkill(body: string): string {
  const firstLine = body.split("\n").find((line) => line.trim() !== "") ?? "";
  const description = firstLine.replace(/^#+\s*/, "").trim();
  return description.length > MAX_SKILL_DESCRIPTION
    ? `${description.slice(0, MAX_SKILL_DESCRIPTION - 1)}…`
    : description;
}

const COMMAND_MARKER = /^<!--COMMAND:([^>]*?)-->\n?/;

/**
 * The prompt sent to the agent for `/<skill> args`. `$ARGUMENTS` in the
 * instructions is replaced by the args; otherwise they follow the skill.
 * The leading marker lets history show the command instead of the expansion.
 */
export function expandSkill(skill: Skill, args: string): string {
  const command = args ? `/${skill.name} ${args}` : `/${skill.name}`;
  const usesArguments = skill.body.includes("$ARGUMENTS");
  const body = usesArguments ? skill.body.split("$ARGUMENTS").join(args) : skill.body;
  const lines = [
    `<!--COMMAND:${encodeURIComponent(command)}-->`,
    `Use the "${skill.name}" skill for this request. Follow its instructions:`,
    "",
    `<skill name="${skill.name}">`,
    body,
    "</skill>",
  ];
  if (args && !usesArguments) {
    lines.push("", args);
  }
  return lines.join("\n");
}

/** Show an expanded skill prompt as the command the player typed. */
export function collapseCommandMarker(text: string): string {
  const match = COMMAND_MARKER.exec(text);
  if (!match) {
    return text;
  }
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return text;
  }
}

/** Markdown for /help. */
export function helpText(skills: Array<Pick<Skill, "name" | "description">>): string {
  const commands = BUILTIN_COMMANDS.map(
    (command) => `| \`${command.usage}\` | ${command.description} |`,
  );
  const installed =
    skills.length > 0
      ? skills.map((skill) => `- \`/${skill.name}\`${skill.description ? ` - ${skill.description}` : ""}`)
      : ["_No skills installed yet._"];
  return [
    "**Commands**",
    "",
    "| Command | What it does |",
    "| --- | --- |",
    ...commands,
    "",
    "**Your skills**",
    "",
    ...installed,
    "",
    "**Skills** are reusable instructions you install once and run with `/<name> [request]`.",
    "Install one inline, e.g. `/skills install pirate Answer every request in pirate speak.`,",
    "or attach a `SKILL.md` file and send `/skills install`:",
    "",
    "```md",
    "---",
    "name: pirate",
    "description: Talk like a pirate",
    "---",
    "Answer this in pirate speak: $ARGUMENTS",
    "```",
    "",
    "`$ARGUMENTS` is replaced by whatever you type after the command.",
  ].join("\n");
}

/** Markdown for /challenges: every level, or one level's briefing. */
export function challengesText(challenges: Challenge[], level?: number): string {
  if (level === undefined) {
    return [
      "**Challenges**",
      "",
      "| Level | Title | OWASP |",
      "| --- | --- | --- |",
      ...challenges.map(
        (challenge) => `| ${challenge.level} | ${challenge.title} | ${challenge.owasp.join(", ") || "-"} |`,
      ),
      "",
      "Use `/challenges <level>` for a briefing and `/level <n>` to play one, or see [Challenges](/challenges).",
    ].join("\n");
  }
  const challenge = challenges.find((candidate) => candidate.level === level);
  if (!challenge) {
    return `No level ${level}. Usage: \`/challenges [0-${MAX_LEVEL}]\``;
  }
  return [
    `**Level ${challenge.level}: ${challenge.title}**`,
    ...(challenge.subtitle ? ["", `_${challenge.subtitle}_`] : []),
    ...(challenge.owasp.length > 0 ? ["", challenge.owasp.map((tag) => `\`${tag}\``).join(" ")] : []),
    ...(challenge.body ? ["", challenge.body] : []),
    "",
    `Type \`/level ${challenge.level}\` to start.`,
  ].join("\n");
}

/** Markdown for /leaderboard. */
export function leaderboardText(rows: LeaderboardRow[], summary: LeaderboardSummary): string {
  if (rows.length === 0) {
    return "No one is on the board yet. See [Leaderboard](/leaderboard).";
  }
  return [
    "**Leaderboard**",
    "",
    "| # | Player | Highest level | Levels done |",
    "| --- | --- | --- | --- |",
    // Usernames may contain "_", which markdown would read as emphasis.
    ...rows.map(
      (row, index) =>
        `| ${index + 1} | ${row.username.replace(/_/g, "\\_")} | ${row.highestLevel} | ${row.levelsCompleted} |`,
    ),
    "",
    `${summary.players} players, ${summary.totalCompletions} completions. Full board: [Leaderboard](/leaderboard).`,
  ].join("\n");
}

/** Markdown for /faq: the FAQ's section headings. */
export function faqText(markdown: string): string {
  const topics = markdown
    .split("\n")
    .filter((line) => line.startsWith("## "))
    .map((line) => `- ${line.slice(3).trim()}`);
  return ["**FAQ topics**", "", ...topics, "", "Read the answers on the [FAQ](/faq) page."].join("\n");
}

/** Built-in commands plus the player's skills, as autocomplete entries. */
export function allCommands(skills: Array<Pick<Skill, "name" | "description">>): CommandInfo[] {
  return [
    ...BUILTIN_COMMANDS,
    ...skills.map((skill) => ({ name: skill.name, usage: `/${skill.name} [request]`, description: skill.description })),
  ];
}

/** Commands whose name starts with what's typed after "/", while still typing the name. */
export function commandSuggestions(input: string, commands: CommandInfo[]): CommandInfo[] {
  if (!input.startsWith("/")) {
    return [];
  }
  const typed = input.slice(1).toLowerCase();
  return commands.filter((command) => command.name.startsWith(typed));
}

/** The input after picking a suggestion: the command, plus a space if it takes arguments. */
export function completeCommand(command: CommandInfo): string {
  return `/${command.name}${/[<[]/.test(command.usage) ? " " : ""}`;
}
