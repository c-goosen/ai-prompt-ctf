"use client";

// Adapted from Watermelon UI copy-confirm (https://ui.watermelon.sh, MIT):
// icon blur/scale swap, green confirmation and per-letter "Copied" text.

import { Check, Copy } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

async function copyText(text: string): Promise<boolean> {
  // navigator.clipboard needs a secure context; the app is often served over
  // plain http on a LAN address, so keep the legacy fallback.
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // fall through
    }
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.append(textarea);
  textarea.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  }
  textarea.remove();
  return copied;
}

type State = "idle" | "copied" | "failed";

export function CopyConfirm({
  value,
  className,
  copyText: idleText = "Copy",
  copiedText = "Copied",
}: {
  value: string | (() => string);
  className?: string;
  copyText?: string;
  copiedText?: string;
}) {
  const [state, setState] = useState<State>("idle");
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);

  async function handleCopy() {
    const ok = await copyText(typeof value === "function" ? value() : value);
    setState(ok ? "copied" : "failed");
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setState("idle"), 1800);
  }

  const label = state === "copied" ? copiedText : state === "failed" ? "Copy failed" : idleText;

  return (
    <motion.button
      type="button"
      onClick={handleCopy}
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.96 }}
      animate={{ backgroundColor: state === "copied" ? "#15803d" : "rgba(5, 2, 25, 0.9)" }}
      aria-label={state === "copied" ? "Copied to clipboard" : "Copy to clipboard"}
      className={cn(
        "relative inline-flex items-center gap-1.5 overflow-hidden rounded-full border border-neon-teal/35 px-2.5 py-1 text-xs font-semibold text-card-foreground",
        state === "copied" && "border-green-500",
        className,
      )}
    >
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.span
          key={state === "copied" ? "check" : "copy"}
          initial={{ opacity: 0, scale: 0.25, filter: "blur(4px)" }}
          animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
          exit={{ opacity: 0, scale: 0.25, filter: "blur(4px)" }}
          transition={{ type: "spring", duration: 0.3, bounce: 0 }}
        >
          {state === "copied" ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
        </motion.span>
      </AnimatePresence>
      <span className="flex" aria-hidden="true">
        <AnimatePresence mode="popLayout" initial={false}>
          {label.split("").map((char, index) => (
            <motion.span
              key={`${label}-${index}`}
              layout
              initial={{ opacity: 0, y: 5, scale: 0.7 }}
              animate={{
                opacity: 1,
                y: 0,
                scale: 1,
                transition: { type: "spring", stiffness: 200, damping: 20, delay: 0.03 * index },
              }}
              exit={{ opacity: 0, y: -5, scale: 0.7 }}
            >
              {char === " " ? " " : char}
            </motion.span>
          ))}
        </AnimatePresence>
      </span>
    </motion.button>
  );
}
