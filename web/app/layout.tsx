import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";

import { Sidebar } from "@/components/sidebar";
import { siteConfig } from "@/lib/config";
import { cn } from "@/lib/utils";

import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "PwnGPT",
  description: "A LLM prompt injection CTF",
  keywords: ["pwngpt", "pwn", "gpt", "ctf", "prompt injection", "cgoosen"],
};

export const viewport: Viewport = {
  themeColor: "#050014",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={cn("dark font-sans", geist.variable)}>
      <body className="min-h-dvh md:h-dvh md:overflow-hidden">
        <div className="flex min-h-dvh flex-col md:h-dvh md:flex-row">
          <Sidebar discordUrl={siteConfig.discordUrl()} />
          <main className="min-w-0 flex-1 bg-gradient-to-b from-[#080323]/90 via-[#070828]/90 to-[#08061c]/95 md:h-dvh md:overflow-y-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
