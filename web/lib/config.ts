import "server-only";

import { platformDatabaseUrl } from "@/lib/platform";

/**
 * Runtime configuration, read from the environment.
 *
 * Mirrors ctf/app_config.py so the web app and the Python agent agree on
 * level passwords (needed here to redact password_search_func output) and
 * on the ADK API location.
 */

const PASSWORD_ENV_NAMES = [
  "PASSWORD_ZERO",
  "PASSWORD_ONE",
  "PASSWORD_TWO",
  "PASSWORD_THREE",
  "PASSWORD_FOUR",
  "PASSWORD_FIVE",
  "PASSWORD_SIX",
  "PASSWORD_SEVEN",
  "PASSWORD_EIGHT",
  "PASSWORD_NINE",
  "PASSWORD_TEN",
] as const;

/** Highest level number; levels run 0..FINAL_LEVEL inclusive. */
export const FINAL_LEVEL = 10;

/** ADK app that contains every level agent (ctf/agents/sub_agents). */
export const ADK_APP_NAME = "sub_agents";

function env(name: string): string | undefined {
  const value = process.env[name];
  return value === undefined || value === "" ? undefined : value;
}

export function adkApiUrl(): string {
  return (env("ADK_API_URL") ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
}

/** Timeout for an agent /run call; local Ollama models can be slow. */
export function adkRunTimeoutMs(): number {
  const value = Number(env("ADK_RUN_TIMEOUT_MS"));
  return Number.isFinite(value) && value > 0 ? value : 180_000;
}

/** Level passwords keyed by level, defaulting like app_config.py (PASS_ZERO, ...). */
export function levelPasswords(): Record<number, string> {
  const passwords: Record<number, string> = {};
  PASSWORD_ENV_NAMES.forEach((name, level) => {
    passwords[level] = env(name) ?? `PASS_${name.slice("PASSWORD_".length)}`;
  });
  return passwords;
}

export const siteConfig = {
  name: () => env("CTF_NAME") ?? "BSIDES CTF Prompt Injection challenge",
  subtitle: () => env("CTF_SUBTITLE") ?? "Agentic LLM CTF",
  discordUrl: () =>
    env("DISCORD_URL") ??
    "https://discord.com/channels/687602309395382282/1168515417514442834",
};

/**
 * Leaderboard database location: the platform's (Cloudflare Hyperdrive) or
 * POSTGRES_DB_URI for Postgres (the historical POSTGRESS_DB_URI spelling is
 * still honoured, as in ctf/leaderboard.py), otherwise the SQLite file the
 * Python agent uses.
 */
export function databaseUrl(): string | undefined {
  return platformDatabaseUrl() ?? env("POSTGRES_DB_URI") ?? env("POSTGRESS_DB_URI");
}

export function sqlitePath(): string {
  return env("LEADERBOARD_DB_PATH") ?? "../ctf/leaderboard.db";
}
