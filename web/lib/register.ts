import "server-only";

import { AdkError, createSession } from "./adk";
import { getDb } from "./db";
import { claimOrVerifyUsername, hashToken } from "./identity";
import { ensureLeaderboardUser } from "./leaderboard";
import { isValidSessionId, isValidUsername, SESSION_ID_RULES, USERNAME_RULES } from "./validation";

export type RegisterOutcome =
  | { ok: true; username: string; sessionId: string; newToken: string | null }
  | { ok: false; status: 400 | 409 | 502; error: string; detail: string };

/**
 * Register a player and their ADK session. Shared by the register form's
 * Server Action and the JSON endpoint (app/api/register/route.ts).
 */
export async function registerPlayer(input: {
  username: unknown;
  sessionId?: unknown;
  presentedToken?: string;
}): Promise<RegisterOutcome> {
  const { username } = input;
  const sessionId =
    typeof input.sessionId === "string" && input.sessionId !== ""
      ? input.sessionId
      : crypto.randomUUID();

  if (!username) {
    return { ok: false, status: 400, error: "Username is required", detail: "Please provide a username" };
  }
  if (!isValidUsername(username)) {
    return { ok: false, status: 400, error: "Invalid username", detail: USERNAME_RULES };
  }
  if (!isValidSessionId(sessionId)) {
    return { ok: false, status: 400, error: "Invalid session ID", detail: SESSION_ID_RULES };
  }

  // First registration mints an ownership token; a returning player must
  // present the token they were given the first time.
  const claim = await claimOrVerifyUsername(username, input.presentedToken);
  if (!claim.allowed) {
    return {
      ok: false,
      status: 409,
      error: "Username already taken",
      detail:
        "That username is already registered. Please choose another, or continue in the browser where you originally registered it.",
    };
  }

  try {
    await createSession(username, sessionId);
  } catch (error) {
    // Don't leave the name claimed under a token nobody received.
    if (claim.newToken) {
      await releaseClaim(username, claim.newToken);
    }
    const message = error instanceof AdkError ? error.message : String(error);
    return { ok: false, status: 502, error: "Failed to connect to ADK API", detail: message };
  }

  await ensureLeaderboardUser(username);
  return { ok: true, username, sessionId, newToken: claim.newToken };
}

async function releaseClaim(username: string, token: string): Promise<void> {
  const db = await getDb();
  await db.query("DELETE FROM player_identities WHERE username = $1 AND token_hash = $2", [
    username,
    await hashToken(token),
  ]);
}
