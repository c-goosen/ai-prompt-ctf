"use client";

import { ArrowUp, ChevronDown, FileText, Plus, Trophy, X } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";

import { ChatBubble, MarkdownBubble } from "@/components/chat/chat-bubble";
import { ChatStart, RunMap, type LevelSummary, type RecentSolve } from "@/components/chat/chat-start";
import { Footer } from "@/components/footer";
import { LevelUp, type LevelUpEvent } from "@/components/game/level-up";
import { QuestMap } from "@/components/game/quest-map";
import { MessageEnter } from "@/components/watermelon/inline-toast";
import { LabeledProgressIndicator } from "@/components/watermelon/labeled-progress-indicator";
import type { ChatMessage } from "@/lib/events";
import { newlyCleared, rankFor, totalXp, xpFor } from "@/lib/progress";
import { allCommands, commandSuggestions, completeCommand, MAX_LEVEL, type CommandInfo, type Skill } from "@/lib/slash";
import { cn } from "@/lib/utils";

const LOADER_LABELS = ["Thinking…", "Checking guardrails…", "Calling tools…", "Sending…"];
const RESUME_POLL_MS = 3_000;
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
  sessionId: initialSessionId,
  levels,
  completedLevels,
  recentSolves,
  running = false,
}: {
  initialMessages: ChatMessage[];
  /** For autocomplete; refreshed after each `/skills` command. */
  initialSkills: Array<Pick<Skill, "name" | "description">>;
  registered: boolean;
  /** The session shown, kept in the URL as /ctf/<session> so it can be bookmarked. */
  sessionId: string | null;
  levels: LevelSummary[];
  /** Levels the player is on the board for; null when not registered. */
  completedLevels: number[] | null;
  recentSolves: RecentSolve[];
  /** An agent run for this session is still going (sent before the player left). */
  running?: boolean;
}) {
  const [entries, setEntries] = useState<Entry[]>(() => toEntries(initialMessages, false));
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(running);
  // Waiting on a run started on an earlier visit, rather than one sent from this page.
  const [resuming, setResuming] = useState(running);
  const [alert, setAlert] = useState<Alert | null>(registered ? null : { kind: "register" });
  const [skills, setSkills] = useState(initialSkills);
  const [sessionId, setSessionId] = useState(initialSessionId);
  const [selected, setSelected] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  const [progress, setProgress] = useState(completedLevels);
  const [levelUp, setLevelUp] = useState<LevelUpEvent | null>(null);
  // Back to the chat, where the agent has already moved the player to the next level.
  const closeLevelUp = useCallback(() => {
    setLevelUp(null);
    textInput.current?.focus();
  }, []);
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
  // Until the player says something, including right after /newsession's notice.
  const showWelcome = !entries.some((entry) => entry.role === "user");

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

  // Show the session in the address bar (/ and /ctf included) without a navigation.
  useEffect(() => {
    const path = sessionId ? `/ctf/${encodeURIComponent(sessionId)}` : null;
    if (path && window.location.pathname !== path) {
      window.history.replaceState(window.history.state, "", path);
    }
  }, [sessionId]);


  // Poll a run started before the page loaded, then show its reply.
  useEffect(() => {
    if (!resuming) {
      return;
    }
    const query = sessionId ? `?session=${encodeURIComponent(sessionId)}` : "";
    let stopped = false;
    const timer = setInterval(async () => {
      try {
        const status = await (await fetch(`/api/chat/status${query}`)).json();
        if (stopped || status.running) {
          return;
        }
        stopped = true;
        clearInterval(timer);
        const body = await (await fetch(`/api/chat/history${query}`)).json();
        if (Array.isArray(body.messages)) {
          setEntries(toEntries(body.messages as ChatMessage[], true));
        }
        if (Array.isArray(body.progress)) {
          updateProgress(body.progress as number[]);
        }
      } catch {
        // Try again on the next tick.
        return;
      }
      setResuming(false);
      setPending(false);
    }, RESUME_POLL_MS);
    return () => {
      stopped = true;
      clearInterval(timer);
    };
    // updateProgress reads the latest progress when the run ends; re-polling on each change isn't wanted.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resuming, sessionId]);

  // A new prompt scrolls up to the top of the view, and its reply fills in below it.
  useEffect(() => {
    if (turnId !== undefined) {
      turnRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [turnId]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void send(input.trim());
  }

  async function send(text: string) {
    if (!text || pending) {
      return;
    }
    const form = new FormData();
    form.set("text_input", text);
    if (sessionId) {
      form.set("session_id", sessionId);
    }
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
      } else if (!Array.isArray(body.messages) || body.messages.length === 0) {
        setAlert({ kind: "error", message: "The server sent an empty response. Please try again." });
      } else {
        const replies = toEntries(body.messages as ChatMessage[], true);
        // /newsession: the old conversation belongs to the previous session.
        setEntries((prev) => (body.newSession ? replies : [...prev, ...replies]));
        if (typeof body.sessionId === "string") {
          setSessionId(body.sessionId);
        }
        const solved = Array.isArray(body.solved) ? (body.solved as number[]) : [];
        if (Array.isArray(body.progress)) {
          updateProgress(body.progress as number[], { quiet: solved.length > 0 });
        }
        if (solved.length > 0) {
          celebrate(solved, Array.isArray(body.progress) ? (body.progress as number[]) : progress);
        }
      }
    } catch {
      setAlert({ kind: "error", message: "Could not reach the server. Please try again." });
    } finally {
      // /register can switch players, and skills are per player.
      if (/^\/(skills|register)\b/i.test(text)) {
        void loadSkills();
      }
      setPending(false);
      textInput.current?.focus();
    }
  }

  /**
   * Take the server's progress. A run that finished while the player was away
   * (no `solved` list) still celebrates levels cleared since the last.
   */
  function updateProgress(next: number[], { quiet = false } = {}) {
    const cleared = progress ? newlyCleared(progress, next) : [];
    if (!quiet && cleared.length > 0) {
      celebrate(cleared, next);
    }
    setProgress(next);
  }

  /** The siege for solved levels; the agent has already moved the player on to the next one. */
  function celebrate(solved: number[], next: number[] | null) {
    const before = progress ?? [];
    const after = next ?? before;
    // XP only for levels this run cleared for the first time.
    const firstClears = newlyCleared(before, after).filter((level) => solved.includes(level));
    const beforeRank = rankFor(totalXp(before)).title;
    const afterRank = rankFor(totalXp(after)).title;
    const upcoming = Math.max(...solved) + 1;
    setLevelUp({
      levels: solved,
      xp: firstClears.reduce((sum, level) => sum + xpFor(level), 0),
      rank: progress && afterRank !== beforeRank ? afterRank : undefined,
      next:
        upcoming > MAX_LEVEL
          ? null
          : { level: upcoming, title: levels.find((level) => level.level === upcoming)?.title ?? "" },
    });
  }

  function changeInput(value: string) {
    setInput(value);
    setSelected(0);
    setDismissed(false);
  }

  function prefill(text: string) {
    changeInput(text);
    textInput.current?.focus();
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
  const alertBox = alert && (
    <div role="alert" className="rounded-xl border border-neon-pink/40 bg-card/80 px-4 py-3 text-sm text-card-foreground">
      {alert.kind === "register" ? (
        <>
          <strong className="block text-white">No user session found</strong>
          Please{" "}
          <Link href="/register" className="text-neon-teal underline">
            register
          </Link>{" "}
          first before chatting, or type <code className="text-neon-teal">/register &lt;username&gt;</code>.
        </>
      ) : (
        alert.message
      )}
    </div>
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
      {alertBox}
    </>
  );

  const composer = (
    <div className="relative w-full">
      {active && (
        <ul
          id="command-suggestions"
          role="listbox"
          aria-label="Commands"
          className="absolute inset-x-0 bottom-full z-20 mb-2 max-h-64 overflow-y-auto rounded-2xl border border-neon-teal/30 bg-background/95 p-1 shadow-[0_0_25px_rgb(92_36_255/25%)]"
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
                "flex cursor-pointer flex-col gap-0.5 rounded-xl px-3 py-1.5 sm:flex-row sm:items-baseline sm:gap-3",
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
        onSubmit={onSubmit}
        className="flex w-full flex-col rounded-2xl border border-neon-teal/30 bg-card/90 text-white shadow-[0_0_25px_rgb(92_36_255/25%)] backdrop-blur transition-colors focus-within:border-neon-pink/60"
      >
        <input
          ref={fileInput}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <div className="flex px-4 py-3">
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
            className="min-w-0 flex-1 bg-transparent text-base/6 outline-none placeholder:text-white/45 disabled:opacity-60"
          />
        </div>
        <div className="flex items-center gap-4 px-3 pt-1.5 pb-3">
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            className="flex size-8 shrink-0 items-center justify-center rounded-full text-neon-teal outline-none hover:bg-neon-pink/15 hover:text-neon-pink focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Attach a file"
          >
            <Plus className="size-4" />
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
          <div className="flex-1" />
          <label className="relative flex items-center text-sm/5 text-muted-foreground">
            <span className="sr-only">Switch level</span>
            <select
              value=""
              disabled={pending}
              onChange={(event) => void send(`/level ${event.target.value}`)}
              className="field-sizing-content cursor-pointer appearance-none rounded-md bg-transparent py-1.5 pr-6 pl-2 outline-none hover:text-white focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="" disabled className="bg-card">
                Level
              </option>
              {levels.map(({ level, title }) => (
                <option key={level} value={level} className="bg-card text-white">
                  Level {level}: {title}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2 size-4" aria-hidden="true" />
          </label>
          <button
            type="submit"
            disabled={pending || input.trim() === ""}
            aria-label="Send message"
            className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-[0_0_20px_rgb(92_36_255/35%)] outline-none transition-shadow hover:shadow-[0_0_28px_rgb(255_47_213/45%)] focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-40 disabled:shadow-none"
          >
            <ArrowUp className="size-3.5" />
          </button>
        </div>
      </form>
    </div>
  );

  return (
    <div className="flex flex-1 flex-col md:pt-2 md:pr-2">
      <div className="relative flex flex-1 flex-col bg-card/40 shadow-[0_0_40px_rgb(92_36_255/20%)] md:rounded-t-xl md:border md:border-b-0 md:border-neon-teal/20">
        <header className="sticky top-14 z-10 flex h-14 items-center justify-end gap-4 px-3 md:top-0">
          {!showWelcome && (
            <div className="mr-auto">
              <QuestMap variant="compact" levels={levels} progress={progress} />
            </div>
          )}
          {progress && (
            <span
              className="flex items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-sm/6 text-amber-100"
              title={(() => {
                const rank = rankFor(totalXp(progress));
                return rank.next ? `${rank.next.xp - totalXp(progress)} XP to ${rank.next.title}` : "Top rank";
              })()}
            >
              <Trophy className="size-4 text-amber-300" aria-hidden="true" />
              <span className="font-semibold">{rankFor(totalXp(progress)).title}</span>
              <span className="hidden sm:inline">· {totalXp(progress).toLocaleString("en")} XP</span>
            </span>
          )}
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => void send("/newsession")}
              disabled={pending || !registered}
              className="flex items-center justify-center rounded-lg p-2 text-neon-teal outline-none transition-colors hover:bg-accent/70 hover:text-neon-pink focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
              aria-label="New session"
              title="New session"
            >
              <Plus className="size-4" />
            </button>
          </div>
        </header>

        {showWelcome ? (
          <ChatStart
            composer={composer}
            notice={
              <div className="flex flex-col gap-4" aria-live="polite">
                {entries.map(renderEntry)}
                {tail}
              </div>
            }
            levels={levels}
            progress={progress}
            recentSolves={recentSolves}
            onPrefill={prefill}
            onSend={(text) => void send(text)}
          />
        ) : (
          <>
            <div className="mx-auto w-full max-w-4xl px-4 pt-2 md:px-8">
              <RunMap levels={levels} progress={progress} onPrefill={prefill} onSend={(text) => void send(text)} />
            </div>
            <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-4 px-4 pt-4 pb-4 md:px-8" aria-live="polite">
              {entries.slice(0, turnStart).map(renderEntry)}
              {turnId !== undefined ? (
                <div ref={turnRef} className="flex min-h-[calc(100dvh-14rem)] scroll-mt-28 flex-col gap-4 md:scroll-mt-16">
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
                {composer}
                <Footer />
              </div>
            </div>
          </>
        )}
      </div>
      <LevelUp event={levelUp} onClose={closeLevelUp} />
    </div>
  );
}
