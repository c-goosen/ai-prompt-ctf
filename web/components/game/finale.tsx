"use client";

import { Crown } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";

import { Fortress, Gremlin, Tower } from "@/components/game/sprites";
import { maxXp, rankFor } from "@/lib/progress";
import { MAX_LEVEL } from "@/lib/slash";
import { cn } from "@/lib/utils";

type Phase = "cascade" | "breach" | "victory";

// One tower falls per step, left to right, then the fortress, then the breach.
const STEP_MS = 150;
const BREACH_AT_MS = (MAX_LEVEL + 1) * STEP_MS + 300;
const VICTORY_AT_MS = BREACH_AT_MS + 650;

const LEVELS = Array.from({ length: MAX_LEVEL }, (_, i) => i + 1);
const SHARDS = 36;
const SHARD_COLORS = ["#fcee0a", "#ff2fd5", "#3cfcd1", "#e4fdf7"];
const DANCERS = [
  { size: "size-12", delay: 0.15 },
  { size: "size-16", delay: 0 },
  { size: "size-12", delay: 0.3 },
];
const TITLE = "System breached";

/**
 * The run's last level just fell: every tower goes down in a chain, the
 * fortress last, and the gremlins take over. Stays up until the player clicks
 * or presses Escape, since it only ever plays once.
 */
