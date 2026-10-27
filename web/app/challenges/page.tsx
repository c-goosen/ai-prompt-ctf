import { Markdown } from "@/components/markdown";
import { PageShell } from "@/components/page-shell";
import challenges from "@/content/challenges.generated";
import { siteConfig } from "@/lib/config";

// Title comes from CTF_SUBTITLE at runtime, so don't prerender at build time.
export const dynamic = "force-dynamic";
export const metadata = { title: "Challenges · PwnGPT" };

export default function ChallengesPage() {
  return (
    <PageShell title={siteConfig.subtitle()}>
      <div className="rounded-2xl border border-neon-pink/30 bg-gradient-to-br from-neon-pink/20 to-neon-violet/30 p-5 md:p-8">
        <Markdown className="prose-h1:mt-10 prose-h1:mb-3 prose-h1:text-2xl first:prose-h1:mt-0 prose-h2:mt-4 prose-h2:mb-2 prose-h2:text-base prose-h2:text-neon-teal">{challenges}</Markdown>
      </div>
    </PageShell>
  );
}
