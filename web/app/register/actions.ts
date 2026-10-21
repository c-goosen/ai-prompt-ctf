"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { COOKIE_NAMES, IDENTITY_COOKIE_OPTIONS } from "@/lib/identity";
import { registerPlayer } from "@/lib/register";

export type RegisterState =
  | { status: "idle" }
  | { status: "error"; error: string; detail: string; username: string };

export async function registerAction(_previous: RegisterState, formData: FormData): Promise<RegisterState> {
  const store = await cookies();
  const username = String(formData.get("username") ?? "").trim();
  const outcome = await registerPlayer({
    username,
    sessionId: String(formData.get("session_id") ?? "").trim() || undefined,
    presentedToken: store.get(COOKIE_NAMES.playerToken)?.value,
  });
  if (!outcome.ok) {
    return { status: "error", error: outcome.error, detail: outcome.detail, username };
  }

  store.set(COOKIE_NAMES.username, outcome.username, IDENTITY_COOKIE_OPTIONS);
  store.set(COOKIE_NAMES.sessionId, outcome.sessionId, IDENTITY_COOKIE_OPTIONS);
  if (outcome.newToken) {
    store.set(COOKIE_NAMES.playerToken, outcome.newToken, IDENTITY_COOKIE_OPTIONS);
  }
  // The page renders the success view from the (now verified) cookies.
  redirect("/register?registered=1");
}
