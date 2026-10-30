import "server-only";

import challengesMarkdown from "@/content/challenges.generated";
import faqMarkdown from "@/content/faq.generated";

import { createSession } from "./adk";
import { parseChallenges } from "./challenges";
import { siteConfig } from "./config";
import { getLeaderboard, getLeaderboardSummary, getPlayerLevels } from "./leaderboard";
import { currentLevel, rankFor, totalXp } from "./progress";
import { getSkill, listSkills, removeSkill, saveSkill } from "./skills";
import {
  MAX_LEVEL,
  MAX_SKILL_BODY,
  MAX_SKILL_DESCRIPTION,
  MAX_SKILLS,
  challengesText,
  describeSkill,
  expandSkill,
  faqText,
  helpText,
  leaderboardText,
  parseSkillFile,
  skillNameError,
  type SlashCommand,
} from "./slash";

/**
 * Run a slash command for a verified player. Either it is answered here
 * (reply, never reaches the agent), becomes a prompt for the agent, or
 * switches the player to a new ADK session.
 */
export type CommandResult =
  | { kind: "reply"; text: string }
  | { kind: "prompt"; text: string }
  | { kind: "new-session"; sessionId: string; text: string };

const MAX_SKILL_FILE_BYTES = 64 * 1024;

const reply = (text: string): CommandResult => ({ kind: "reply", text });
const prompt = (text: string): CommandResult => ({ kind: "prompt", text });

const challenges = parseChallenges(challengesMarkdown);

/** Commands that only read public content, so they work before registering. */
export const PUBLIC_COMMANDS = new Set(["challenges", "faq", "discord"]);

/** Answer one of PUBLIC_COMMANDS. */
export function runPublicCommand(command: SlashCommand): CommandResult {
  const { name, args } = command;
  switch (name) {
    case "challenges": {
      if (!args) {
        return reply(challengesText(challenges));
      }
      return /^\d{1,2}$/.test(args)
        ? reply(challengesText(challenges, Number(args)))
        : reply(`Usage: \`/challenges [0-${MAX_LEVEL}]\``);
    }
    case "faq":
      return reply(faqText(faqMarkdown));
    case "discord":
      return reply(`Join the conversation on [Discord](${siteConfig.discordUrl()}).`);
  }
  throw new Error(`/${name} is not a public command`);
}

export async function runCommand(
  player: { username: string; sessionId: string },
  command: SlashCommand,
  file?: File,
): Promise<CommandResult> {
  const { username } = player;
  const { name, args } = command;
  if (PUBLIC_COMMANDS.has(name)) {
    return runPublicCommand(command);
  }
  switch (name) {
    case "help":
      return reply(helpText(await listSkills(username)));
    case "newsession": {
      // The old session stays in ADK; only the cookie moves on.
      const sessionId = crypto.randomUUID();
      await createSession(username, sessionId);
      return {
        kind: "new-session",
        sessionId,
        text: "Started a new session. The agent has forgotten this conversation, but your leaderboard progress is kept.",
      };
    }
    case "level": {
      const level = /^\d{1,2}$/.test(args) ? Number(args) : NaN;
      if (!(level >= 0 && level <= MAX_LEVEL)) {
        return reply(`Usage: \`/level <0-${MAX_LEVEL}>\``);
      }
      // Matches the coordinator's deterministic level router (level_router.py).
      return prompt(`level ${level}`);
    }
    case "hint":
      return prompt(args ? `Give me a hint for the current level: ${args}` : "Give me a hint for the current level.");
    case "submit":
      return args ? prompt(`submit answer: ${args}`) : reply("Usage: `/submit <answer>`");
    case "leaderboard": {
      const [rows, summary] = await Promise.all([getLeaderboard(10), getLeaderboardSummary()]);
      return reply(leaderboardText(rows, summary));
    }
    case "whoami":
      return reply(await whoamiText(player));
    case "start":
      return prompt("level 0");
    case "continue": {
      const next = currentLevel(await getPlayerLevels(username));
      // Same routing as /level, so the coordinator switches deterministically.
      return next === null ? reply("You've cleared every level. Nothing left to pwn!") : prompt(`level ${next}`);
    }
    case "skills":
      return runSkillsCommand(username, args, file);
  }

  const skill = await getSkill(username, name);
  if (!skill) {
    return reply(`Unknown command \`/${name}\`. Type \`/help\` to see commands and your skills.`);
  }
  return prompt(expandSkill(skill, args));
}

