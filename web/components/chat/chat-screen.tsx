"use client";

import { FileText, Paperclip, SendHorizontal, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";

import { ChatBubble, MarkdownBubble } from "@/components/chat/chat-bubble";
import { WelcomeMessages } from "@/components/chat/welcome";
import { Footer } from "@/components/footer";
import { MessageEnter } from "@/components/watermelon/inline-toast";
import { LabeledProgressIndicator } from "@/components/watermelon/labeled-progress-indicator";
import { ShimmerButton } from "@/components/watermelon/shimmer-button";
import type { ChatMessage } from "@/lib/events";
import { allCommands, commandSuggestions, completeCommand, type CommandInfo, type Skill } from "@/lib/slash";
import { cn } from "@/lib/utils";

const LOADER_LABELS = ["Thinking…", "Checking guardrails…", "Calling tools…", "Sending…"];
// Markdown/text is for `/skills install` with a SKILL.md.
const ACCEPT = ".pdf,.json,.md,.txt,image/*,audio/*,application/pdf,application/json,text/markdown,text/plain";

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
  initialSkills,
  registered,
}: {
  initialMessages: ChatMessage[];
  /** For autocomplete; refreshed after each `/skills` command. */
  initialSkills: Array<Pick<Skill, "name" | "description">>;
  registered: boolean;
}) {
  const [entries, setEntries] = useState<Entry[]>(() => toEntries(initialMessages, false));
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [alert, setAlert] = useState<Alert | null>(registered ? null : { kind: "register" });
  const [skills, setSkills] = useState(initialSkills);
  const [selected, setSelected] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const textInput = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const turnRef = useRef<HTMLDivElement>(null);

  // The turn started by the last prompt sent this visit; history before it renders as usual.
  let turnStart = entries.length;
  for (let i = entries.length - 1; i >= 0; i--) {
    if (entries[i].role === "user") {
      if (entries[i].fresh) {
        turnStart = i;
      }
      break;
    }
  }
  const turnId = entries[turnStart]?.id;

  const suggestions = dismissed || pending ? [] : commandSuggestions(input, allCommands(skills));
  const active = suggestions[Math.min(selected, suggestions.length - 1)];

  async function loadSkills() {
    try {
      const response = await fetch("/api/skills");
      if (response.ok) {
        setSkills((await response.json()).skills);
      }
    } catch {
      // Autocomplete only; commands still work without it.
    }
  }

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, []);


  // A new prompt scrolls up to the top of the view, and its reply fills in below it.
  useEffect(() => {
    if (turnId !== undefined) {
      turnRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [turnId]);

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
        const replies = toEntries(body.messages as ChatMessage[], true);
        // /newsession: the old conversation belongs to the previous session.
        setEntries((prev) => (body.newSession ? replies : [...prev, ...replies]));
      }
    } catch {
      setAlert({ kind: "error", message: "Could not reach the server. Please try again." });
    } finally {
      if (/^\/skills\b/i.test(text)) {
        void loadSkills();
      }
      setPending(false);
      textInput.current?.focus();
    }
  }

  function changeInput(value: string) {
    setInput(value);
    setSelected(0);
    setDismissed(false);
  }

  function pick(command: CommandInfo) {
    changeInput(completeCommand(command));
    textInput.current?.focus();
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!active) {
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      setSelected((suggestions.indexOf(active) + step + suggestions.length) % suggestions.length);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setDismissed(true);
    } else if (event.key === "Tab" || (event.key === "Enter" && input.trim() !== `/${active.name}`)) {
      // Enter runs a fully typed command; otherwise it completes, like Tab.
      event.preventDefault();
      pick(active);
    }
  }

  const renderEntry = (entry: Entry) => (
    <MessageEnter key={entry.id} animate={entry.fresh} index={entry.batchIndex}>
      <MarkdownBubble role={entry.role} text={entry.text} thoughts={entry.thoughts} />
    </MessageEnter>
  );
  const tail = (
    <>
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
    </>
  );

  return (
    <div className="flex flex-1 flex-col">
      <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-4 px-4 pt-6 pb-4 md:px-8" aria-live="polite">
        {entries.length === 0 && <WelcomeMessages />}
        {entries.slice(0, turnStart).map(renderEntry)}
        {turnId !== undefined ? (
          <div ref={turnRef} className="flex min-h-[calc(100dvh-14rem)] scroll-mt-18 flex-col gap-4 md:scroll-mt-6">
            {entries.slice(turnStart).map(renderEntry)}
            {tail}
          </div>
        ) : (
          tail
        )}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-0 bg-gradient-to-b from-transparent via-background/80 to-background px-4 pt-6 pb-1 md:px-8">
        <div className="mx-auto w-full max-w-4xl">
          {active && (
            <ul
              id="command-suggestions"
              role="listbox"
              aria-label="Commands"
              className="mb-2 max-h-64 overflow-y-auto rounded-xl border border-neon-teal/30 bg-background/95 p-1 shadow-[0_0_25px_rgb(92_36_255/25%)]"
            >
              {suggestions.map((command) => (
                <li
                  key={command.name}
                  id={`command-${command.name.replace(" ", "-")}`}
                  role="option"
                  aria-selected={command === active}
                  onMouseDown={(event) => {
                    // Keep focus in the input.
                    event.preventDefault();
                    pick(command);
                  }}
                  className={cn(
                    "flex cursor-pointer flex-col gap-0.5 rounded-lg px-3 py-1.5 sm:flex-row sm:items-baseline sm:gap-3",
                    command === active ? "bg-neon-pink/15" : "hover:bg-neon-pink/10",
                  )}
                >
                  <code className="shrink-0 font-mono text-sm text-neon-teal">{command.usage}</code>
                  <span className="truncate text-sm text-white/70">{command.description}</span>
                </li>
              ))}
            </ul>
          )}
          <form
            onSubmit={send}
            className="flex min-h-14 items-center gap-1 rounded-2xl border border-neon-teal/30 bg-card/90 px-2 shadow-[0_0_25px_rgb(92_36_255/25%)] backdrop-blur transition-colors focus-within:border-neon-pink/60"
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
              onChange={(event) => changeInput(event.target.value)}
              onKeyDown={onKeyDown}
              disabled={pending}
              placeholder="Message PwnGPT… (type / for commands)"
              aria-label="Message"
              role="combobox"
              aria-expanded={active !== undefined}
              aria-controls="command-suggestions"
              aria-autocomplete="list"
              aria-activedescendant={active ? `command-${active.name.replace(" ", "-")}` : undefined}
              autoComplete="off"
              className="min-w-0 flex-1 bg-transparent px-2 py-3.5 text-base text-white outline-none placeholder:text-white/45 disabled:opacity-60"
            />
            <ShimmerButton
              type="submit"
              disabled={pending || input.trim() === ""}
              aria-label="Send message"
              className="size-10 rounded-xl px-0 py-0"
            >
              <SendHorizontal className="size-5" />
            </ShimmerButton>
          </form>
          <Footer />
        </div>
      </div>
    </div>
  );
}
