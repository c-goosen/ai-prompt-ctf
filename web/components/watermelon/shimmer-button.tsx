"use client";

// Adapted from Watermelon UI shimmer-button (https://ui.watermelon.sh, MIT).
// Client-only on purpose: importing the radix-ui barrel (for Slot) into the
// RSC environment makes the vinext 1.3 production build spin indefinitely.

import { Slot } from "radix-ui";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

/** Light sweep across the button on hover/focus. */
export function ShimmerButton({
  className,
  children,
  asChild = false,
  ...props
}: ComponentProps<"button"> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "button";
  return (
    <Comp
      className={cn(
        "group relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-lg px-6 py-3 font-medium",
        "bg-primary text-primary-foreground shadow-[0_0_20px_rgb(92_36_255/35%)] transition-shadow duration-300 hover:shadow-[0_0_28px_rgb(255_47_213/45%)]",
        "outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <Slot.Slottable>{children}</Slot.Slottable>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700 group-hover:translate-x-full group-focus-visible:translate-x-full motion-reduce:hidden"
      />
    </Comp>
  );
}
