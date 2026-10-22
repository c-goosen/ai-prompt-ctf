import { describe, expect, it } from "vitest";

import { useTestDb } from "@/test/helpers";

import {
  ensureLeaderboardUser,
  getLeaderboard,
  getLeaderboardSummary,
  getRecentCompletions,
  recordLevelCompletionForTesting,
} from "./leaderboard";

describe("leaderboard", () => {
  const { db } = useTestDb();

  it("orders by highest level, then earliest first completion", async () => {
    await recordLevelCompletionForTesting("bob", 1, new Date("2026-01-01T10:00:00Z"));
    await recordLevelCompletionForTesting("alice", 1, new Date("2026-01-01T09:00:00Z"));
    await recordLevelCompletionForTesting("alice", 2, new Date("2026-01-01T11:00:00Z"));
    await recordLevelCompletionForTesting("carol", 2, new Date("2026-01-01T12:00:00Z"));

    const rows = await getLeaderboard();
    expect(rows.map((row) => row.username)).toEqual(["alice", "carol", "bob"]);
    expect(rows[0]).toMatchObject({ levelsCompleted: 2, highestLevel: 2 });
    expect(await getLeaderboardSummary()).toEqual({ players: 3, totalCompletions: 4 });
    expect((await getRecentCompletions(1))[0]).toMatchObject({ username: "carol", level: 2 });
  });

  it("reads rows written by the Python agent (SQLAlchemy SQLite format)", async () => {
    await db().query(
      "INSERT INTO leaderboard_entries (username, level, completed_at) VALUES ($1, $2, $3)",
      ["agent-user", 3, "2026-10-21 12:00:00.123456"],
    );
    const [row] = await getLeaderboard();
    expect(row.firstCompletedAt).toBe("2026-10-21T12:00:00.123Z");
  });

  it("writes timestamps in the same format the agent uses", async () => {
    await ensureLeaderboardUser("dana");
    const [row] = await db().query<{ completed_at: string }>(
      "SELECT completed_at FROM leaderboard_entries WHERE username = $1",
      ["dana"],
    );
    expect(row.completed_at).toMatch(/^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{6}$/);
  });

  it("registration adds a single level 0 entry", async () => {
    await ensureLeaderboardUser("erin");
    await ensureLeaderboardUser("erin");
    expect(await getLeaderboardSummary()).toEqual({ players: 1, totalCompletions: 1 });
  });
});
