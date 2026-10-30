"use client";

import { Crown, Trophy } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";

import { Fortress, Gremlin, Tower } from "@/components/game/sprites";
import { MAX_LEVEL } from "@/lib/slash";

export interface LevelUpEvent {
  /** Solved levels, lowest first. */
  levels: number[];
  /** XP for levels not cleared before; 0 for a re-solve or level 0. */
  xp: number;
  /** Set when the player reached a new rank. */
  rank?: string;
  /** The next level to play, or null after the boss. */
  next: { level: number; title: string } | null;
}

type Phase = "march" | "attack" | "fallen";

// The siege: the horde marches in, attacks, the tower falls, then the banner.
const ATTACK_AT_MS = 1_300;
const FALL_AT_MS = 2_900;
const DISMISS_MS = 6_500;
const REDUCED_DISMISS_MS = 3_500;

const GREMLINS = [
  { x: -150, y: 10, size: "size-10", delay: 0 },
  { x: -112, y: -14, size: "size-12", delay: 0.12 },
  { x: -80, y: 14, size: "size-9", delay: 0.24 },
  { x: -48, y: -6, size: "size-11", delay: 0.06 },
  { x: -186, y: -2, size: "size-9", delay: 0.18 },
];
const DEBRIS = 14;
const PARTICLES = 24;
const PARTICLE_COLORS = ["#3cfcd1", "#ff2fd5", "#5c24ff", "#e4fdf7"];

/** Gremlins storming a tower when a level is solved. Click, Escape or wait to continue. */
export function LevelUp({ event, onClose }: { event: LevelUpEvent | null; onClose: () => void }) {
  return (
    <AnimatePresence>{event && <Siege key={event.levels.join(",")} event={event} onClose={onClose} />}</AnimatePresence>
  );
}

