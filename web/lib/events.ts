/**
 * Convert ADK session events into chat messages, and strip the agent's
 * leaderboard markers for display. Pure: no I/O, so it is unit tested directly.
 */

export type ChatRole = "user" | "assistant" | "tool";

export interface ChatMessage {
  role: ChatRole;
  text: string;
}

/** Loose shape of an ADK event as returned by /run and the sessions API. */
export interface AdkEvent {
  author?: string;
  content?: {
    role?: string;
    text?: string;
    parts?: Array<string | AdkPart>;
  } | null;
}

interface AdkPart {
  text?: unknown;
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
  let hasPasswordSearch = false;

  for (const part of parts) {
    if (typeof part === "string") {
      chunks.push(part);
    } else if (!part || typeof part !== "object") {
      continue;
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
      roleHint = "tool";
    }
  }

  let text = chunks.filter(Boolean).join("\n").trim();
  if (!text) {
    text = String(content.text ?? "").trim();
  }
  if (!text) {
    return null;
  }
  if (hasPasswordSearch) {
    text = redact(text);
  }
  return { role: normalizeRole(roleHint), text };
}

export const FALLBACK_MESSAGE: ChatMessage = {
  role: "assistant",
  text: "Sorry, I couldn't process your request. Please try again.",
};

/** Messages for a /run response; never empty. */
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

/**
 * Remove leaderboard markers from model text. Display-only: credit is never
 * derived from model output, which a player can steer via prompt injection.
 */
export function stripLeaderboardMarkers(text: string): string {
  return text ? text.replace(LEADERBOARD_MARKER, "").trim() : text;
}
