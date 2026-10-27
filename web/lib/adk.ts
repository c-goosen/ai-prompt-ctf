import "server-only";

import { ADK_APP_NAME, adkApiUrl, adkRunMaxMs, adkRunTimeoutMs } from "./config";
import {
  eventToMessage,
  FALLBACK_MESSAGE,
  parseRunResponse,
  stripMessageMarkers,
  type AdkEvent,
  type ChatMessage,
} from "./events";
import { redactPasswords } from "./redact";
import { collapseCommandMarker } from "./slash";

/**
 * Client for the Python ADK API server (ctf/agents). Callers must pass a
 * username/session id that already passed validation and the ownership
 * check, because both are interpolated into the URL path.
 */

const sessionUrl = (userId: string, sessionId: string) =>
  `${adkApiUrl()}/apps/${ADK_APP_NAME}/users/${encodeURIComponent(userId)}/sessions/${encodeURIComponent(sessionId)}`;

export class AdkError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "AdkError";
  }
}

/** Status of the AdkError for a run that timed out. */
const TIMEOUT_STATUS = 504;
/** Status of the AdkError for an ADK API that can't be reached. */
const UNREACHABLE_STATUS = 502;

async function adkFetch(url: string, init: RequestInit & { timeoutMs?: number } = {}) {
  const { timeoutMs = 30_000, signal: given, ...rest } = init;
  const signal = given ?? AbortSignal.timeout(timeoutMs);
  try {
    return await fetch(url, { ...rest, signal });
  } catch (error) {
    if (signal.aborted) {
      throw signal.reason instanceof AdkError
        ? signal.reason
        : new AdkError("Timed out waiting for the ADK API", TIMEOUT_STATUS);
    }
    throw new AdkError(`Failed to reach ADK API: ${(error as Error).message}`, UNREACHABLE_STATUS);
  }
}

/** The reply shown to the player when an agent run fails. */
export function adkErrorReply(error: unknown): string {
  const status = error instanceof AdkError ? error.status : undefined;
  if (status === TIMEOUT_STATUS) {
    return "Sorry, the agent took too long to respond. Please try again.";
  }
  if (status === UNREACHABLE_STATUS) {
    return "Sorry, the agent is unavailable right now. Please try again shortly.";
  }
  return "Sorry, there was an error processing your request. Please try again.";
}

/**
 * Aborts a run once nothing has arrived for `idleMs`, or after `maxMs` in
 * total. Streamed tokens count as progress, so a slow model that is still
 * answering isn't cut off.
 */
function runDeadline(idleMs: number, maxMs: number) {
  const controller = new AbortController();
  const expire = () => controller.abort(new AdkError("The agent run timed out", TIMEOUT_STATUS));
  let idle = setTimeout(expire, idleMs);
  const total = setTimeout(expire, maxMs);
  return {
    signal: controller.signal,
    progress() {
      clearTimeout(idle);
      idle = setTimeout(expire, idleMs);
    },
    clear() {
      clearTimeout(idle);
      clearTimeout(total);
    },
  };
}

/** Create the ADK session (empty state). Throws AdkError on HTTP failure. */
export async function createSession(userId: string, sessionId: string): Promise<void> {
  const response = await adkFetch(sessionUrl(userId, sessionId), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  if (!response.ok) {
    throw new AdkError(
      `Failed to create session: ${response.status} ${await response.text()}`,
      response.status,
    );
  }
}

export async function getSession(
  userId: string,
  sessionId: string,
): Promise<Record<string, unknown> | null> {
  const response = await adkFetch(sessionUrl(userId, sessionId), { timeoutMs: 10_000 });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new AdkError(`Failed to get session: ${response.status}`, response.status);
  }
  return (await response.json()) as Record<string, unknown>;
}

async function ensureSession(userId: string, sessionId: string): Promise<void> {
  if ((await getSession(userId, sessionId)) === null) {
    await createSession(userId, sessionId);
  }
}

export interface Upload {
  data: ArrayBuffer;
  name: string;
  mimeType: string;
}

/** Same allow-list as before: PDF, JSON, images and audio. */
export function isAllowedUpload(mimeType: string): boolean {
  const lowered = mimeType.toLowerCase();
  return ["image/", "audio/", "application/pdf", "application/json"].some((prefix) =>
    lowered.startsWith(prefix),
  );
}