function Siege({ event, onClose }: { event: LevelUpEvent; onClose: () => void }) {
  const reduceMotion = useReducedMotion();
  const [phase, setPhase] = useState<Phase>(reduceMotion ? "fallen" : "march");

  useEffect(() => {
    const timers = reduceMotion
      ? [setTimeout(onClose, REDUCED_DISMISS_MS)]
      : [
          setTimeout(() => setPhase("attack"), ATTACK_AT_MS),
          setTimeout(() => setPhase("fallen"), FALL_AT_MS),
          setTimeout(onClose, DISMISS_MS),
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

  const level = event.levels[event.levels.length - 1];
  const boss = level === MAX_LEVEL;
  const fallen = phase === "fallen";
  const cleared =
    event.levels.length === 1
      ? `Level ${event.levels[0]} tower destroyed!`
      : `Levels ${event.levels.join(", ")} towers destroyed!`;

  return (
    <motion.div
      key="level-up"
      role="status"
      aria-live="assertive"
      aria-label={cleared}
      onClick={onClose}
      className="fixed inset-0 z-50 flex cursor-pointer flex-col items-center justify-center gap-6 bg-background/75 px-4 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
    >
      {/* The battlefield */}
      <div className="relative h-48 w-full max-w-md" aria-hidden="true">
        <div className="absolute inset-x-0 bottom-6 h-px bg-gradient-to-r from-transparent via-neon-teal/50 to-transparent" />

        {/* The tower (or the level 10 fortress), shaking under attack */}
        <motion.div
          className="absolute bottom-6 left-[68%] -translate-x-1/2"
          animate={
            phase === "attack" && !reduceMotion
              ? { x: [0, -5, 5, -4, 4, -2, 0], rotate: [0, -2, 2, -1.5, 1.5, 0] }
              : { x: 0, rotate: 0 }
          }
          transition={{ duration: 0.5, repeat: phase === "attack" ? Infinity : 0 }}
        >
          <motion.div
            key={fallen ? "rubble" : "standing"}
            initial={fallen && !reduceMotion ? { scaleY: 1.6, opacity: 0.4 } : false}
            animate={{ scaleY: 1, opacity: 1 }}
            transition={{ type: "spring", bounce: 0.35, duration: 0.6 }}
            style={{ originY: 1 }}
          >
            {boss ? (
              <Fortress state={fallen ? "destroyed" : "siege"} className="h-32 w-auto" />
            ) : (
              <Tower
                state={fallen ? "destroyed" : "siege"}
                className="h-32 w-auto drop-shadow-[0_0_14px_rgb(255_47_213/45%)]"
              />
            )}
          </motion.div>
          {phase === "attack" && !reduceMotion && <Sparks />}
          {fallen && !reduceMotion && <Debris />}
        </motion.div>

        {/* The horde */}
        <div className="absolute bottom-6 left-[68%]">
          {GREMLINS.map((gremlin, i) => (
            <motion.div
              key={i}
              className="absolute bottom-0"
              style={{ left: gremlin.x, marginBottom: gremlin.y }}
              initial={reduceMotion ? false : { x: -260, opacity: 0 }}
              animate={
                reduceMotion
                  ? undefined
                  : phase === "march"
                    ? { x: 0, opacity: 1, y: [0, -6, 0] }
                    : phase === "attack"
                      ? { x: [0, 26, 0], y: [0, -14, 0], opacity: 1 }
                      : { x: 0, y: [0, -22, 0], opacity: 1 }
              }
              transition={
                phase === "march"
                  ? {
                      x: { duration: 1.1, ease: "easeOut", delay: gremlin.delay },
                      opacity: { duration: 0.3, delay: gremlin.delay },
                      y: { duration: 0.35, repeat: Infinity, delay: gremlin.delay },
                    }
                  : { duration: phase === "attack" ? 0.4 : 0.55, repeat: Infinity, delay: gremlin.delay }
              }
            >
              <Gremlin className={`${gremlin.size} drop-shadow-[0_0_8px_rgb(60_252_209/70%)]`} />
            </motion.div>
          ))}
        </div>
      </div>

      {/* The banner, once the tower falls */}
      <AnimatePresence>
        {fallen && (
          <motion.div
            className="relative flex max-w-sm flex-col items-center gap-2 rounded-2xl border border-neon-pink/50 bg-card/95 px-8 py-6 text-center shadow-[0_0_60px_rgb(255_47_213/35%)]"
            initial={reduceMotion ? { opacity: 0 } : { scale: 0.6, opacity: 0, y: 20 }}
            animate={reduceMotion ? { opacity: 1 } : { scale: 1, opacity: 1, y: 0 }}
            transition={{ type: "spring", bounce: 0.45, duration: 0.6 }}
          >
            {!reduceMotion && <Burst />}
            {boss ? (
              <Crown className="size-10 text-neon-pink" aria-hidden="true" />
            ) : (
              <Trophy className="size-10 text-amber-300" aria-hidden="true" />
            )}
            <p className="text-2xl font-bold text-white">{boss ? "The fortress has fallen!" : cleared}</p>
            {event.xp > 0 && (
              <p className="text-lg font-semibold text-neon-teal">+{event.xp.toLocaleString("en")} XP</p>
            )}
            {event.rank && (
              <p className="rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-sm text-amber-100">
                New rank: <strong>{event.rank}</strong>
              </p>
            )}
            <p className="text-sm text-muted-foreground">
              {event.next
                ? `The horde marches on Level ${event.next.level}: ${event.next.title}`
                : "Every agent pwned. The gremlins rule the realm."}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/** Sparks off the tower while the horde attacks. */
function Sparks() {
  return (
    <span className="pointer-events-none absolute top-1/4 left-1/2" aria-hidden="true">
      {Array.from({ length: 8 }, (_, i) => {
        const angle = (i / 8) * Math.PI * 2;
        return (
          <motion.span
            key={i}
            className="absolute size-1.5 rounded-full bg-neon-pink shadow-[0_0_8px_#ff2fd5]"
            initial={{ x: 0, y: 0, opacity: 0 }}
            animate={{ x: Math.cos(angle) * 34, y: Math.sin(angle) * 34 - 10, opacity: [0, 1, 0] }}
            transition={{ duration: 0.5, repeat: Infinity, delay: (i % 4) * 0.12, ease: "easeOut" }}
          />
        );
      })}
    </span>
  );
}

/** Stones flying off as the tower collapses. */
function Debris() {
  return (
    <span className="pointer-events-none absolute top-1/2 left-1/2" aria-hidden="true">
      {Array.from({ length: DEBRIS }, (_, i) => {
        const side = i % 2 === 0 ? 1 : -1;
        return (
          <motion.span
            key={i}
            className="absolute size-2 rounded-[2px] bg-[#a8a2ff]"
            initial={{ x: 0, y: 0, rotate: 0, opacity: 1 }}
            animate={{
              x: side * (20 + (i * 13) % 70),
              y: [0, -40 - (i * 7) % 40, 50],
              rotate: side * 220,
              opacity: [1, 1, 0],
            }}
            transition={{ duration: 1.1, ease: "easeOut" }}
          />
        );
      })}
    </span>
  );
}

/** Particle burst behind the banner. */
function Burst() {
  return (
    <>
      {Array.from({ length: PARTICLES }, (_, i) => {
        const angle = (i / PARTICLES) * Math.PI * 2;
        const distance = 150 + (i % 4) * 40;
        const color = PARTICLE_COLORS[i % PARTICLE_COLORS.length];
        return (
          <motion.span
            key={i}
            aria-hidden="true"
            className="absolute top-1/2 left-1/2 size-2.5 rounded-full"
            style={{ backgroundColor: color, boxShadow: `0 0 12px ${color}` }}
            initial={{ x: 0, y: 0, scale: 0, opacity: 1 }}
            animate={{
              x: Math.cos(angle) * distance,
              y: Math.sin(angle) * distance,
              scale: [0, 1.4, 0.6],
              opacity: [1, 1, 0],
            }}
            transition={{ duration: 1.3, ease: "easeOut", delay: (i % 3) * 0.05 }}
          />
        );
      })}
    </>
  );
}
