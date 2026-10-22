import { Markdown } from "@/components/markdown";
import { PageShell } from "@/components/page-shell";
import faq from "@/content/faq.generated";

export const metadata = { title: "FAQ · PwnGPT" };

export default function FaqPage() {
  return (
    <PageShell title="FAQ">
      <div className="rounded-2xl border border-neon-pink/30 bg-card/60 p-5 md:p-8">
        <Markdown>{faq}</Markdown>
      </div>
    </PageShell>
  );
}
