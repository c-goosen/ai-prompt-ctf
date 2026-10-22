import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { CodeBlock } from "@/components/code-block";
import { cn } from "@/lib/utils";

/**
 * Markdown for FAQ/challenges content and chat messages. Raw HTML in the
 * source is not rendered (react-markdown's default), so model output can't
 * inject markup into the page.
 */
export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div
      className={cn(
        "prose prose-invert max-w-none prose-a:text-neon-teal prose-strong:text-white",
        "prose-code:rounded prose-code:bg-background/80 prose-code:px-1 prose-code:py-0.5 prose-code:font-mono prose-code:text-[0.85em] prose-code:before:content-none prose-code:after:content-none",
        "prose-pre:border prose-pre:border-neon-teal/25 prose-pre:bg-background/85 prose-pre:font-mono",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ pre: CodeBlock }}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
