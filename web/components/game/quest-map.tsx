"use client";

import { motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";

import { Camp, Fortress, Gremlin, Tower, type TowerState } from "@/components/game/sprites";
import { DIFFICULTY, difficulty } from "@/lib/challenges";
import { currentLevel } from "@/lib/progress";
import { MAX_LEVEL } from "@/lib/slash";
import { cn } from "@/lib/utils";

export interface QuestLevel {
  level: number;
  title: string;
}

// The map is drawn in a 1000x300 box: levels 0-5 left to right on the top
// row, then 6-10 back right to left below, ending at the boss.
const WIDTH = 1000;
const HEIGHT = 380;
const NODES: Array<{ x: number; y: number }> = [
  { x: 70, y: 140 },
  { x: 240, y: 120 },
  { x: 410, y: 150 },
  { x: 580, y: 120 },
  { x: 750, y: 150 },
  { x: 920, y: 140 },
  { x: 845, y: 320 },
  { x: 665, y: 305 },
  { x: 485, y: 335 },
  { x: 305, y: 305 },
  { x: 125, y: 320 },
];

const ZONE_STYLES = [
  "fill-neon-teal/5 stroke-neon-teal/25",
  "fill-neon-teal/10 stroke-neon-teal/35",
  "fill-neon-violet/15 stroke-neon-violet/50",
  "fill-neon-pink/10 stroke-neon-pink/35",
  "fill-neon-pink/15 stroke-neon-pink/55",
];
const ZONE_PAD = 44;
// Towers rise above their node, so zones reach higher than they go below.
const ZONE_HEADROOM = 70;

const zones = DIFFICULTY.map((label, index) => {
  const members = NODES.filter((_, level) => difficulty(level, MAX_LEVEL) === index + 1);
  const xs = members.map((node) => node.x);
  const ys = members.map((node) => node.y);
  return {
    label,
    style: ZONE_STYLES[index],
    x: Math.min(...xs) - ZONE_PAD,
    y: Math.min(...ys) - ZONE_PAD - ZONE_HEADROOM,
    width: Math.max(...xs) - Math.min(...xs) + ZONE_PAD * 2,
    height: Math.max(...ys) - Math.min(...ys) + ZONE_PAD * 2 + ZONE_HEADROOM,
  };
});

/** Catmull-Rom curve from node i to i+1, as an SVG path. */
function segmentPath(i: number): string {
  const p0 = NODES[Math.max(i - 1, 0)];
  const p1 = NODES[i];
  const p2 = NODES[i + 1];
  const p3 = NODES[Math.min(i + 2, NODES.length - 1)];
  const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 };
  const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 };
  return `M${p1.x},${p1.y} C${c1.x},${c1.y} ${c2.x},${c2.y} ${p2.x},${p2.y}`;
}

const percent = (value: number, of: number) => `${(value / of) * 100}%`;

/**
 * Where the character stands, and the nodes it walks through to get there
 * after the player clears levels.
 */
function useWalk(position: number, replay: boolean) {
  const [walk, setWalk] = useState({ from: position, to: position });
  if (!replay && walk.to !== position) {
    setWalk({ from: walk.to, to: position });
  }

  // Replay: every so often the horde reappears at camp and marches back to
  // where the player is, through every tower they've knocked down.
  useEffect(() => {
    if (!replay || position === 0) {
      return;
    }
    let march: ReturnType<typeof setTimeout> | undefined;
    const cycle = () => {
      setWalk({ from: 0, to: 0 });
      march = setTimeout(() => setWalk({ from: 0, to: position }), REPLAY_PAUSE_MS);
    };
    const timer = setInterval(cycle, REPLAY_PAUSE_MS + position * STEP_SECONDS * 1000 + REPLAY_REST_MS);
    return () => {
      clearInterval(timer);
      clearTimeout(march);
    };
  }, [replay, position]);

  const step = walk.from <= walk.to ? 1 : -1;
  const stops: number[] = [];
  for (let level = walk.from; level !== walk.to + step; level += step) {
    stops.push(level);
  }
  return stops;
}

const STEP_SECONDS = 0.45;
const REPLAY_PAUSE_MS = 900;
const REPLAY_REST_MS = 4_000;

type NodeState = "cleared" | "current" | "locked";

const TOWER_STATE: Record<NodeState, TowerState> = { cleared: "destroyed", current: "siege", locked: "standing" };

/** Which way the horde faces at a node: towards it, from the previous one. */
function facing(level: number): 1 | -1 {
  return level > 0 && NODES[level].x < NODES[level - 1].x ? -1 : 1;
}

