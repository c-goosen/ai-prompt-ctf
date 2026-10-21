"use client";

import { FileText, Paperclip, SendHorizontal, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { ChatBubble, MarkdownBubble } from "@/components/chat/chat-bubble";
import { WelcomeMessages } from "@/components/chat/welcome";
import { Footer } from "@/components/footer";
import { MessageEnter } from "@/components/watermelon/inline-toast";
import { LabeledProgressIndicator } from "@/components/watermelon/labeled-progress-indicator";
import { ShimmerButton } from "@/components/watermelon/shimmer-button";
import type { ChatMessage } from "@/lib/events";

const LOADER_LABELS = ["Thinking…", "Checking guardrails…", "Calling tools…", "Sending…"];
const ACCEPT = ".pdf,.json,image/*,audio/*,application/pdf,application/json";

interface Entry extends ChatMessage {
  id: number;
  /** Arrived during this visit, so it animates in (history doesn't). */
  fresh: boolean;
  /** Stagger position within its batch. */
  batchIndex: number;
}

type Alert = { kind: "register" } | { kind: "error"; message: string };

let nextId = 0;
const toEntries = (messages: ChatMessage[], fresh: boolean): Entry[] =>
  messages.map((message, batchIndex) => ({ ...message, id: nextId++, fresh, batchIndex }));

export function ChatScreen({
  initialMessages,
  registered,
}: {
  initialMessages: ChatMessage[];
  registered: boolean;
}) {
  const [entries, setEntries] = useState<Entry[]>(() => toEntries(initialMessages, false));
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [alert, setAlert] = useState<Alert | null>(registered ? null : { kind: "register" });
  const fileInput = useRef<HTMLInputElement>(null);
  const textInput = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [entries, pending]);

  async function send(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || pending) {
      return;
    }
    const form = new FormData();
    form.set("text_input", text);
    if (file) {
      form.set("file_input", file);
    }

    setEntries((prev) => [...prev, ...toEntries([{ role: "user", text }], true)]);
    setInput("");
    setFile(null);
    if (fileInput.current) {
      fileInput.current.value = "";
    }
    setAlert(null);
    setPending(true);

    try {
      const response = await fetch("/v1/chat/completions", { method: "POST", body: form });
      const body = await response.json().catch(() => ({}));
      if (response.status === 401) {
        setAlert({ kind: "register" });
      } else if (!response.ok) {
        setAlert({ kind: "error", message: body.message ?? body.error ?? `Request failed (${response.status})` });
      } else {
        setEntries((prev) => [...prev, ...toEntries(body.messages as ChatMessage[], true)]);
      }
    } catch {
      setAlert({ kind: "error", message: "Could not reach the server. Please try again." });
    } finally {
      setPending(false);
      textInput.current?.focus();
    }
  }

  return (
    <div className="flex min-h-full flex-col">
      <div className="flex flex-1 flex-col gap-3 p-4 md:p-6" aria-live="polite">
        {entries.length === 0 && <WelcomeMessages />}
        {entries.map((entry) => (
          <MessageEnter key={entry.id} animate={entry.fresh} index={entry.batchIndex}>
            <MarkdownBubble role={entry.role} text={entry.text} />
          </MessageEnter>
        ))}
        {pending && (
          <MessageEnter>
            <ChatBubble role="assistant">
              <LabeledProgressIndicator labels={LOADER_LABELS} />
            </ChatBubble>
          </MessageEnter>
        )}
        {alert && (
          <div
            role="alert"
            className="rounded-xl border border-neon-pink/40 bg-card/80 px-4 py-3 text-sm text-card-foreground"
          >
            {alert.kind === "register" ? (
              <>
                <strong className="block text-white">No user session found</strong>
                Please{" "}
                <Link href="/register" className="text-neon-teal underline">
                  register
                </Link>{" "}
                first before chatting.
              </>
            ) : (
              alert.message
            )}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-0 bg-gradient-to-b from-transparent to-background/95 px-3 pt-4 pb-2">
        <form
          onSubmit={send}
          className="flex min-h-16 items-center gap-1 rounded-xl border border-neon-teal/30 bg-background/90 px-2 shadow-[0_0_25px_rgb(92_36_255/25%)]"
        >
          <input
            ref={fileInput}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            className="flex size-10 items-center justify-center rounded-lg text-neon-teal hover:bg-neon-pink/15 hover:text-neon-pink"
            aria-label="Attach a file"
          >
            <Paperclip className="size-5" />
          </button>
          {file && (
            <span className="flex max-w-40 items-center gap-1 rounded-full bg-card px-2 py-1 text-xs text-neon-teal">
              <FileText className="size-3.5 shrink-0" aria-hidden="true" />
              <span className="truncate">{file.name}</span>
              <button
                type="button"
                onClick={() => {
                  setFile(null);
                  if (fileInput.current) {
                    fileInput.current.value = "";
                  }
                }}
                aria-label="Remove attachment"
              >
                <X className="size-3.5" />
              </button>
            </span>
          )}
          <input
            ref={textInput}
            name="text_input"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={pending}
            placeholder="Message PwnGPT…"
            aria-label="Message"
            autoComplete="off"
            className="min-w-0 flex-1 bg-transparent px-3 py-4 text-lg text-white outline-none placeholder:text-white/45 disabled:opacity-60"
          />
          <ShimmerButton
            type="submit"
            disabled={pending || input.trim() === ""}
            aria-label="Send message"
            className="size-11 rounded-lg px-0 py-0"
          >
            <SendHorizontal className="size-5" />
          </ShimmerButton>
        </form>
        <Footer />
      </div>
    </div>
  );
}
