"use client";

import { useRef, type ComponentProps } from "react";

import { CopyConfirm } from "@/components/watermelon/copy-confirm";

/** <pre> with a copy button; copies the rendered text, not the button. */
export function CodeBlock(props: ComponentProps<"pre">) {
  const ref = useRef<HTMLPreElement>(null);
  return (
    <div className="relative">
      <pre ref={ref} {...props} className="!mt-0 overflow-x-auto pt-10 whitespace-pre-wrap break-words" />
      <CopyConfirm
        className="absolute top-2 right-2"
        value={() => ref.current?.innerText.trim() ?? ""}
      />
    </div>
  );
}
