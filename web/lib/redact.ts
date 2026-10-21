import "server-only";

import { levelPasswords } from "./config";

/** Replace every level password in text with [REDACTED]. */
export function redactPasswords(text: string, level?: number): string {
  if (!text) {
    return text;
  }
  const passwords = levelPasswords();
  const targets = level === undefined ? Object.values(passwords) : [passwords[level]];
  let result = text;
  for (const password of targets) {
    if (password) {
      result = result.split(password).join("[REDACTED]");
    }
  }
  return result;
}