export function Finale({ onClose }: { onClose: () => void }) {
  const reduceMotion = useReducedMotion();
  const [phase, setPhase] = useState<Phase>(reduceMotion ? "victory" : "cascade");
  const [fallen, setFallen] = useState(reduceMotion ? MAX_LEVEL : 0);

  useEffect(() => {
    const timers = reduceMotion
      ? []
      : [
          ...LEVELS.map((level) => setTimeout(() => setFallen(level), level * STEP_MS)),
          setTimeout(() => setPhase("breach"), BREACH_AT_MS),
          setTimeout(() => setPhase("victory"), VICTORY_AT_MS),
        ];
    const onKeyDown = (keyEvent: KeyboardEvent) => {
      if (keyEvent.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      timers.forEach(clearTimeout);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [onClose, reduceMotion]);

  return (
    <motion.div
      key="finale"
      role="status"
      aria-live="assertive"
      aria-label={`${TITLE}! You cleared all ${MAX_LEVEL} levels.`}
      onClick={onClose}
      className="fixed inset-0 z-50 flex cursor-pointer flex-col items-center justify-center gap-6 overflow-hidden bg-background/90 px-4 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={phase === "breach" && !reduceMotion ? { opacity: 1, x: [0, -14, 12, -8, 6, 0] } : { opacity: 1, x: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
    >
      {phase === "victory" && (
        <motion.svg
          viewBox="0 0 1000 600"
          preserveAspectRatio="none"
          className="pointer-events-none absolute inset-0 size-full opacity-40"
          style={{ originX: 0 }}
          initial={reduceMotion ? false : { scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          aria-hidden="true"
        >
          <path d="M0 520L300 330l-30 60L700 90l-40 70L1000 0 720 250l30-60-410 270 30-60-230 110z" fill="#fcee0a" />
          <path d="M1000 240L760 370l24-50-330 240 130-30-30 50 230-110-16 36z" fill="#ff2fd5" />
        </motion.svg>
      )}
      {phase === "victory" && !reduceMotion && <Shards />}

      {/* A single flash as the fortress goes down. */}
      {phase === "breach" && (
        <motion.div
          className="pointer-events-none absolute inset-0 bg-neon-yellow"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.75, 0] }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          aria-hidden="true"
        />
      )}

      {phase === "victory" ? (
        <Victory reduceMotion={!!reduceMotion} />
      ) : (
        <TowerLine fallen={fallen} />
      )}
    </motion.div>
  );
}

/** Every level in a line, falling in turn with a gremlin sprinting along the top. */
function TowerLine({ fallen }: { fallen: number }) {
  return (
    <div className="relative w-full max-w-3xl pt-10" aria-hidden="true">
      <motion.div
        className="absolute top-0 -translate-x-1/2"
        initial={false}
        animate={{ left: `${(fallen / MAX_LEVEL) * 100}%`, y: [0, -6, 0] }}
        transition={{ left: { duration: STEP_MS / 1000, ease: "linear" }, y: { duration: 0.3, repeat: Infinity } }}
      >
        <Gremlin className="size-9 drop-shadow-[0_0_8px_rgb(60_252_209/70%)] sm:size-12" />
      </motion.div>
      <div className="flex items-end gap-0.5 sm:gap-1">
        {LEVELS.map((level) => {
          const state = level <= fallen ? "destroyed" : level === fallen + 1 ? "siege" : "standing";
          const boss = level === MAX_LEVEL;
          return (
            <motion.div
              key={`${level}-${state === "destroyed"}`}
              className={boss ? "min-w-0 flex-[2_1_0]" : "min-w-0 flex-1"}
              style={{ originY: 1 }}
              initial={state === "destroyed" ? { scaleY: 1.5, opacity: 0.4 } : false}
              animate={{ scaleY: 1, opacity: 1 }}
              transition={{ type: "spring", bounce: 0.4, duration: 0.45 }}
            >
              {boss ? <Fortress state={state} className="w-full" /> : <Tower state={state} className="w-full" />}
            </motion.div>
          );
        })}
      </div>
      <div className="mt-1 h-px bg-gradient-to-r from-transparent via-neon-yellow/70 to-transparent" />
    </div>
  );
}

function Victory({ reduceMotion }: { reduceMotion: boolean }) {
  return (
    <motion.div
      className="relative flex w-full max-w-md flex-col items-center gap-3 rounded-2xl border border-neon-yellow/60 bg-card/95 px-6 py-7 text-center shadow-[0_0_70px_rgb(252_238_10/30%)]"
      initial={reduceMotion ? false : { scale: 0.6, opacity: 0, y: 24 }}
      animate={{ scale: 1, opacity: 1, y: 0 }}
      transition={{ type: "spring", bounce: 0.45, duration: 0.7 }}
    >
      <Crown className="size-9 text-neon-yellow" aria-hidden="true" />
      <div className="flex items-end gap-2" aria-hidden="true">
        {DANCERS.map((dancer, i) => (
          <motion.div
            key={i}
            animate={reduceMotion ? undefined : { y: [0, -14, 0], rotate: [0, -8, 0, 8, 0] }}
            transition={{ duration: 0.7, repeat: Infinity, delay: dancer.delay, ease: "easeInOut" }}
          >
            <Gremlin className={cn(dancer.size, "drop-shadow-[0_0_8px_rgb(60_252_209/70%)]")} />
          </motion.div>
        ))}
      </div>
      <GlitchTitle animated={!reduceMotion} />
      <p className="text-sm text-muted-foreground">Every agent pwned. The gremlins rule the realm.</p>
      <dl className="mt-1 grid w-full grid-cols-3 gap-2">
        <Stat label="Levels" value={`${MAX_LEVEL}/${MAX_LEVEL}`} />
        <Stat label="XP" value={maxXp().toLocaleString("en")} />
        <Stat label="Rank" value={rankFor(maxXp()).title} />
      </dl>
      <p className="mt-1 text-xs text-muted-foreground">Click or press Esc to continue</p>
    </motion.div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col justify-center rounded-lg border border-white/10 bg-white/5 px-1 py-2">
      <dt className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">{label}</dt>
      <dd className="text-sm font-bold text-neon-teal">{value}</dd>
    </div>
  );
}

/** The title with teal and pink copies that slip out of register every so often. */
function GlitchTitle({ animated }: { animated: boolean }) {
  const slip = (x: number[], color: string) => (
    <motion.span
      className={cn("absolute inset-0 mix-blend-screen", color)}
      animate={{ x }}
      transition={{ duration: 0.3, repeat: Infinity, repeatDelay: 1.8 }}
      aria-hidden="true"
    >
      {TITLE}
    </motion.span>
  );
  return (
    <p className="relative font-mono text-3xl font-extrabold tracking-tight text-white uppercase">
      {animated && slip([0, -4, 3, -2, 0], "text-neon-teal")}
      {animated && slip([0, 4, -3, 2, 0], "text-neon-pink")}
      <span className="relative">{TITLE}</span>
    </p>
  );
}

/** Shards raining down behind the banner. */
function Shards() {
  return (
    <div className="pointer-events-none absolute inset-0" aria-hidden="true">
      {Array.from({ length: SHARDS }, (_, i) => (
        <motion.span
          key={i}
          className="absolute -top-4 h-3 w-1.5 rounded-[1px]"
          style={{ left: `${(i * 37) % 100}%`, backgroundColor: SHARD_COLORS[i % SHARD_COLORS.length] }}
          animate={{ y: "110vh", rotate: i % 2 === 0 ? 360 : -360 }}
          transition={{ duration: 2.6 + (i % 5) * 0.5, repeat: Infinity, delay: (i % 9) * 0.3, ease: "linear" }}
        />
      ))}
    </div>
  );
}
