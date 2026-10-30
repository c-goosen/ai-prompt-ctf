import { Crown, Flag, Medal, Swords, Trophy, Users, Zap } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { PageShell } from "@/components/page-shell";
import { ShimmerButton } from "@/components/watermelon/shimmer-button";
import { FINAL_LEVEL } from "@/lib/config";
import { getLeaderboard, getLeaderboardSummary, getRecentCompletions } from "@/lib/leaderboard";
import { currentPlayer } from "@/lib/session";
import { cn } from "@/lib/utils";

import { AutoRefresh } from "./auto-refresh";

export const dynamic = "force-dynamic";
export const metadata = { title: "Leaderboard · PwnGPT" };

const TOTAL_LEVELS = FINAL_LEVEL + 1;
const formatTime = (iso: string) => iso.replace("T", " ").replace(/\.\d+Z$/, " UTC");

function formatRelative(iso: string, now: number) {
  const seconds = Math.max(0, Math.round((now - Date.parse(iso)) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function When({ iso, now, className }: { iso: string | null; now: number; className?: string }) {
  if (!iso) return <span className={className}>—</span>;
  return (
    <time dateTime={iso} title={formatTime(iso)} className={className}>
      {formatRelative(iso, now)}
    </time>
  );
}

function Stat({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-neon-teal/25 bg-card/60 p-3 sm:p-4">
      <span className="hidden size-10 shrink-0 items-center justify-center rounded-lg bg-neon-teal/10 text-neon-teal ring-1 ring-neon-teal/30 sm:flex">
        {icon}
      </span>
      <div className="min-w-0">
        <div className="text-2xl font-bold text-white tabular-nums sm:text-3xl">{value}</div>
        <div className="truncate text-xs text-muted-foreground sm:text-sm">{label}</div>
      </div>
    </div>
  );
}

const RANK_STYLES = [
  { ring: "bg-amber-400/15 text-amber-300 ring-amber-400/50", icon: <Crown className="size-4" aria-hidden="true" /> },
  { ring: "bg-slate-300/15 text-slate-200 ring-slate-300/50", icon: <Medal className="size-4" aria-hidden="true" /> },
  { ring: "bg-orange-500/15 text-orange-300 ring-orange-500/50", icon: <Medal className="size-4" aria-hidden="true" /> },
];

function Rank({ rank }: { rank: number }) {
  const style = RANK_STYLES[rank - 1];
  return (
    <span
      className={cn(
        "flex size-8 items-center justify-center rounded-full text-sm font-semibold tabular-nums ring-1",
        style ? style.ring : "text-muted-foreground ring-neon-teal/20",
      )}
      aria-label={`Rank ${rank}`}
    >
      {style ? style.icon : rank}
    </span>
  );
}

function Progress({ completed }: { completed: number }) {
  const percent = Math.round((completed / TOTAL_LEVELS) * 100);
  return (
    <div className="flex items-center gap-2.5">
      <div
        role="progressbar"
        aria-valuenow={completed}
        aria-valuemin={0}
        aria-valuemax={TOTAL_LEVELS}
        aria-label="Levels completed"
        className="h-2 w-20 overflow-hidden rounded-full bg-background/80 ring-1 ring-neon-teal/20 sm:w-28"
      >
        <div className="h-full rounded-full bg-gradient-to-r from-neon-violet via-neon-pink to-neon-teal" style={{ width: `${percent}%` }} />
      </div>
      <span className="text-xs text-muted-foreground tabular-nums">
        {completed}/{TOTAL_LEVELS}
      </span>
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
    return { rows, recent, summary, now: Date.now() };
  } catch (error) {
    console.error("Failed to load leaderboard:", (error as Error).message);
    return null;
  }
}

export default async function LeaderboardPage() {
  const [data, player] = await Promise.all([loadLeaderboard(), currentPlayer()]);
  if (!data) {
    return (
      <PageShell title="Live Leaderboard">
        <div role="alert" className="rounded-xl border border-destructive/50 bg-destructive/10 px-4 py-3 text-card-foreground">
          The leaderboard is temporarily unavailable. Please try again shortly.
        </div>
      </PageShell>
    );
  }
  const { rows, recent, summary, now } = data;
  const playerRank = player ? rows.findIndex((row) => row.username === player.username) + 1 : 0;

  return (
    <PageShell
      title="Live Leaderboard"
      description={
        <span className="flex items-center gap-2">
          <span className="relative flex size-2" aria-hidden="true">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-neon-teal opacity-75 motion-reduce:hidden" />
            <span className="relative inline-flex size-2 rounded-full bg-neon-teal" />
          </span>
          Ranked by highest level reached, then by who got there first. Updates every 30 seconds.
        </span>
      }
    >
      <AutoRefresh />
      <div className="grid grid-cols-3 gap-2 sm:gap-3">
        <Stat icon={<Users className="size-5" />} label="Competitors" value={summary.players} />
        <Stat icon={<Zap className="size-5" />} label="Levels cleared" value={summary.totalCompletions} />
        <Stat icon={<Flag className="size-5" />} label="Levels available" value={TOTAL_LEVELS} />
      </div>

      {player ? (
        playerRank > 0 && (
          <p className="flex items-center gap-2 rounded-xl border border-neon-pink/30 bg-neon-pink/10 px-4 py-2.5 text-sm text-card-foreground">
            <Trophy className="size-4 shrink-0 text-neon-pink" aria-hidden="true" />
            You&apos;re ranked <strong className="text-white">#{playerRank}</strong> as{" "}
            <strong className="truncate text-white">{player.username}</strong>.
          </p>
        )
      ) : (
        <div className="flex flex-col gap-3 rounded-xl border border-neon-teal/30 bg-neon-teal/5 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-card-foreground">Want your name up here? Register and start cracking levels.</p>
          <ShimmerButton asChild className="px-4 py-2 text-sm">
            <Link href="/register">Join the game</Link>
          </ShimmerButton>
        </div>
      )}

      {rows.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-neon-teal/40 px-4 py-10 text-center">
          <Swords className="size-8 text-neon-teal" aria-hidden="true" />
          <p className="font-medium text-white">No entries yet</p>
          <p className="text-sm text-muted-foreground">Be the first to crack a level!</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-neon-teal/30 bg-card/40">
          <table className="w-full border-collapse text-left text-sm text-white">
            <caption className="sr-only">Top {rows.length} players</caption>
            <thead className="bg-background/60 text-xs tracking-wide text-muted-foreground uppercase">
              <tr>
                <th scope="col" className="w-14 px-3 py-3 font-medium">Rank</th>
                <th scope="col" className="px-3 py-3 font-medium">Player</th>
                <th scope="col" className="px-3 py-3 font-medium">Progress</th>
                <th scope="col" className="hidden px-3 py-3 font-medium sm:table-cell">Highest</th>
                <th scope="col" className="hidden px-3 py-3 text-right font-medium md:table-cell">Last solve</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => {
                const isYou = player?.username === row.username;
                return (
                  <tr
                    key={row.username}
                    aria-current={isYou ? "true" : undefined}
                    className={cn(
                      "border-t border-neon-teal/15 transition-colors hover:bg-neon-teal/5",
                      index === 0 && "bg-amber-400/5",
                      isYou && "bg-neon-pink/10 hover:bg-neon-pink/15",
                    )}
                  >
                    <td className="px-3 py-3">
                      <Rank rank={index + 1} />
                    </td>
                    <td className="max-w-40 px-3 py-3 sm:max-w-56">
                      <div className="flex items-center gap-2">
                        <span className={cn("truncate", index < 3 && "font-semibold")} title={row.username}>
                          {row.username}
                        </span>
                        {isYou && (
                          <span className="shrink-0 rounded-full bg-neon-pink/20 px-2 py-0.5 text-[10px] font-semibold text-neon-pink uppercase">
                            You
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <Progress completed={row.levelsCompleted} />
                    </td>
                    <td className="hidden px-3 py-3 sm:table-cell">
                      <span className="rounded-md bg-primary/25 px-2 py-0.5 text-xs font-semibold text-white tabular-nums ring-1 ring-primary/50">
                        Lvl {row.highestLevel}
                      </span>
                    </td>
                    <td className="hidden px-3 py-3 text-right whitespace-nowrap text-muted-foreground md:table-cell">
                      <When iso={row.lastCompletedAt} now={now} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <section aria-labelledby="recent" className="flex flex-col gap-3">
        <h2 id="recent" className="text-lg font-semibold text-white">
          Recent completions
        </h2>
        {recent.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent completions.</p>
        ) : (
          <ol className="flex flex-col divide-y divide-neon-teal/10 rounded-xl border border-neon-teal/20 bg-card/40">
            {recent.map((entry) => (
              <li key={`${entry.username}-${entry.level}`} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                <span className="w-14 shrink-0 rounded-full bg-primary px-2 py-0.5 text-center text-xs font-semibold text-primary-foreground tabular-nums">
                  Lvl {entry.level}
                </span>
                <span className="min-w-0 flex-1 truncate">
                  <strong className="text-white">{entry.username}</strong>{" "}
                  <span className="text-muted-foreground">{entry.level === 0 ? "joined the game" : "cracked the level"}</span>
                </span>
                <When iso={entry.completedAt} now={now} className="shrink-0 text-xs text-muted-foreground" />
              </li>
            ))}
          </ol>
        )}
      </section>
    </PageShell>
  );
}
