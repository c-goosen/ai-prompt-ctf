import "server-only";

import { getDb, timestampParam, toDate } from "./db";

/**
 * Leaderboard reads (and the registration-time level 0 entry), ported from
 * ctf/leaderboard.py. Level completions themselves are written by the
 * Python agent's submit_answer_func, never from model text.
 */

export interface LeaderboardRow {
  username: string;
  levelsCompleted: number;
  highestLevel: number;
  lastCompletedAt: string | null;
  firstCompletedAt: string | null;
}

export interface RecentCompletion {
  username: string;
  level: number;
  completedAt: string | null;
}

export interface LeaderboardSummary {
  players: number;
  totalCompletions: number;
}

const iso = (value: unknown) => toDate(value)?.toISOString() ?? null;

export async function getLeaderboard(limit = 25): Promise<LeaderboardRow[]> {
  const db = await getDb();
  const rows = await db.query<{
    username: string;
    levels_completed: number | string;
    highest_level: number;
    last_completed_at: unknown;
    first_completed_at: unknown;
  }>(
    `SELECT username,
            COUNT(*) AS levels_completed,
            MAX(level) AS highest_level,
            MAX(completed_at) AS last_completed_at,
            MIN(completed_at) AS first_completed_at
       FROM leaderboard_entries
      GROUP BY username
      ORDER BY MAX(level) DESC, MIN(completed_at) ASC
      LIMIT $1`,
    [limit],
  );
  return rows.map((row) => ({
    username: row.username,
    levelsCompleted: Number(row.levels_completed),
    highestLevel: Number(row.highest_level),
    lastCompletedAt: iso(row.last_completed_at),
    firstCompletedAt: iso(row.first_completed_at),
  }));
}

export async function getRecentCompletions(limit = 10): Promise<RecentCompletion[]> {
  const db = await getDb();
  const rows = await db.query<{ username: string; level: number; completed_at: unknown }>(
    `SELECT username, level, completed_at
       FROM leaderboard_entries
      ORDER BY completed_at DESC
      LIMIT $1`,
    [limit],
  );
  return rows.map((row) => ({
    username: row.username,
    level: Number(row.level),
    completedAt: iso(row.completed_at),
  }));
}

export async function getLeaderboardSummary(): Promise<LeaderboardSummary> {
  const db = await getDb();
  const rows = await db.query<{ players: number | string; total_completions: number | string }>(
    `SELECT COUNT(DISTINCT username) AS players, COUNT(*) AS total_completions
       FROM leaderboard_entries`,
  );
  return {
    players: Number(rows[0]?.players ?? 0),
    totalCompletions: Number(rows[0]?.total_completions ?? 0),
  };
}

/** The levels a player has on the board, lowest first. */
export async function getPlayerLevels(username: string): Promise<number[]> {
  const db = await getDb();
  const rows = await db.query<{ level: number }>(
    "SELECT level FROM leaderboard_entries WHERE username = $1 ORDER BY level",
    [username],
  );
  return rows.map((row) => Number(row.level));
}

/** Registration puts the player on the board at level 0 (as before). */
export async function ensureLeaderboardUser(username: string): Promise<void> {
  if (!username) {
    return;
  }
  const db = await getDb();
  await db.query(
    `INSERT INTO leaderboard_entries (username, level, completed_at)
     VALUES ($1, 0, $2)
     ON CONFLICT (username, level) DO NOTHING`,
    [username, timestampParam(db, new Date())],
  );
}

/**
 * Test-only mirror of the agent's record_level_completion (first completion
 * time wins). Production completions are recorded by the Python agent.
 */
export async function recordLevelCompletionForTesting(
  username: string,
  level: number,
  at = new Date(),
): Promise<void> {
  const db = await getDb();
  await db.query(
    `INSERT INTO leaderboard_entries (username, level, completed_at)
     VALUES ($1, $2, $3)
     ON CONFLICT (username, level) DO NOTHING`,
    [username, level, timestampParam(db, at)],
  );
}
