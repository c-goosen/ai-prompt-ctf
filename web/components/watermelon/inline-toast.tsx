"use client";

// Adapted from Watermelon UI inline-toast (https://ui.watermelon.sh, MIT):
// the blur/scale presence transition, used for chat messages entering.

import { motion } from "motion/react";
import type { ReactNode } from "react";

export function MessageEnter({
  children,
  animate = true,
  index = 0,
}: {
  children: ReactNode;
  /** false for history loaded with the page, so it doesn't replay. */
  animate?: boolean;
  /** Stagger position within a batch of new messages. */
  index?: number;
}) {
  return (
    <motion.div
      initial={animate ? { opacity: 0, filter: "blur(4px)", scale: 0.95, y: 6 } : false}
      animate={{ opacity: 1, filter: "blur(0px)", scale: 1, y: 0 }}
      transition={{ type: "spring", bounce: 0, duration: 0.4, delay: Math.min(index, 6) * 0.06 }}
    >
      {children}
    </motion.div>
  );
}