function toBase64(data: ArrayBuffer): string {
  const bytes = new Uint8Array(data);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

/**
 * Send one user message (plus optional file) to the agent and parse the reply.
 * If the run fails partway, the messages so far are returned followed by an
 * error reply; it throws AdkError only when there is nothing to show.
 */
export async function runAgent(
  userId: string,
  sessionId: string,
  message: string,
  upload?: Upload,
): Promise<ChatMessage[]> {
  await ensureSession(userId, sessionId);

  const parts: Array<Record<string, unknown>> = [{ text: message }];
  if (upload) {
    parts.push({
      inline_data: {
        mime_type: upload.mimeType || "application/octet-stream",
        data: toBase64(upload.data),
        display_name: upload.name,
      },
    });
  }

  // /run_sse with token streaming rather than /run: /run sends nothing until
  // the agent finishes, and Node's fetch gives up after 5 minutes without
  // response headers, which a CPU-bound Ollama model easily exceeds.
  const deadline = runDeadline(adkRunTimeoutMs(), adkRunMaxMs());
  try {
    const response = await adkFetch(`${adkApiUrl()}/run_sse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        appName: ADK_APP_NAME,
        userId,
        sessionId,
        newMessage: { role: "user", parts },
        streaming: true,
      }),
      signal: deadline.signal,
    });
    if (!response.ok || !response.body) {
      throw new AdkError(`ADK /run_sse failed: ${response.status}`, response.status);
    }
    const { events, error } = await readFinalEvents(response.body, deadline);
    const messages = parseRunResponse(events, redactPasswords);
    if (!error) {
      return messages;
    }
    const partial = messages.filter((message) => message !== FALLBACK_MESSAGE);
    if (partial.length === 0) {
      throw error;
    }
    console.error("ADK run failed partway:", error.message);
    return [...partial, { role: "assistant", text: adkErrorReply(error) }];
  } finally {
    deadline.clear();
  }
}

/**
 * Collect the complete events of an ADK SSE stream, skipping partial token
 * chunks. A failure ends the stream early but keeps the events before it.
 */
async function readFinalEvents(
  body: ReadableStream<Uint8Array>,
  deadline: ReturnType<typeof runDeadline>,
): Promise<{ events: AdkEvent[]; error?: AdkError }> {
  const events: AdkEvent[] = [];
  const handle = (line: string) => {
    if (!line.startsWith("data:")) {
      return;
    }
    const event = JSON.parse(line.slice("data:".length)) as AdkEvent & { partial?: boolean; error?: string };
    if (event.error) {
      throw new AdkError(`ADK run failed: ${event.error}`);
    }
    if (!event.partial) {
      events.push(event);
    }
  };

  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for await (const chunk of body) {
      deadline.progress();
      buffer += decoder.decode(chunk, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      lines.forEach(handle);
    }
    handle(buffer + decoder.decode());
  } catch (error) {
    if (deadline.signal.aborted && deadline.signal.reason instanceof AdkError) {
      return { events, error: deadline.signal.reason };
    }
    return {
      events,
      error: error instanceof AdkError ? error : new AdkError(`ADK stream failed: ${(error as Error).message}`),
    };
  }
  return { events };
}

/** Chat history for a session; empty when it doesn't exist or ADK is down. */
export async function getSessionHistory(
  userId: string,
  sessionId: string,
): Promise<ChatMessage[]> {
  try {
    const session = await getSession(userId, sessionId);
    const events = (session?.events as AdkEvent[] | undefined) ?? [];
    return events
      .map((event) => eventToMessage(event, redactPasswords))
      .filter((m): m is ChatMessage => m !== null)
      .map(stripMessageMarkers)
      .map((m) => (m.role === "user" ? { ...m, text: collapseCommandMarker(m.text) } : m))
      .filter((m) => m.text !== "" || m.thoughts);
  } catch (error) {
    console.warn("Could not retrieve session history:", (error as Error).message);
    return [];
  }
}

/** ADK health: /health, falling back to /list-apps on older servers. */
export async function checkAdkHealth(): Promise<{ healthy: boolean; error?: string }> {
  try {
    const health = await adkFetch(`${adkApiUrl()}/health`, { timeoutMs: 5_000 });
    if (health.ok) {
      return { healthy: true };
    }
    const apps = await adkFetch(`${adkApiUrl()}/list-apps`, { timeoutMs: 2_000 });
    return { healthy: apps.status < 500 };
  } catch (error) {
    return { healthy: false, error: (error as Error).message };
  }
}
