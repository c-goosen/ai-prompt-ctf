import { cn } from "@/lib/utils";

export function Footer({ className }: { className?: string }) {
  return (
    <p className={cn("py-2 text-center text-[11px] text-muted-foreground/80", className)}>
      <span className="font-medium text-muted-foreground">PwnGPT V1</span> · All your AGI belong to us · Christo Goosen{" "}
      <a href="mailto:christogoosen@gmail.com" className="underline-offset-2 hover:text-neon-teal hover:underline">
        christogoosen@gmail.com
      </a>
    </p>
  );
}
