import { Bot, Brain, ChevronRight, User, Wrench } from "lucide-react";
import type { ReactNode } from "react";

import { Markdown } from "@/components/markdown";
import { splitToolSections, type ChatRole, type MessageSection } from "@/lib/events";
import { cn } from "@/lib/utils";

const ICONS: Record<ChatRole, ReactNode> = {
  user: <User className="size-4" />,
  assistant: <Bot className="size-4" />,
  tool: <Wrench className="size-4" />,
};

/** User messages sit on the left, agent and tool output on the right (as before). */
export function ChatBubble({
  role,
  children,
  compact = false,
}: {
  role: ChatRole;
  children: ReactNode;
  /** Tighter padding, for a bubble holding only collapsed tool calls. */
  compact?: boolean;
}) {
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
          "max-w-[min(48rem,85%)] rounded-2xl border text-[0.95rem] text-white shadow-[0_10px_30px_rgb(7_1_32/60%)]",
          compact ? "px-2 py-1.5" : "px-4 py-2.5",
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

/** The model's reasoning (ADK include_thoughts), collapsed by default. */
function Thoughts({ text }: { text: string }) {
  return (
    <details className="group mb-1.5 rounded-lg border border-neon-teal/25 bg-background/40 text-white/75">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-neon-teal select-none [&::-webkit-details-marker]:hidden">
        <ChevronRight className="size-3.5 transition-transform group-open:rotate-90" aria-hidden="true" />
        <Brain className="size-3.5" aria-hidden="true" />
        Thoughts
      </summary>
      <Markdown className="prose-sm border-t border-neon-teal/15 px-2.5 py-1.5 text-[0.85rem] italic prose-p:my-1">
        {text}
      </Markdown>
    </details>
  );
}

/** A tool call or its response, collapsed to one line until opened. */
function ToolSection({ section }: { section: Extract<MessageSection, { kind: "tool" }> }) {
  return (
    <details className="group rounded-lg border border-neon-violet/40 bg-background/40 text-white/85 [&+&]:mt-1.5">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-white/75 select-none hover:text-white [&::-webkit-details-marker]:hidden">
        <ChevronRight className="size-3.5 shrink-0 transition-transform group-open:rotate-90" aria-hidden="true" />
        <Wrench className="size-3.5 shrink-0 text-neon-teal" aria-hidden="true" />
        {section.label}
        <code className="truncate font-mono text-neon-teal">{section.name}</code>
      </summary>
      <Markdown className="prose-sm border-t border-neon-violet/25 px-2.5 py-1.5 text-[0.85rem] prose-pre:my-1">
        {section.body}
      </Markdown>
    </details>
  );
}

export function MarkdownBubble({ role, text, thoughts }: { role: ChatRole; text: string; thoughts?: string }) {
  const sections = text ? splitToolSections(text) : [];
  const onlyTools = !thoughts && sections.length > 0 && sections.every((section) => section.kind === "tool");
  return (
    <ChatBubble role={role} compact={onlyTools}>
      {thoughts && <Thoughts text={thoughts} />}
      {sections.map((section, index) =>
        section.kind === "tool" ? (
          <ToolSection key={index} section={section} />
        ) : (
          <Markdown key={index} className="prose-sm text-[0.95rem] prose-p:my-1.5">
            {section.text}
          </Markdown>
        ),
      )}
    </ChatBubble>
  );
}
