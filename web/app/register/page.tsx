import { ArrowRight, CheckCircle2, KeyRound, MessageSquare, RefreshCw, Trophy, UserCheck, UserPlus } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { PageShell } from "@/components/page-shell";
import { CopyConfirm } from "@/components/watermelon/copy-confirm";
import { ShimmerButton } from "@/components/watermelon/shimmer-button";
import { currentPlayer } from "@/lib/session";

import { RegisterForm } from "./register-form";

export const dynamic = "force-dynamic";
export const metadata = { title: "Register · PwnGPT" };

const cardClass = "rounded-2xl border border-neon-teal/25 bg-card/70 p-5 shadow-[0_0_40px_rgb(92_36_255/12%)] backdrop-blur md:p-7";
const secondaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-neon-teal/35 px-5 py-3 text-sm font-medium text-white transition-colors hover:border-neon-teal hover:bg-neon-teal/10 outline-none focus-visible:ring-2 focus-visible:ring-ring";

function CredentialRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1.5 rounded-lg border border-neon-teal/15 bg-background/50 px-3 py-2.5">
      <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</span>
      <div className="flex items-center justify-between gap-3">
        <code className="min-w-0 truncate font-mono text-sm text-white" title={value}>
          {value}
        </code>
        <CopyConfirm value={value} className="shrink-0" />
      </div>
    </div>
  );
}

function CardHeading({ icon, title, children }: { icon: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="mb-5 flex items-start gap-3">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-neon-teal/10 text-neon-teal ring-1 ring-neon-teal/30">
        {icon}
      </span>
      <div className="flex flex-col gap-0.5">
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        {children && <p className="text-sm text-muted-foreground">{children}</p>}
      </div>
    </div>
  );
}

const STEPS = [
  { icon: <UserPlus className="size-4" />, title: "Pick a username", body: "It identifies you on the leaderboard." },
  { icon: <MessageSquare className="size-4" />, title: "Chat with the agents", body: "Trick each level into leaking its password." },
  { icon: <Trophy className="size-4" />, title: "Climb the board", body: "Every level you crack is scored live." },
];

function HowItWorks() {
  return (
    <aside aria-labelledby="how-it-works" className="flex flex-col gap-4 rounded-2xl border border-neon-pink/20 bg-gradient-to-br from-neon-pink/10 to-neon-violet/15 p-5">
      <h2 id="how-it-works" className="text-sm font-semibold tracking-wide text-neon-pink uppercase">
        How it works
      </h2>
      <ol className="flex flex-col gap-4">
        {STEPS.map((step, index) => (
          <li key={step.title} className="flex gap-3">
            <span className="relative flex size-8 shrink-0 items-center justify-center rounded-full bg-background/70 text-neon-teal ring-1 ring-neon-teal/40">
              {step.icon}
              <span className="sr-only">Step {index + 1}</span>
            </span>
            <div>
              <p className="text-sm font-medium text-white">{step.title}</p>
              <p className="text-sm text-muted-foreground">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </aside>
  );
}

function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
      {children}
      <HowItWorks />
    </div>
  );
}

export default async function RegisterPage({
  searchParams,
}: {
  searchParams: Promise<{ force_new?: string; registered?: string }>;
}) {
  const player = await currentPlayer();
  const params = await searchParams;
  const forceNew = params.force_new === "1";

  if (player && params.registered === "1") {
    return (
      <PageShell title="You're in" description="Your session is saved in this browser. Time to break some agents.">
        <Layout>
          <section role="status" className={cardClass}>
            <CardHeading icon={<CheckCircle2 className="size-5" />} title={`Welcome, ${player.username}!`}>
              Registration complete. Keep your session ID if you want to resume this conversation later.
            </CardHeading>
            <div className="flex flex-col gap-3">
              <CredentialRow label="Username" value={player.username} />
              <CredentialRow label="Session ID" value={player.sessionId} />
            </div>
            <ShimmerButton asChild className="mt-6 w-full">
              <Link href="/ctf">
                Start chatting <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </ShimmerButton>
          </section>
        </Layout>
      </PageShell>
    );
  }

  if (player && !forceNew) {
    return (
      <PageShell title="Register" description="You already have an active session in this browser.">
        <Layout>
          <section className={cardClass}>
            <CardHeading icon={<UserCheck className="size-5" />} title={`Signed in as ${player.username}`}>
              Pick up where you left off, or start a fresh conversation thread.
            </CardHeading>
            <CredentialRow label="Current session" value={player.sessionId} />
            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <ShimmerButton asChild className="flex-1">
                <Link href="/ctf">
                  Continue chatting <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </ShimmerButton>
              <Link href="/register?force_new=1" prefetch={false} className={`${secondaryButtonClass} flex-1`}>
                <RefreshCw className="size-4" aria-hidden="true" />
                New session
              </Link>
            </div>
          </section>
        </Layout>
      </PageShell>
    );
  }

  return (
    <PageShell
      title={player ? "Start a new session" : "Join the game"}
      description={
        player
          ? "Registers a fresh session ID. Your progress on the leaderboard is kept."
          : "Register to start chatting with the agents and get on the leaderboard."
      }
    >
      <Layout>
        <section className={cardClass}>
          <CardHeading
            icon={player ? <RefreshCw className="size-5" /> : <KeyRound className="size-5" />}
            title={player ? `New session for ${player.username}` : "Create your player"}
          >
            {player ? (
              <>
                Changed your mind?{" "}
                <Link href="/register" className="text-neon-teal underline-offset-2 hover:underline">
                  Keep the current session
                </Link>
              </>
            ) : (
              "Takes a few seconds, no email or password needed."
            )}
          </CardHeading>
          {!player && (
            <p className="mb-5 rounded-lg border border-amber-400/30 bg-amber-400/10 px-3 py-2.5 text-sm text-amber-100">
              <strong className="text-amber-300">At BSides Cape Town 2025?</strong> Enter your Quicket code as the session ID
              below to qualify for the CTF.
            </p>
          )}
          <RegisterForm defaultUsername={player?.username} isEvent={!player} />
        </section>
      </Layout>
    </PageShell>
  );
}