async function whoamiText({ username, sessionId }: { username: string; sessionId: string }): Promise<string> {
  const levels = await getPlayerLevels(username);
  const next = currentLevel(levels);
  const xp = totalXp(levels);
  return [
    `You are **${username.replace(/_/g, "\\_")}**.`,
    "",
    `- Session ID: \`${sessionId}\` (your Quicket code at the event)`,
    `- On the leaderboard at levels: ${levels.length > 0 ? levels.join(", ") : "none yet"}`,
    `- Rank: ${rankFor(xp).title} (${xp} XP)`,
    next !== null ? `- Next up: \`/level ${next}\`` : "- You've completed every level!",
  ].join("\n");
}

async function runSkillsCommand(username: string, args: string, file?: File): Promise<CommandResult> {
  const [action = "list", ...rest] = args.split(/\s+/).filter(Boolean);
  const name = (rest[0] ?? "").toLowerCase();

  switch (action.toLowerCase()) {
    case "list": {
      const skills = await listSkills(username);
      if (skills.length === 0) {
        return reply("You have no skills installed. Type `/help` to see how to install one.");
      }
      return reply(
        [
          `**Your skills** (${skills.length}/${MAX_SKILLS})`,
          "",
          ...skills.map((skill) => `- \`/${skill.name}\`${skill.description ? ` - ${skill.description}` : ""}`),
        ].join("\n"),
      );
    }
    case "show": {
      const skill = name ? await getSkill(username, name) : null;
      if (!skill) {
        return reply(name ? `No skill named \`${name}\`.` : "Usage: `/skills show <name>`");
      }
      return reply(`**/${skill.name}**${skill.description ? ` - ${skill.description}` : ""}\n\n\`\`\`md\n${skill.body}\n\`\`\``);
    }
    case "remove":
    case "uninstall": {
      if (!name) {
        return reply("Usage: `/skills remove <name>`");
      }
      return reply(
        (await removeSkill(username, name)) ? `Removed \`/${name}\`.` : `No skill named \`${name}\`.`,
      );
    }
    case "install":
    case "add":
      return installSkill(username, args.replace(/^\S+\s*/, ""), file);
    default:
      return reply("Usage: `/skills [list | show <name> | install <name> <instructions> | remove <name>]`");
  }
}

/** `/skills install <name> <instructions>`, or a SKILL.md attachment. */
async function installSkill(username: string, args: string, file?: File): Promise<CommandResult> {
  const [argName = "", ...words] = args.split(/\s+/).filter(Boolean);
  let name = argName.toLowerCase();
  let description: string | undefined;
  let body: string;

  if (file) {
    if (!isTextFile(file)) {
      return reply("Attach the skill as a Markdown or text file (e.g. `SKILL.md`).");
    }
    if (file.size > MAX_SKILL_FILE_BYTES) {
      return reply("Skill files must be 64 KB or smaller.");
    }
    const parsed = parseSkillFile(await file.text());
    // A typed name wins, then the frontmatter, then the file name (unless it's just "SKILL.md").
    const stem = file.name.replace(/\.(md|markdown|txt)$/i, "");
    name = (name || parsed.name || (stem.toLowerCase() === "skill" ? "" : stem)).toLowerCase();
    description = parsed.description;
    body = parsed.body;
  } else {
    body = args.slice(args.indexOf(argName) + argName.length).trim();
    if (!name || words.length === 0) {
      return reply(
        "Usage: `/skills install <name> <instructions>`, or attach a `SKILL.md` and send `/skills install`.",
      );
    }
  }

  const nameError = name ? skillNameError(name) : "Give the skill a name in its frontmatter or the command.";
  if (nameError) {
    return reply(nameError);
  }
  if (!body) {
    return reply("The skill has no instructions.");
  }
  if (body.length > MAX_SKILL_BODY) {
    return reply(`Skill instructions must be ${MAX_SKILL_BODY} characters or fewer.`);
  }
  description = (description ?? describeSkill(body)).slice(0, MAX_SKILL_DESCRIPTION);

  const existed = (await getSkill(username, name)) !== null;
  if (!(await saveSkill(username, { name, description, body }))) {
    return reply(`You can install up to ${MAX_SKILLS} skills. Remove one with \`/skills remove <name>\` first.`);
  }
  return reply(`${existed ? "Updated" : "Installed"} \`/${name}\`. Run it with \`/${name} [request]\`.`);
}

function isTextFile(file: File): boolean {
  return file.type.startsWith("text/") || /\.(md|markdown|txt)$/i.test(file.name);
}
