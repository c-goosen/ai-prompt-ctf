/**
 * Game rules for the quest map: XP per level, rank titles and where the
 * player's character stands. Pure, so the chat UI and server share it.
 *
 * Progress is the list of levels a player has on the leaderboard, which only
 * the agent's submit_answer_func writes (after checking the password).
 * Registering puts everyone on the board at level 0, so level 0 is
 * "Basecamp": always cleared, worth no XP, never celebrated.
 */

import { difficulty } from "./challenges";
import { MAX_LEVEL } from "./slash";

/** XP for a level by difficulty (Warm-up … Insane); the final level is the boss. */
const DIFFICULTY_XP = [100, 200, 300, 500, 800];
const BOSS_XP = 1500;

export function xpFor(level: number): number {
  if (level <= 0 || level > MAX_LEVEL) {
    return 0;
  }
  return level === MAX_LEVEL ? BOSS_XP : DIFFICULTY_XP[difficulty(level, MAX_LEVEL) - 1];
}

export function totalXp(levels: number[]): number {
  return [...new Set(levels)].reduce((sum, level) => sum + xpFor(level), 0);
}

export function maxXp(): number {
  let sum = 0;
  for (let level = 1; level <= MAX_LEVEL; level++) {
    sum += xpFor(level);
  }
  return sum;
}

export const RANKS: Array<{ title: string; xp: number }> = [
  { title: "Script Kiddie", xp: 0 },
  { title: "Prompt Wrangler", xp: 300 },
  { title: "Jailbreaker", xp: 1000 },
  { title: "Red Teamer", xp: 2200 },
  { title: "AGI Whisperer", xp: maxXp() },
];

export function rankFor(xp: number): { title: string; next?: { title: string; xp: number } } {
  let index = 0;
  while (index + 1 < RANKS.length && xp >= RANKS[index + 1].xp) {
    index++;
  }
  const next = RANKS[index + 1];
  return next ? { title: RANKS[index].title, next } : { title: RANKS[index].title };
}

/** The level the character stands at: the lowest uncleared one, or null when all are cleared. */
export function currentLevel(levels: number[]): number | null {
  for (let level = 1; level <= MAX_LEVEL; level++) {
    if (!levels.includes(level)) {
      return level;
    }
  }
  return null;
}

/** Levels cleared since `before` (Basecamp excluded), lowest first. */
export function newlyCleared(before: number[], after: number[]): number[] {
  return after.filter((level) => level > 0 && !before.includes(level)).sort((a, b) => a - b);
}
