import { Bot, User, Wrench } from "lucide-react";
import type { ReactNode } from "react";

import { Markdown } from "@/components/markdown";
import type { ChatRole } from "@/lib/events";
import { cn } from "@/lib/utils";

const ICONS: Record<ChatRole, ReactNode> = {
  user: <User className="size-4" />,
  assistant: <Bot className="size-4" />,
  tool: <Wrench className="size-4" />,
};

/** User messages sit on the left, agent and tool output on the right (as before). */
export function ChatBubble({ role, children }: { role: ChatRole; children: ReactNode }) {
  const isUser = role === "user";
  return (
    <div className={cn("flex items-end gap-2", isUser ? "flex-row" : "flex-row-reverse")}>
      <div
        className="flex size-8 shrink-0 items-center justify-center rounded-full border border-neon-teal/30 bg-card text-neon-teal"
        aria-hidden="true"
      >
        {ICONS[role]}
      </div>
      <div
        className={cn(
          "max-w-[min(48rem,85%)] rounded-2xl border px-4 py-2.5 text-[0.95rem] text-white shadow-[0_10px_30px_rgb(7_1_32/60%)]",
          isUser && "rounded-bl-sm border-neon-teal/35 bg-gradient-to-br from-neon-teal/30 to-neon-violet/30",
          role === "assistant" && "rounded-br-sm border-neon-pink/35 bg-gradient-to-br from-neon-pink/35 to-neon-violet/50",
          role === "tool" && "rounded-br-sm border-neon-violet/50 bg-gradient-to-br from-neon-violet/40 to-background/80",
        )}
      >
        <span className="sr-only">{isUser ? "You:" : role === "tool" ? "Tool output:" : "PwnGPT:"}</span>
        {children}
      </div>
    </div>
  );
}

export function MarkdownBubble({ role, text }: { role: ChatRole; text: string }) {
  return (
    <ChatBubble role={role}>
      <Markdown className="prose-sm text-[0.95rem] prose-p:my-1.5">{text}</Markdown>
    </ChatBubble>
  );
}