/** Three gremlins bobbing out of step, camped just before the tower they're attacking. */
function Horde({ facing, cheering, reduceMotion }: { facing: 1 | -1; cheering: boolean; reduceMotion: boolean }) {
  const offsets = [
    { x: -84, y: -2, size: "size-7" },
    { x: -62, y: -16, size: "size-8" },
    { x: -42, y: 2, size: "size-7" },
  ];
  return (
    <div className="relative" style={{ transform: `scaleX(${facing})` }}>
      {offsets.map((offset, i) => (
        <motion.div
          key={i}
          className="absolute"
          style={{ left: offset.x, top: offset.y - 30 }}
          animate={reduceMotion ? undefined : { y: cheering ? [0, -10, 0] : [0, -3, 0], rotate: cheering ? 0 : [0, -6, 0, 6, 0] }}
          transition={{ duration: cheering ? 0.6 : 0.9, repeat: Infinity, delay: i * 0.2, ease: "easeInOut" }}
        >
          <Gremlin className={cn(offset.size, "drop-shadow-[0_0_6px_rgb(60_252_209/70%)]")} />
        </motion.div>
      ))}
    </div>
  );
}

/** Smoke rising from a destroyed tower. */
function Smoke() {
  return (
    <span className="pointer-events-none absolute top-1/3 left-1/2" aria-hidden="true">
      {[0, 1].map((i) => (
        <motion.span
          key={i}
          className="absolute size-2 rounded-full bg-white/25 blur-[1px]"
          initial={{ x: i * 4 - 2, y: 0, opacity: 0, scale: 0.6 }}
          animate={{ y: -22, opacity: [0, 0.8, 0], scale: [0.6, 1.4, 1.8] }}
          transition={{ duration: 2.2, repeat: Infinity, delay: i * 1.1, ease: "easeOut" }}
        />
      ))}
    </span>
  );
}

/** Sparks flying off a tower under siege. */
function Sparks() {
  const sparks = [
    { x: -14, y: -10 },
    { x: 12, y: -14 },
    { x: -6, y: -20 },
    { x: 16, y: -4 },
  ];
  return (
    <span className="pointer-events-none absolute top-1/4 left-1/2" aria-hidden="true">
      {sparks.map((spark, i) => (
        <motion.span
          key={i}
          className="absolute size-1 rounded-full bg-neon-pink shadow-[0_0_6px_#ff2fd5]"
          initial={{ x: 0, y: 0, opacity: 0 }}
          animate={{ x: spark.x, y: spark.y, opacity: [0, 1, 0] }}
          transition={{ duration: 0.7, repeat: Infinity, delay: i * 0.18, ease: "easeOut" }}
        />
      ))}
    </span>
  );
}

function nodeState(level: number, progress: number[] | null, position: number | null): NodeState {
  // Basecamp (level 0) is cleared by registering.
  if (progress && (level === 0 || progress.includes(level))) {
    return "cleared";
  }
  return level === position ? "current" : "locked";
}

/**
 * The siege trail: every level is a guard tower on a winding path through
 * the difficulty zones, ending at the level 10 fortress. The player's gremlin
 * horde camps at the next tower to break; cleared towers lie in smoking rubble.
 * `progress` is null for visitors who haven't registered (everything locked).
 */
