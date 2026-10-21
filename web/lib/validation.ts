/**
 * Usernames and session ids are interpolated into ADK URL paths, so restrict
 * them to characters that can't change the path (no "/", "..", "?" etc.).
 * Same patterns as the former ctf/frontend/utils.py.
 */
const USERNAME_PATTERN = /^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,31}$/;
const SESSION_ID_PATTERN = /^[A-Za-z0-9-]{1,64}$/;

export function isValidUsername(value: unknown): value is string {
  return typeof value === "string" && USERNAME_PATTERN.test(value);
}

export function isValidSessionId(value: unknown): value is string {
  return typeof value === "string" && SESSION_ID_PATTERN.test(value);
}

export const USERNAME_RULES =
  "Usernames are 1-32 characters: letters, digits, '_', '-' or '.', and may not start with '.'";
export const SESSION_ID_RULES = "Session IDs are 1-64 characters: letters, digits or '-'";
