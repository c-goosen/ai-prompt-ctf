import type { ReactNode } from "react";

import { Footer } from "@/components/footer";

/** Standard padded content page (FAQ, challenges, leaderboard, register). */
export function PageShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 md:p-8">
      <h1 className="text-2xl font-semibold tracking-tight text-white">{title}</h1>
      {children}
      <Footer />
    </div>
  );
}
