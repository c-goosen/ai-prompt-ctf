"use client";

// Adapted from Watermelon UI labeled-progress-indicator
// (https://ui.watermelon.sh, MIT): rotating labels over an indeterminate
// shimmer bar (there is no real progress signal from the agent).

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";

export function LabeledProgressIndicator({
  labels,
  intervalMs = 1600,
}: {
  labels: string[];
  intervalMs?: number;
}) {
  const reduceMotion = useReducedMotion();
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (reduceMotion) {
      return;
    }
    const timer = setInterval(() => setIndex((prev) => (prev + 1) % labels.length), intervalMs);
    return () => clearInterval(timer);
  }, [labels.length, intervalMs, reduceMotion]);

  const label = reduceMotion ? labels[labels.length - 1] : labels[index];

  return (
    <div className="flex min-w-[220px] flex-col gap-2" role="status" aria-live="polite">
      <div className="relative flex items-center [perspective:800px]">
        <AnimatePresence mode="popLayout" initial={false}>
          <motion.span
            key={label}
            initial={{ opacity: 0, y: 10, scale: 1.3, filter: "blur(4px)", rotateX: -60 }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", rotateX: 0 }}
            exit={{ opacity: 0, filter: "blur(4px)", rotateX: 90, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 600, damping: 100, mass: 10 }}
            className="origin-bottom text-sm font-semibold"
          >
            {label}
          </motion.span>
        </AnimatePresence>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full border border-white/5 bg-background/70">
        <motion.div
          className="h-full w-2/5 rounded-full bg-gradient-to-r from-neon-violet/20 via-neon-teal to-neon-pink/20"
          initial={{ x: "-100%" }}
          animate={reduceMotion ? { x: "0%" } : { x: "260%" }}
          transition={reduceMotion ? { duration: 0 } : { duration: 1.4, repeat: Infinity, ease: "linear" }}
        />
      </div>
    </div>
  );
}
