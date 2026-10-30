/**
 * Convert ADK session events into chat messages, and strip the agent's
 * leaderboard markers for display. Pure: no I/O, so it is unit tested directly.
 */

export type ChatRole = "user" | "assistant" | "tool";

export interface ChatMessage {
  role: ChatRole;
  text: string;
  /** The model's reasoning, from parts ADK marks as thoughts (include_thoughts). */
  thoughts?: string;
  /** The level submit_answer_func accepted in this event. Server-side only; see solvedLevels. */
  solved?: number;
}

/** Loose shape of an ADK event as returned by /run_sse and the sessions API. */
export interface AdkEvent {
  author?: string;
  content?: {
    role?: string;
    text?: string;
    parts?: Array<string | AdkPart>;
  } | null;
  /** Set by ADK when a model call failed, e.g. a thought-only turn. */
  errorCode?: string;
  errorMessage?: string;
}

interface AdkPart {
  text?: unknown;
  thought?: boolean;
  functionCall?: { name?: string; args?: unknown };
  functionResponse?: { name?: string; response?: unknown };
}

export function normalizeRole(role: string | undefined | null): ChatRole {
  const lowered = (role ?? "").toLowerCase();
  return lowered === "user" || lowered === "tool" ? lowered : "assistant";
}

function formatFunctionResponse(fnResp: NonNullable<AdkPart["functionResponse"]>): string {
  const name = fnResp.name ?? "unknown";
  let resp: unknown = fnResp.response ?? {};
  if (resp && typeof resp === "object" && !Array.isArray(resp)) {
    const values = Object.values(resp);
    if (values.length === 1 && typeof values[0] === "string" && values[0].includes("\n")) {
      resp = values[0];
    }
  }
  if (typeof resp === "string") {
    return `Tool response \`${name}\`\n\`\`\`\n${resp}\n\`\`\``;
  }
  return `Tool response \`${name}\`\n\`\`\`json\n${stableJson(resp)}\n\`\`\``;
}

/** JSON with sorted keys and 2-space indent (Python's sort_keys=True). */
function stableJson(value: unknown): string {
  return JSON.stringify(sortKeys(value), null, 2);
}

function sortKeys(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortKeys);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value as Record<string, unknown>)
        .sort()
        .map((key) => [key, sortKeys((value as Record<string, unknown>)[key])]),
    );
  }
  return value;
}

const ERROR_NOTICES: Record<string, string> = {
  MODEL_RETURNED_NO_CONTENT: "The model finished without an answer. Try rephrasing your message.",
  MAX_TOKENS: "The model ran out of tokens before it finished. Try a shorter request.",
  MALFORMED_FUNCTION_CALL: "The model made an invalid tool call. Please try again.",
};

/** What to tell the player about an ADK model error. */
function errorNotice(event: AdkEvent): string {
  const code = event.errorCode ?? "";
  return ERROR_NOTICES[code] ?? `The model failed (${code}): ${event.errorMessage ?? "unknown error"}`;
}

/**
 * Convert one ADK event into a message, or null if it has no text.
 * `redact` replaces level passwords in password_search_func output.
 */
export function eventToMessage(
  event: AdkEvent,
  redact: (text: string) => string = (text) => text,
): ChatMessage | null {
  const content = event.content ?? {};
  const parts = content.parts ?? [];
  let roleHint = content.role ?? event.author;
  const chunks: string[] = [];
  const thoughtChunks: string[] = [];
  let hasPasswordSearch = false;
  let solved: number | undefined;

  for (const part of parts) {
    if (typeof part === "string") {
      chunks.push(part);
    } else if (!part || typeof part !== "object") {
      continue;
    } else if (part.thought && part.text !== undefined) {
      thoughtChunks.push(String(part.text));
    } else if ("text" in part && part.text !== undefined) {
      chunks.push(String(part.text));
    } else if (part.functionCall) {
      const call = part.functionCall;
      chunks.push(
        `Function call \`${call.name ?? "unknown"}\`\n\`\`\`json\n${stableJson(call.args ?? {})}\n\`\`\``,
      );
      roleHint = "assistant";
    } else if (part.functionResponse) {
      chunks.push(formatFunctionResponse(part.functionResponse));
      if (part.functionResponse.name === "password_search_func") {
        hasPasswordSearch = true;
      }
      if (part.functionResponse.name === "submit_answer_func") {
        solved = correctLevel(part.functionResponse.response) ?? solved;
      }
      roleHint = "tool";
    }
  }

  let text = chunks.filter(Boolean).join("\n").trim();
  if (!text) {
    text = String(content.text ?? "").trim();
  }
  let thoughts = thoughtChunks.filter(Boolean).join("\n").trim();
  if (event.errorCode) {
    text = text ? `${text}\n\n${errorNotice(event)}` : errorNotice(event);
    roleHint = "assistant";
  }
  if (!text && !thoughts) {
    return null;
  }
  if (hasPasswordSearch) {
    text = redact(text);
    thoughts = redact(thoughts);
  }
  const message: ChatMessage = { role: normalizeRole(roleHint), text };
  if (thoughts) {
    message.thoughts = thoughts;
  }
  if (solved !== undefined) {
    message.solved = solved;
  }
  return message;
}

