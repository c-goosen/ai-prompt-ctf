import type { ReactNode } from "react";

import { Footer } from "@/components/footer";

/** Standard padded content page (FAQ, challenges, leaderboard, register). */
export function PageShell({
  title,
  description,
  children,
}: {
  title: string;
  description?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="mx-auto flex w-full flex-1 max-w-4xl flex-col gap-6 px-4 pt-6 pb-2 md:px-8 md:pt-10">
      <header className="flex flex-col gap-1.5 border-b border-neon-teal/20 pb-5">
        <h1 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">{title}</h1>
        {description && <p className="text-muted-foreground">{description}</p>}
      </header>
      {children}
      <Footer className="mt-auto pt-6" />
    </div>
  );
}
