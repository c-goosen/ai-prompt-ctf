import { ArrowRight, ShieldAlert, Skull } from "lucide-react";
import Link from "next/link";

import { ChallengesMap } from "@/components/game/challenges-map";
import { Markdown } from "@/components/markdown";
import { PageShell } from "@/components/page-shell";
import { ShimmerButton } from "@/components/watermelon/shimmer-button";
import challengesMarkdown from "@/content/challenges.generated";
import { DIFFICULTY, difficulty, parseChallenges, type Challenge } from "@/lib/challenges";
import { FINAL_LEVEL, siteConfig } from "@/lib/config";
import { getPlayerLevels } from "@/lib/leaderboard";
import { currentPlayer } from "@/lib/session";
import { cn } from "@/lib/utils";

// Title comes from CTF_SUBTITLE at runtime, so don't prerender at build time.
export const dynamic = "force-dynamic";
export const metadata = { title: "Challenges · PwnGPT" };

const challenges = parseChallenges(challengesMarkdown);

function Difficulty({ level }: { level: number }) {
  const score = difficulty(level, FINAL_LEVEL);
  return (
    <div className="flex items-center gap-2" aria-label={`Difficulty: ${DIFFICULTY[score - 1]}`}>
      <div className="flex gap-0.5" aria-hidden="true">
        {DIFFICULTY.map((label, index) => (
          <span
            key={label}
            className={cn(
              "h-1.5 w-3 rounded-full",
              index < score ? (score >= 4 ? "bg-neon-pink" : "bg-neon-teal") : "bg-white/10",
            )}
          />
        ))}
      </div>
      <span className="text-xs text-muted-foreground" aria-hidden="true">
        {DIFFICULTY[score - 1]}
      </span>
    </div>
  );
}

function ChallengeCard({ challenge }: { challenge: Challenge }) {
  const isFinal = challenge.level === FINAL_LEVEL;
  return (
    <article
      id={`level-${challenge.level}`}
      aria-labelledby={`level-${challenge.level}-title`}
      className={cn(
        "scroll-mt-6 rounded-2xl border bg-card/60 p-5 transition-colors md:p-6",
        isFinal
          ? "border-neon-pink/50 bg-gradient-to-br from-neon-pink/15 to-neon-violet/20 shadow-[0_0_40px_rgb(255_47_213/15%)]"
          : "border-neon-teal/20 hover:border-neon-teal/40",
      )}
    >
      <div className="flex gap-4">
        <div
          className={cn(
            "flex size-12 shrink-0 flex-col items-center justify-center rounded-xl ring-1 md:size-14",
            isFinal ? "bg-neon-pink/15 text-neon-pink ring-neon-pink/50" : "bg-primary/20 text-white ring-primary/50",
          )}
          aria-hidden="true"
        >
          <span className="text-[10px] leading-none tracking-wider uppercase opacity-70">Lvl</span>
          <span className="text-xl leading-tight font-bold tabular-nums md:text-2xl">{challenge.level}</span>
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-1.5">
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
            <h2 id={`level-${challenge.level}-title`} className="flex items-center gap-2 text-lg font-semibold text-white md:text-xl">
              <span className="sr-only">Level {challenge.level}: </span>
              {challenge.title}
              {isFinal && <Skull className="size-5 text-neon-pink" aria-label="Final level" />}
            </h2>
            <Difficulty level={challenge.level} />
          </div>
          {challenge.subtitle && (
            <Markdown className="text-sm font-medium prose-p:my-0 prose-p:text-neon-teal">{challenge.subtitle}</Markdown>
          )}
        </div>
      </div>

      {challenge.body && (
        <Markdown className="mt-4 text-sm prose-p:my-2 prose-p:text-card-foreground/85 md:pl-[4.5rem]">{challenge.body}</Markdown>
      )}

      {challenge.owasp.length > 0 && (
        <ul className="mt-4 flex flex-wrap gap-2 md:pl-[4.5rem]" aria-label="OWASP LLM Top 10 risks">
          {challenge.owasp.map((risk) => (
            <li
              key={risk}
              className="flex items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-400/10 px-2.5 py-1 text-xs text-amber-100"
            >
              <ShieldAlert className="size-3.5 text-amber-300" aria-hidden="true" />
              {risk}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export default async function ChallengesPage() {
  const player = await currentPlayer();
  const progress = player ? await getPlayerLevels(player.username).catch(() => null) : null;
  return (
    <PageShell
      title={siteConfig.subtitle()}
      description={`${challenges.length} levels of prompt injection, from a defenceless model to every guard combined. Get the agent to leak each level's password.`}
    >
      <section
        aria-label="Your run"
        className="rounded-2xl border border-neon-teal/20 bg-card/60 p-4"
      >
        <ChallengesMap levels={challenges.map(({ level, title }) => ({ level, title }))} progress={progress} />
      </section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <nav aria-label="Jump to level" className="flex flex-wrap gap-1.5">
          {challenges.map((challenge) => (
            <a
              key={challenge.level}
              href={`#level-${challenge.level}`}
              className={cn(
                "flex size-9 items-center justify-center rounded-lg border text-sm font-semibold tabular-nums transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring",
                challenge.level === FINAL_LEVEL
                  ? "border-neon-pink/50 text-neon-pink hover:bg-neon-pink/15"
                  : "border-neon-teal/25 text-white hover:border-neon-teal hover:bg-neon-teal/10",
              )}
              title={`Level ${challenge.level}: ${challenge.title}`}
            >
              {challenge.level}
            </a>
          ))}
        </nav>
        <ShimmerButton asChild className="shrink-0 px-5 py-2.5 text-sm">
          <Link href="/ctf">
            Start hacking <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </ShimmerButton>
      </div>

      <div className="flex flex-col gap-4">
        {challenges.map((challenge) => (
          <ChallengeCard key={challenge.level} challenge={challenge} />
        ))}
      </div>
    </PageShell>
  );
}
