import "server-only";

import { getDb, timestampParam } from "./db";
import { MAX_SKILLS, type Skill } from "./slash";

/** Per-player skills, installed and run with slash commands in the chat. */

export async function listSkills(username: string): Promise<Skill[]> {
  const db = await getDb();
  return db.query<Skill>(
    "SELECT name, description, body FROM player_skills WHERE username = $1 ORDER BY name",
    [username],
  );
}

export async function getSkill(username: string, name: string): Promise<Skill | null> {
  const db = await getDb();
  const rows = await db.query<Skill>(
    "SELECT name, description, body FROM player_skills WHERE username = $1 AND name = $2",
    [username, name],
  );
  return rows[0] ?? null;
}

/**
 * Install or replace a skill. Returns false when the player already has
 * MAX_SKILLS and this would be a new one.
 */
export async function saveSkill(username: string, skill: Skill): Promise<boolean> {
  const db = await getDb();
  if (!(await getSkill(username, skill.name))) {
    const [{ count }] = await db.query<{ count: number | string }>(
      "SELECT COUNT(*) AS count FROM player_skills WHERE username = $1",
      [username],
    );
    if (Number(count) >= MAX_SKILLS) {
      return false;
    }
  }
  await db.query(
    `INSERT INTO player_skills (username, name, description, body, updated_at)
     VALUES ($1, $2, $3, $4, $5)
     ON CONFLICT (username, name) DO UPDATE
     SET description = excluded.description, body = excluded.body, updated_at = excluded.updated_at`,
    [username, skill.name, skill.description, skill.body, timestampParam(db, new Date())],
  );
  return true;
}

export async function removeSkill(username: string, name: string): Promise<boolean> {
  const db = await getDb();
  const rows = await db.query(
    "DELETE FROM player_skills WHERE username = $1 AND name = $2 RETURNING name",
    [username, name],
  );
  return rows.length > 0;
}
