import { describe, expect, it } from "vitest";

import { currentLevel, maxXp, newlyCleared, rankFor, totalXp, xpFor } from "./progress";

describe("progress", () => {
  it("scores levels by difficulty, with Basecamp free and a boss bonus", () => {
    expect(xpFor(0)).toBe(0);
    expect(xpFor(1)).toBe(100);
    expect(xpFor(3)).toBe(100);
    expect(xpFor(4)).toBe(200);
    expect(xpFor(9)).toBe(300);
    expect(xpFor(10)).toBe(500);
    expect(xpFor(14)).toBe(800);
    expect(xpFor(15)).toBe(1500);
    expect(totalXp([0, 1, 1, 4])).toBe(300);
    expect(maxXp()).toBe(6400);
  });

  it("ranks by XP and names the next rank", () => {
    expect(rankFor(0)).toEqual({ title: "Script Kiddie", next: { title: "Prompt Wrangler", xp: 300 } });
    expect(rankFor(1000).title).toBe("Jailbreaker");
    expect(rankFor(maxXp())).toEqual({ title: "AGI Whisperer" });
  });

  it("puts the character at the lowest uncleared level", () => {
    expect(currentLevel([])).toBe(1);
    expect(currentLevel([0, 1, 2, 4])).toBe(3);
    expect(currentLevel([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])).toBe(15);
    expect(currentLevel(Array.from({ length: 16 }, (_, level) => level))).toBeNull();
  });

  it("finds newly cleared levels, ignoring Basecamp", () => {
    expect(newlyCleared([0, 1], [0, 1, 3, 2])).toEqual([2, 3]);
    expect(newlyCleared([], [0])).toEqual([]);
  });
});
