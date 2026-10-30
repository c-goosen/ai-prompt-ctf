// Turn content/*.md into TypeScript string modules (content/*.generated.ts).
// A plain module import works under both vinext (Vite) and `next build`,
// where Vite-only `?raw` imports would not, and needs no fs at runtime
// (Cloudflare Workers has none).
import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const contentDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "content");

for (const file of await readdir(contentDir)) {
  if (!file.endsWith(".md")) {
    continue;
  }
  const markdown = await readFile(path.join(contentDir, file), "utf8");
  const target = path.join(contentDir, file.replace(/\.md$/, ".generated.ts"));
  const source = `// Generated from content/${file} by scripts/build-content.mjs. Do not edit.\nexport default ${JSON.stringify(markdown)};\n`;
  await writeFile(target, source);
}
