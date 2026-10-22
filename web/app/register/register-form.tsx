"use client";

import { LoaderCircle, TriangleAlert } from "lucide-react";
import { useActionState } from "react";

import { ShimmerButton } from "@/components/watermelon/shimmer-button";

import { registerAction, type RegisterState } from "./actions";

const inputClass =
  "w-full rounded-lg border border-input bg-background/60 px-3 py-2.5 text-white outline-none placeholder:text-white/60 focus-visible:border-neon-pink focus-visible:ring-2 focus-visible:ring-ring/40";

export function RegisterForm({ defaultUsername }: { defaultUsername?: string }) {
  const [state, formAction, pending] = useActionState<RegisterState, FormData>(registerAction, {
    status: "idle",
  });

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {state.status === "error" && (
        <div role="alert" className="flex gap-3 rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-card-foreground">
          <TriangleAlert className="mt-0.5 size-5 shrink-0 text-destructive" aria-hidden="true" />
          <div>
            <h2 className="font-semibold text-white">{state.error}</h2>
            <p className="text-sm">{state.detail}</p>
          </div>
        </div>
      )}
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-white">Username *</span>
        <input
          name="username"
          required
          maxLength={32}
          autoComplete="username"
          placeholder="Enter your username"
          defaultValue={state.status === "error" ? state.username : (defaultUsername ?? "")}
          className={inputClass}
        />
      </label>
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-white">Session ID (optional)</span>
        <input name="session_id" maxLength={64} placeholder="Leave empty to auto-generate" className={inputClass} />
        <span className="text-xs text-muted-foreground">If not provided, a unique session ID will be generated</span>
      </label>
      <ShimmerButton type="submit" disabled={pending} className="self-start">
        {pending && <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />}
        Register
      </ShimmerButton>
    </form>
  );
}
