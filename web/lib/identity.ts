import "server-only";

import { getDb, timestampParam } from "./db";
import { isValidSessionId, isValidUsername } from "./validation";

/**
 * Username ownership, ported from ctf/leaderboard.py
 * (claim_or_verify_username / verify_owner).
 *
 * The first registration of a username mints a random token; only its
 * sha256 is stored. The token goes back to the browser as an httpOnly
 * cookie and must be presented to use that username again. Tokens and
 * hashes are interchangeable with ones the Python code created.
 */

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Equivalent of Python's secrets.token_urlsafe(32). */
export function newToken(): string {
  return base64Url(crypto.getRandomValues(new Uint8Array(32)));
}

export async function hashToken(token: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token));
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

export type ClaimResult =
  | { allowed: true; newToken: string | null }
  | { allowed: false; newToken: null };

/**
 * Claim a username on first registration, or verify ownership on a repeat
 * registration. newToken is only set when a fresh token was minted.
 */
export async function claimOrVerifyUsername(
  username: string,
  presentedToken: string | undefined,
): Promise<ClaimResult> {
  if (!username) {
    return { allowed: false, newToken: null };
  }
  const db = await getDb();
  const token = newToken();
  // Insert-if-absent, so two concurrent first registrations can't both win.
  const inserted = await db.query(
    `INSERT INTO player_identities (username, token_hash, created_at)
     VALUES ($1, $2, $3)
     ON CONFLICT (username) DO NOTHING
     RETURNING username`,
    [username, await hashToken(token), timestampParam(db, new Date())],
  );
  if (inserted.length > 0) {
    return { allowed: true, newToken: token };
  }
  if (presentedToken && (await verifyOwner(username, presentedToken))) {
    return { allowed: true, newToken: null };
  }
  return { allowed: false, newToken: null };
}

export async function verifyOwner(
  username: string,
  presentedToken: string | undefined,
): Promise<boolean> {
  if (!username || !presentedToken) {
    return false;
  }
  const db = await getDb();
  const rows = await db.query<{ token_hash: string }>(
    "SELECT token_hash FROM player_identities WHERE username = $1",
    [username],
  );
  return rows.length > 0 && rows[0].token_hash === (await hashToken(presentedToken));
}

export interface IdentityCookies {
  username?: string;
  sessionId?: string;
  playerToken?: string;
}

/**
 * Return the username only if the cookies prove ownership of it. The
 * anon_user_identity cookie alone is attacker-controlled; the httpOnly
 * player_token minted at registration is what proves ownership.
 */
export async function authorizedIdentity(
  cookies: IdentityCookies,
): Promise<{ username: string; sessionId: string } | null> {
  const { username, sessionId, playerToken } = cookies;
  if (!isValidUsername(username) || !isValidSessionId(sessionId)) {
    return null;
  }
  try {
    if (!(await verifyOwner(username, playerToken))) {
      return null;
    }
  } catch (error) {
    // Fail closed: without the database nobody's ownership can be proven.
    console.error("Ownership check failed:", (error as Error).message);
    return null;
  }
  return { username, sessionId };
}

export const COOKIE_NAMES = {
  username: "anon_user_identity",
  sessionId: "session_id",
  playerToken: "player_token",
} as const;

/** Identity cookies are only read server-side, so keep them away from JS. */
export const IDENTITY_COOKIE_OPTIONS = {
  httpOnly: true,
  sameSite: "lax",
  path: "/",
  secure: process.env.NODE_ENV === "production" && process.env.COOKIE_SECURE !== "0",
} as const;
