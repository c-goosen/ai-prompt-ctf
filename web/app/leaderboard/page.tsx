import { Flag } from "lucide-react";

import { PageShell } from "@/components/page-shell";
import { FINAL_LEVEL } from "@/lib/config";
import { getLeaderboard, getLeaderboardSummary, getRecentCompletions } from "@/lib/leaderboard";

export const dynamic = "force-dynamic";
export const metadata = { title: "Leaderboard · PwnGPT" };

const TOTAL_LEVELS = FINAL_LEVEL + 1;
const formatTime = (iso: string | null) => (iso ? iso.replace("T", " ").replace(/\.\d+Z$/, " UTC") : "—");

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-neon-teal/30 bg-card/60 p-4">
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  );
}

async function loadLeaderboard() {
  try {
    const [rows, recent, summary] = await Promise.all([
      getLeaderboard(),
      getRecentCompletions(),
      getLeaderboardSummary(),
    ]);
    return { rows, recent, summary };
  } catch (error) {
    console.error("Failed to load leaderboard:", (error as Error).message);
    return null;
  }
}

export default async function LeaderboardPage() {
  const data = await loadLeaderboard();
  if (!data) {
    return (
      <PageShell title="Live Leaderboard">
        <div role="alert" className="rounded-xl border border-destructive/50 bg-destructive/10 px-4 py-3 text-card-foreground">
          The leaderboard is temporarily unavailable. Please try again shortly.
        </div>
      </PageShell>
    );
  }
  const { rows, recent, summary } = data;

  return (
    <PageShell title="Live Leaderboard" description="Progress updates land here as soon as a level is solved.">
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Competitors" value={summary.players} />
        <Stat label="Levels Cleared" value={summary.totalCompletions} />
        <Stat label="Levels Available" value={TOTAL_LEVELS} />
      </div>

      {rows.length === 0 ? (
        <div className="flex items-center gap-3 rounded-xl border border-neon-teal/40 bg-neon-teal/10 px-4 py-3 text-card-foreground">
          <Flag className="size-4 text-neon-teal" aria-hidden="true" />
          No entries yet — be the first to crack a level!
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-neon-teal/40">
          <table className="w-full border-collapse text-left text-sm text-white">
            <thead className="bg-background/60">
              <tr>
                {["#", "Player", "Levels Completed", "Highest Level", "Last Completion"].map((heading) => (
                  <th key={heading} scope="col" className="border-b border-neon-teal/40 px-3 py-3 font-semibold">
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={row.username} className="border-b border-neon-teal/20 last:border-0 hover:bg-neon-teal/10">
                  <td className="px-3 py-3">{index + 1}</td>
                  <td className="max-w-48 truncate px-3 py-3">{row.username}</td>
                  <td className="px-3 py-3">
                    {row.levelsCompleted}/{TOTAL_LEVELS}
                  </td>
                  <td className="px-3 py-3">Level {row.highestLevel}</td>
                  <td className="px-3 py-3 whitespace-nowrap">{formatTime(row.lastCompletedAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold text-white">Recent Completions</h2>
        {recent.length === 0 ? (
          <p className="text-muted-foreground">No recent completions.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {recent.map((entry) => (
              <li key={`${entry.username}-${entry.level}`} className="flex flex-wrap items-center gap-2 text-sm">
                <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-semibold text-primary-foreground">
                  Level {entry.level}
                </span>
                <strong className="text-white">{entry.username}</strong>
                <small className="text-muted-foreground">{formatTime(entry.completedAt)}</small>
              </li>
            ))}
          </ul>
        )}
      </section>
    </PageShell>
  );
}
