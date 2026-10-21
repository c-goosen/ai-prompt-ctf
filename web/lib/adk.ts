import "server-only";

import { ADK_APP_NAME, adkApiUrl } from "./config";
import {
  eventToMessage,
  parseRunResponse,
  stripLeaderboardMarkers,
  type AdkEvent,
  type ChatMessage,
} from "./events";
import { redactPasswords } from "./redact";

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

async function adkFetch(url: string, init: RequestInit & { timeoutMs?: number } = {}) {
  const { timeoutMs = 30_000, ...rest } = init;
  try {
    return await fetch(url, { ...rest, signal: AbortSignal.timeout(timeoutMs) });
  } catch (error) {
    throw new AdkError(`Failed to reach ADK API: ${(error as Error).message}`);
  }
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

/** Send one user message (plus optional file) to the agent and parse the reply. */
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

  const response = await adkFetch(`${adkApiUrl()}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      appName: ADK_APP_NAME,
      userId,
      sessionId,
      newMessage: { role: "user", parts },
      streaming: false,
    }),
    timeoutMs: 60_000,
  });
  if (!response.ok) {
    throw new AdkError(`ADK /run failed: ${response.status}`, response.status);
  }
  return parseRunResponse(await response.json(), redactPasswords);
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
      .map((m) => ({ ...m, text: stripLeaderboardMarkers(m.text) }))
      .filter((m) => m.text !== "");
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