export function QuestMap({
  levels,
  progress,
  variant = "full",
  replay = false,
  onSelect,
}: {
  levels: QuestLevel[];
  progress: number[] | null;
  variant?: "full" | "compact";
  /** Keep re-marching the horde from camp to the player's tower (Challenges page). */
  replay?: boolean;
  onSelect?: (level: number) => void;
}) {
  const reduceMotion = useReducedMotion();
  const position = progress ? currentLevel(progress) : null;
  // All cleared: the character stands on the defeated boss.
  const standing = progress === null ? 0 : (position ?? MAX_LEVEL);
  const stops = useWalk(standing, replay && !reduceMotion);
  const titles = new Map(levels.map((level) => [level.level, level.title]));
  const walkTransition = reduceMotion
    ? { duration: 0 }
    : stops.length === 1
      ? { duration: 0 }
      : { duration: (stops.length - 1) * STEP_SECONDS, ease: "easeInOut" as const };

  if (variant === "compact") {
    const along = (level: number) => percent(level, MAX_LEVEL);
    return (
      <div className="flex items-center gap-3">
        <div className="relative h-7 w-40 sm:w-56" aria-hidden="true">
          <div className="absolute inset-x-0 top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-white/10" />
          <div
            className="absolute top-1/2 left-0 h-0.5 -translate-y-1/2 rounded-full bg-gradient-to-r from-neon-teal to-neon-pink shadow-[0_0_8px_rgb(60_252_209/60%)] transition-[width] duration-700"
            style={{ width: along(standing) }}
          />
          {NODES.map((_, level) => {
            const state = nodeState(level, progress, position);
            return (
              <span
                key={level}
                className={cn(
                  "absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full",
                  level === MAX_LEVEL ? "size-2.5" : "size-1.5",
                  state === "cleared" && "bg-neon-teal",
                  state === "current" && "bg-neon-pink",
                  state === "locked" && (level === MAX_LEVEL ? "bg-neon-pink/40" : "bg-white/25"),
                )}
                style={{ left: along(level) }}
              />
            );
          })}
          <motion.div
            className="absolute top-0 -translate-x-1/2 -translate-y-1/2"
            initial={false}
            animate={{ left: stops.map(along) }}
            transition={walkTransition}
          >
            <Gremlin className="size-5 drop-shadow-[0_0_6px_rgb(60_252_209/70%)]" />
          </motion.div>
        </div>
        <span className="text-xs font-medium whitespace-nowrap text-muted-foreground">
          {position === null ? "All cleared" : `Lvl ${position}`}
        </span>
        <span className="sr-only">
          {progress === null
            ? "Register to start your run."
            : position === null
              ? "You have cleared every level."
              : `You are on level ${position}: ${titles.get(position) ?? ""}.`}
        </span>
      </div>
    );
  }

  const at = (level: number) => NODES[level];
  return (
    <div className="w-full overflow-x-auto">
      <div className="relative mx-auto aspect-[1000/380] min-w-[640px]">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="absolute inset-0 size-full" aria-hidden="true">
          <defs>
            <linearGradient id="quest-trail" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#3cfcd1" />
              <stop offset="1" stopColor="#ff2fd5" />
            </linearGradient>
            <filter id="quest-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {zones.map((zone) => (
            <rect
              key={zone.label}
              x={zone.x}
              y={zone.y}
              width={zone.width}
              height={zone.height}
              rx={40}
              strokeWidth={1.5}
              strokeDasharray="6 6"
              className={zone.style}
            />
          ))}
          {NODES.slice(0, -1).map((_, i) => {
            const lit = progress !== null && i + 1 <= standing;
            return (
              <path
                key={i}
                d={segmentPath(i)}
                fill="none"
                strokeLinecap="round"
                strokeWidth={lit ? 5 : 3}
                stroke={lit ? "url(#quest-trail)" : "rgb(255 255 255 / 18%)"}
                strokeDasharray={lit ? undefined : "2 10"}
                filter={lit ? "url(#quest-glow)" : undefined}
              />
            );
          })}
        </svg>

        {zones.map((zone) => (
          <span
            key={zone.label}
            className="absolute text-[11px] font-semibold tracking-wider text-muted-foreground uppercase"
            // Bottom-left, clear of the character standing above the nodes.
            style={{ left: percent(zone.x + 18, WIDTH), top: percent(zone.y + zone.height - 22, HEIGHT) }}
          >
            {zone.label}
          </span>
        ))}

        {NODES.map((node, level) => {
          const state = nodeState(level, progress, position);
          const boss = level === MAX_LEVEL;
          const tower = TOWER_STATE[state];
          const title = level === 0 ? `Gremlin camp: ${titles.get(0) ?? ""}` : (titles.get(level) ?? "");
          const status = {
            cleared: level === 0 ? "your camp" : "tower destroyed",
            current: "under siege, your next level",
            locked: "tower standing",
          }[state];
          return (
            <button
              key={level}
              type="button"
              onClick={() => onSelect?.(level)}
              disabled={!onSelect}
              title={`Level ${level}: ${title}`}
              aria-label={`Level ${level}, ${title}, ${status}`}
              className={cn(
                "group absolute flex -translate-x-1/2 -translate-y-[88%] flex-col items-center rounded-lg outline-none transition-transform hover:-translate-y-[92%] focus-visible:ring-2 focus-visible:ring-ring disabled:hover:-translate-y-[88%]",
                boss ? "w-[10%]" : "w-[5.6%]",
              )}
              style={{ left: percent(node.x, WIDTH), top: percent(node.y, HEIGHT) }}
            >
              {/* Smoke over rubble, sparks around a tower under siege. */}
              {!reduceMotion && state === "cleared" && level > 0 && <Smoke />}
              {!reduceMotion && state === "current" && <Sparks />}
              {level === 0 ? (
                <Camp className="w-full" />
              ) : boss ? (
                <Fortress
                  state={tower}
                  className={cn(
                    "w-full",
                    state !== "cleared" && "drop-shadow-[0_0_14px_rgb(255_47_213/45%)]",
                    state === "current" && !reduceMotion && "animate-[shake_0.5s_ease-in-out_infinite]",
                  )}
                />
              ) : (
                <Tower
                  state={tower}
                  className={cn(
                    "w-full",
                    state === "current" && "drop-shadow-[0_0_12px_rgb(255_47_213/60%)]",
                    state === "current" && !reduceMotion && "animate-[shake_0.5s_ease-in-out_infinite]",
                    state === "locked" && "opacity-80",
                  )}
                />
              )}
              <span
                className={cn(
                  "mt-0.5 rounded-full px-1.5 text-[10px] leading-4 font-bold tabular-nums",
                  state === "cleared" && "bg-neon-teal text-background",
                  state === "current" && "bg-neon-pink text-white",
                  state === "locked" && "bg-white/10 text-white/60",
                )}
              >
                {level === 0 ? "Camp" : level}
              </span>
            </button>
          );
        })}

        <motion.div
          className="pointer-events-none absolute z-10"
          initial={false}
          animate={{
            left: stops.map((level) => percent(at(level).x, WIDTH)),
            top: stops.map((level) => percent(at(level).y, HEIGHT)),
          }}
          transition={walkTransition}
          aria-hidden="true"
        >
          <Horde facing={facing(standing)} cheering={progress !== null && position === null} reduceMotion={!!reduceMotion} />
        </motion.div>
      </div>
    </div>
  );
}
