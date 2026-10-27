"use client";

import {
  CircleHelp,
  Flag,
  Menu,
  MessageSquarePlus,
  MessagesSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Trophy,
  UserPlus,
  X,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, useSyncExternalStore, type MouseEvent } from "react";

import { FluidTabs, type FluidTab } from "@/components/watermelon/fluid-tabs";
import { cn } from "@/lib/utils";

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

// Desktop collapsed state, remembered per browser. Storage can be unavailable
// (private mode, blocked site data), so the in-memory value is the source of truth.
const COLLAPSED_KEY = "pwngpt:sidebar-collapsed";
const listeners = new Set<() => void>();
let collapsedPref: boolean | null = null;

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getCollapsed(): boolean {
  if (collapsedPref === null) {
    try {
      collapsedPref = localStorage.getItem(COLLAPSED_KEY) === "1";
    } catch {
      collapsedPref = false;
    }
  }
  return collapsedPref;
}

function setCollapsed(value: boolean) {
  collapsedPref = value;
  try {
    localStorage.setItem(COLLAPSED_KEY, value ? "1" : "0");
  } catch {
    // Not persisted; still applies for this visit.
  }
  listeners.forEach((listener) => listener());
}

const iconButtonClass =
  "flex size-10 shrink-0 items-center justify-center rounded-xl text-neon-teal outline-none transition-colors hover:bg-accent/70 hover:text-neon-pink focus-visible:ring-2 focus-visible:ring-ring";

export function Sidebar({ discordUrl }: { discordUrl: string }) {
  const pathname = usePathname();
  const collapsed = useSyncExternalStore(subscribe, getCollapsed, () => false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const tabs: FluidTab[] = [
    ...TABS,
    { href: discordUrl, label: "Discord", icon: <MessagesSquare className="size-4" />, external: true },
  ];
  const active = activeHref(pathname);

  useEffect(() => {
    if (!drawerOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDrawerOpen(false);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);

  // Following any link in the drawer closes it.
  const closeOnLink = (event: MouseEvent) => {
    if ((event.target as Element).closest("a")) {
      setDrawerOpen(false);
    }
  };

  return (
    <>
      {/* Mobile: top bar with a slide-in drawer. */}
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-sidebar-border bg-sidebar/90 px-3 backdrop-blur md:hidden">
        <Link href="/ctf" prefetch={false} className="flex items-center gap-2 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-ring">
          <Image src="/images/pwngpt-mark.svg" alt="" width={32} height={32} unoptimized className="size-8" />
          <span className="font-mono text-lg font-extrabold tracking-tight text-neon-pink">
            Pwn<span className="text-white">GPT</span>
          </span>
        </Link>
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className={iconButtonClass}
          aria-label="Open menu"
          aria-expanded={drawerOpen}
          aria-controls="mobile-nav"
        >
          <Menu className="size-5" />
        </button>
      </header>
      <div
        className={cn("fixed inset-0 z-40 md:hidden", !drawerOpen && "pointer-events-none")}
        inert={!drawerOpen}
      >
        <button
          type="button"
          tabIndex={-1}
          aria-label="Close menu"
          onClick={() => setDrawerOpen(false)}
          className={cn(
            "absolute inset-0 bg-background/70 backdrop-blur-sm transition-opacity",
            drawerOpen ? "opacity-100" : "opacity-0",
          )}
        />
        <div
          id="mobile-nav"
          role="dialog"
          aria-modal="true"
          aria-label="Menu"
          onClick={closeOnLink}
          className={cn(
            "absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col gap-4 overflow-y-auto border-r border-sidebar-border bg-gradient-to-b from-[#060019] via-[#120528] to-[#1c0937] p-3 shadow-[0_0_40px_rgb(92_36_255/35%)] transition-transform duration-200",
            drawerOpen ? "translate-x-0" : "-translate-x-full",
          )}
        >
          <div className="flex justify-end">
            <button type="button" onClick={() => setDrawerOpen(false)} className={iconButtonClass} aria-label="Close menu">
              <X className="size-5" />
            </button>
          </div>
          <Image
            src="/images/pwngpt-logo-hero.svg"
            alt="PwnGPT: Agentic LLM CTF"
            width={320}
            height={232}
            unoptimized
            className="h-auto w-full"
          />
          <FluidTabs tabs={tabs} activeHref={active} />
        </div>
      </div>

      {/* Desktop: rail that collapses to icons. */}
      <aside
        className={cn(
          "hidden h-dvh shrink-0 flex-col gap-4 overflow-x-hidden overflow-y-auto border-r border-sidebar-border bg-gradient-to-b from-[#060019] via-[#120528] to-[#1c0937] p-3 shadow-[0_0_40px_rgb(92_36_255/25%)] transition-[width] duration-200 md:flex",
          collapsed ? "w-[4.25rem]" : "w-64",
        )}
      >
        <Link
          href="/ctf"
          prefetch={false}
          className="flex justify-center rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {collapsed ? (
            <Image src="/images/pwngpt-mark.svg" alt="PwnGPT" width={40} height={40} unoptimized className="size-10" />
          ) : (
            <Image
              src="/images/pwngpt-logo-hero.svg"
              alt="PwnGPT: Agentic LLM CTF"
              width={320}
              height={232}
              priority
              unoptimized
              className="h-auto w-full"
            />
          )}
        </Link>
        <FluidTabs tabs={tabs} activeHref={active} collapsed={collapsed} />
        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "mt-auto flex h-10 items-center gap-3 rounded-xl text-sm text-muted-foreground outline-none transition-colors hover:bg-accent/70 hover:text-white focus-visible:ring-2 focus-visible:ring-ring",
            collapsed ? "justify-center" : "px-3",
          )}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
          title={collapsed ? "Expand sidebar" : undefined}
        >
          {collapsed ? <PanelLeftOpen className="size-5 shrink-0" /> : <PanelLeftClose className="size-5 shrink-0" />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </aside>
    </>
  );
}
