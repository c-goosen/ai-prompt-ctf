import { CheckCircle2, Info, Repeat, TriangleAlert } from "lucide-react";
import Link from "next/link";

import { PageShell } from "@/components/page-shell";
import { CopyConfirm } from "@/components/watermelon/copy-confirm";
import { ShimmerButton } from "@/components/watermelon/shimmer-button";
import { currentPlayer } from "@/lib/session";

import { RegisterForm } from "./register-form";

export const dynamic = "force-dynamic";
export const metadata = { title: "Register · PwnGPT" };

export default async function RegisterPage({
  searchParams,
}: {
  searchParams: Promise<{ force_new?: string; registered?: string }>;
}) {
  const player = await currentPlayer();
  const params = await searchParams;
  const forceNew = params.force_new === "1";
  const showForm = forceNew || player === null;

  if (player && params.registered === "1") {
    return (
      <PageShell title="Registration Successful">
        <div role="status" className="flex gap-3 rounded-xl border border-green-500/50 bg-green-500/10 p-4 text-card-foreground">
          <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-green-400" aria-hidden="true" />
          <div className="flex flex-col gap-1">
            <h2 className="font-semibold text-white">User registered successfully!</h2>
            <p>
              <strong>User ID:</strong> {player.username}
            </p>
            <p className="flex flex-wrap items-center gap-2">
              <strong>Session/Quicket code ID:</strong>
              <code className="rounded bg-background/80 px-1.5 py-0.5 font-mono text-sm">{player.sessionId}</code>
              <CopyConfirm value={player.sessionId} />
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Your session has been saved as a cookie. You can now start chatting!
            </p>
          </div>
        </div>
        <ShimmerButton asChild className="self-start">
          <Link href="/ctf">Start Chatting</Link>
        </ShimmerButton>
      </PageShell>
    );
  }

  return (
    <PageShell title="Register User">
      {player && (
        <div className="flex flex-col gap-3">
          <div className="flex gap-3 rounded-xl border border-neon-teal/40 bg-neon-teal/10 p-4 text-card-foreground">
            <Info className="mt-0.5 size-5 shrink-0 text-neon-teal" aria-hidden="true" />
            <div>
              <h2 className="font-semibold text-white">You already have a session!</h2>
              <p>User: {player.username}</p>
              <p>Session: {player.sessionId}</p>
            </div>
          </div>
          {!forceNew && (
            <div className="flex flex-col gap-2 md:flex-row md:items-center">
              <Link
                href="/register?force_new=1"
                prefetch={false}
                className="self-start rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground hover:opacity-90"
              >
                Create a new session
              </Link>
              <p className="text-sm text-muted-foreground">
                Need a fresh conversation thread? Generate a brand new session ID.
              </p>
            </div>
          )}
        </div>
      )}

      {showForm && (
        <>
          <div className="flex gap-3 rounded-xl border border-amber-400/40 bg-amber-400/10 p-4 text-card-foreground">
            {player ? (
              <Repeat className="mt-0.5 size-5 shrink-0 text-amber-300" aria-hidden="true" />
            ) : (
              <TriangleAlert className="mt-0.5 size-5 shrink-0 text-amber-300" aria-hidden="true" />
            )}
            <div>
              {player ? (
                <>
                  <h2 className="font-semibold text-white">Create another session</h2>
                  <p>Your existing cookies stay intact—we&apos;ll register a fresh session below.</p>
                </>
              ) : (
                <>
                  <h2 className="font-semibold text-white">No session found</h2>
                  <p>Please register to create a new session.</p>
                  <p>
                    If you are at Bsides Cape Town 2025, to qualify for the CTF, you need to register with your
                    Quicket code.
                  </p>
                </>
              )}
            </div>
          </div>
          <RegisterForm defaultUsername={player?.username} />
        </>
      )}
    </PageShell>
  );
}