/**
 * The level in a "correct" leaderboard marker in submit_answer_func's
 * response. Only a tool response counts: the tool writes it after checking
 * the password, while a marker in model text can be steered by the player.
 */
function correctLevel(response: unknown): number | undefined {
  // ADK wraps a tool's string result as {"result": "..."}.
  const texts = typeof response === "string" ? [response] : Object.values(response ?? {});
  for (const text of texts) {
    if (typeof text !== "string") {
      continue;
    }
    for (const match of text.matchAll(LEADERBOARD_MARKER)) {
      try {
        const payload = JSON.parse(match[1]);
        if (payload.status === "correct" && Number.isInteger(payload.level)) {
          return payload.level;
        }
      } catch {
        // Not a marker the agent wrote.
      }
    }
  }
  return undefined;
}

/** The levels solved in a run's messages, lowest first. */
export function solvedLevels(messages: ChatMessage[]): number[] {
  const levels = messages.flatMap((message) => (message.solved === undefined ? [] : [message.solved]));
  return [...new Set(levels)].sort((a, b) => a - b);
}

export const FALLBACK_MESSAGE: ChatMessage = {
  role: "assistant",
  text: "Sorry, I couldn't process your request. Please try again.",
};

/** Messages for an agent run's events; never empty. */
export function parseRunResponse(
  events: unknown,
  redact?: (text: string) => string,
): ChatMessage[] {
  const messages = Array.isArray(events)
    ? events
        .map((event) => eventToMessage(event as AdkEvent, redact))
        .filter((m): m is ChatMessage => m !== null)
    : [];
  return messages.length > 0 ? messages : [FALLBACK_MESSAGE];
}

const LEADERBOARD_MARKER = /<!--LEADERBOARD:(\{.*?\})-->/g;

/** stripLeaderboardMarkers over a message's text and thoughts, dropping `solved`. */
export function stripMessageMarkers(message: ChatMessage): ChatMessage {
  const stripped: ChatMessage = { role: message.role, text: stripLeaderboardMarkers(message.text) };
  if (message.thoughts) {
    stripped.thoughts = stripLeaderboardMarkers(message.thoughts);
  }
  return stripped;
}

/**
 * Remove leaderboard markers from model text. Display-only: credit is never
 * derived from model output, which a player can steer via prompt injection.
 */
export function stripLeaderboardMarkers(text: string): string {
  return text ? text.replace(LEADERBOARD_MARKER, "").trim() : text;
}

export type MessageSection =
  | { kind: "text"; text: string }
  | { kind: "tool"; label: "Function call" | "Tool response"; name: string; body: string };

const TOOL_SECTION = /^(Function call|Tool response) `([^`\n]+)`\n(```[^\n]*\n[\s\S]*?\n```)/gm;

/**
 * Split a message into plain text and the tool calls/responses that
 * eventToMessage formats, so the chat can show tools collapsed.
 */
export function splitToolSections(text: string): MessageSection[] {
  const sections: MessageSection[] = [];
  let last = 0;
  for (const match of text.matchAll(TOOL_SECTION)) {
    const before = text.slice(last, match.index).trim();
    if (before) {
      sections.push({ kind: "text", text: before });
    }
    sections.push({
      kind: "tool",
      label: match[1] as "Function call" | "Tool response",
      name: match[2],
      body: match[3],
    });
    last = match.index + match[0].length;
  }
  const rest = text.slice(last).trim();
  if (rest) {
    sections.push({ kind: "text", text: rest });
  }
  return sections;
}
