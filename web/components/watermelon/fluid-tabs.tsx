"use client";

// Adapted from Watermelon UI fluid-tabs (https://ui.watermelon.sh, MIT):
// vertical navigation with a shared-layout active pill and a blur pulse on
// the newly active label.

import { motion } from "motion/react";
import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface FluidTab {
  href: string;
  label: string;
  icon: ReactNode;
}

const pillSpring = { type: "spring", stiffness: 280, damping: 25, mass: 0.8 } as const;

export function FluidTabs({
  tabs,
  activeHref,
  className,
  children,
}: {
  tabs: FluidTab[];
  activeHref: string | null;
  className?: string;
  /** Extra non-tab items (e.g. external links) laid out with the tabs. */
  children?: ReactNode;
}) {
  return (
    <nav className={cn("flex flex-col gap-2", className)}>
      {tabs.map((tab) => {
        const isActive = tab.href === activeHref;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            // Prefetches would spend the per-route rate limits (see proxy.ts).
            prefetch={false}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "group relative flex items-center gap-3 rounded-xl border px-3 py-2.5 text-sm md:px-4 md:py-3 md:text-[0.95rem] font-medium tracking-wide outline-none transition-colors",
              "focus-visible:ring-2 focus-visible:ring-ring",
              isActive
                ? "border-transparent text-white"
                : "border-neon-teal/30 bg-card/60 text-card-foreground hover:border-neon-pink/50 hover:bg-accent/80",
            )}
          >
            {isActive && (
              <motion.span
                layoutId="nav-active-pill"
                transition={pillSpring}
                className="absolute inset-0 rounded-xl border border-neon-pink/60 bg-gradient-to-b from-neon-violet/60 to-neon-pink/30 shadow-[0_0_22px_rgb(255_47_213/35%)]"
              />
            )}
            <motion.span
              className="relative z-10 flex items-center gap-3"
              animate={{ filter: isActive ? ["blur(0px)", "blur(4px)", "blur(0px)"] : "blur(0px)" }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <motion.span
                className="flex size-5 items-center justify-center text-neon-teal"
                animate={{ scale: isActive ? 1.06 : 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 15 }}
              >
                {tab.icon}
              </motion.span>
              <span>{tab.label}</span>
            </motion.span>
          </Link>
        );
      })}
      {children}
    </nav>
  );
}
