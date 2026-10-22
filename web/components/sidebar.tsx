"use client";

import { CircleHelp, Flag, MessageSquarePlus, MessagesSquare, Trophy, UserPlus } from "lucide-react";
import Image from "next/image";
import { usePathname } from "next/navigation";

import { FluidTabs, type FluidTab } from "@/components/watermelon/fluid-tabs";

const TABS: FluidTab[] = [
  { href: "/ctf", label: "Chat", icon: <MessageSquarePlus className="size-4" /> },
  { href: "/leaderboard", label: "Leaderboard", icon: <Trophy className="size-4" /> },
  { href: "/register", label: "Register", icon: <UserPlus className="size-4" /> },
  { href: "/faq", label: "FAQ", icon: <CircleHelp className="size-4" /> },
  { href: "/challenges", label: "Challenges", icon: <Flag className="size-4" /> },
];

function activeHref(pathname: string): string | null {
  if (pathname === "/" || pathname === "/chat") {
    return "/ctf";
  }
  return TABS.find((tab) => pathname === tab.href || pathname.startsWith(`${tab.href}/`))?.href ?? null;
}

export function Sidebar({ discordUrl }: { discordUrl: string }) {
  const pathname = usePathname();
  return (
    <aside className="flex w-full shrink-0 flex-col gap-3 border-sidebar-border bg-gradient-to-b from-[#060019] via-[#120528] to-[#1c0937] p-3 shadow-[0_0_40px_rgb(92_36_255/25%)] md:h-dvh md:w-1/4 md:max-w-80 md:overflow-y-auto md:border-r">
      <div className="flex justify-center">
        <Image
          src="/images/pwn_gpt_logo.webp"
          alt="PwnGPT: Agentic LLM CTF"
          width={640}
          height={960}
          priority
          className="h-auto w-24 md:w-full md:max-w-xs"
        />
      </div>
      <FluidTabs tabs={TABS} activeHref={activeHref(pathname)} className="grid grid-cols-2 md:flex">
        <a
          href={discordUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 rounded-xl border border-neon-teal/30 bg-card/60 px-3 py-2.5 text-sm font-medium tracking-wide text-card-foreground transition-colors hover:border-neon-pink/50 hover:bg-accent/80 md:px-4 md:py-3 md:text-[0.95rem]"
        >
          <MessagesSquare className="size-4 text-neon-teal" aria-hidden="true" />
          <span>Discord</span>
        </a>
      </FluidTabs>
    </aside>
  );
}
