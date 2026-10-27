"use client";

import { LoaderCircle, TriangleAlert } from "lucide-react";
import { useActionState } from "react";

import { ShimmerButton } from "@/components/watermelon/shimmer-button";
import { SESSION_ID_RULES, USERNAME_RULES } from "@/lib/validation";

import { registerAction, type RegisterState } from "./actions";

const inputClass =
  "w-full rounded-lg border border-input bg-background/60 px-3 py-2.5 text-white outline-none transition-colors placeholder:text-white/40 hover:border-neon-teal/50 focus-visible:border-neon-pink focus-visible:ring-2 focus-visible:ring-ring/40 user-invalid:border-destructive";

// Mirrors lib/validation.ts so the browser can flag bad input before a round trip.
const USERNAME_INPUT_PATTERN = "[A-Za-z0-9_\\-][A-Za-z0-9_.\\-]{0,31}";
const SESSION_ID_INPUT_PATTERN = "[A-Za-z0-9\\-]{1,64}";

export function RegisterForm({ defaultUsername, isEvent }: { defaultUsername?: string; isEvent?: boolean }) {
  const [state, formAction, pending] = useActionState<RegisterState, FormData>(registerAction, {
    status: "idle",
  });

  return (
    <form action={formAction} className="flex flex-col gap-5">
      {state.status === "error" && (
        <div role="alert" className="flex gap-3 rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-card-foreground">
          <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" aria-hidden="true" />
          <div>
            <h2 className="font-semibold text-white">{state.error}</h2>
            <p className="text-sm">{state.detail}</p>
          </div>
        </div>
      )}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="username" className="text-sm font-medium text-white">
          Username
        </label>
        <input
          id="username"
          name="username"
          required
          autoFocus
          maxLength={32}
          pattern={USERNAME_INPUT_PATTERN}
          autoComplete="username"
          autoCapitalize="off"
          spellCheck={false}
          placeholder="e.g. prompt_ninja"
          title={USERNAME_RULES}
          aria-describedby="username-hint"
          defaultValue={state.status === "error" ? state.username : (defaultUsername ?? "")}
          className={inputClass}
        />
        <p id="username-hint" className="text-xs text-muted-foreground">
          Shown on the leaderboard. Up to 32 letters, digits, <kbd className="font-mono text-white">_ - .</kbd>
        </p>
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="session_id" className="text-sm font-medium text-white">
          Session ID / Quicket code <span className="font-normal text-muted-foreground">(optional)</span>
        </label>
        <input
          id="session_id"
          name="session_id"
          maxLength={64}
          pattern={SESSION_ID_INPUT_PATTERN}
          autoCapitalize="off"
          spellCheck={false}
          placeholder="Leave empty to auto-generate"
          title={SESSION_ID_RULES}
          aria-describedby="session-hint"
          className={`${inputClass} font-mono text-sm`}
        />
        <p id="session-hint" className="text-xs text-muted-foreground">
          {isEvent
            ? "At the event? Enter your Quicket code here. Otherwise leave it empty and we'll generate one."
            : "Leave empty and we'll generate a unique session ID."}
        </p>
      </div>

      <ShimmerButton type="submit" disabled={pending} className="w-full">
        {pending ? (
          <>
            <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
            Registering…
          </>
        ) : (
          "Register & start hacking"
        )}
      </ShimmerButton>
    </form>
  );
}
