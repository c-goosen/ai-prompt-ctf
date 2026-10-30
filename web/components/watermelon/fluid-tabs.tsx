"use client";

// Adapted from Watermelon UI fluid-tabs (https://ui.watermelon.sh, MIT):
// vertical navigation with a shared-layout active pill and a blur pulse on
// the newly active label.

import { motion } from "motion/react";
import Link from "next/link";
import { useId, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface FluidTab {
  href: string;
  label: string;
  icon: ReactNode;
  /** Opens in a new tab and is never shown as active. */
  external?: boolean;
}

const pillSpring = { type: "spring", stiffness: 280, damping: 25, mass: 0.8 } as const;

export function FluidTabs({
  tabs,
  activeHref,
  collapsed = false,
  className,
}: {
  tabs: FluidTab[];
  activeHref: string | null;
  /** Icons only; labels stay available to screen readers and as tooltips. */
  collapsed?: boolean;
  className?: string;
}) {
  // Per instance, so the mobile drawer and desktop rail don't share a pill.
  const pillId = `nav-active-pill-${useId()}`;
  return (
    <nav aria-label="Main" className={cn("flex flex-col gap-1.5", className)}>
      {tabs.map((tab) => {
        const isActive = !tab.external && tab.href === activeHref;
        const itemClass = cn(
          "group relative flex h-11 items-center rounded-xl border text-sm font-medium tracking-wide outline-none transition-colors",
          "focus-visible:ring-2 focus-visible:ring-ring",
          collapsed ? "justify-center px-0" : "px-3",
          isActive
            ? "border-transparent text-white"
            : "border-transparent text-card-foreground/85 hover:border-neon-pink/40 hover:bg-accent/70 hover:text-white",
        );
        const content = (
          <>
            {isActive && (
              <motion.span
                layoutId={pillId}
                transition={pillSpring}
                className="absolute inset-0 rounded-xl border border-neon-pink/60 bg-gradient-to-b from-neon-violet/60 to-neon-pink/30 shadow-[0_0_22px_rgb(255_47_213/35%)]"
              />
            )}
            <motion.span
              className="relative z-10 flex min-w-0 items-center gap-3"
              animate={{ filter: isActive ? ["blur(0px)", "blur(4px)", "blur(0px)"] : "blur(0px)" }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <motion.span
                className="flex size-5 shrink-0 items-center justify-center text-neon-teal"
                animate={{ scale: isActive ? 1.06 : 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 15 }}
              >
                {tab.icon}
              </motion.span>
              <span className={cn("truncate", collapsed && "sr-only")}>{tab.label}</span>
            </motion.span>
          </>
        );
        const title = collapsed ? tab.label : undefined;
        return tab.external ? (
          <a
            key={tab.href}
            href={tab.href}
            target="_blank"
            rel="noopener noreferrer"
            title={title}
            className={itemClass}
          >
            {content}
          </a>
        ) : (
          <Link
            key={tab.href}
            href={tab.href}
            // Prefetches would spend the per-route rate limits (see proxy.ts).
            prefetch={false}
            aria-current={isActive ? "page" : undefined}
            title={title}
            className={itemClass}
          >
            {content}
          </Link>
        );
      })}
    </nav>
  );
}
