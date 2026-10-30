// Cloudflare Workers build: `pnpm build:cf` / `pnpm deploy:cf`.
// The default vite.config.ts builds the standalone Node server (Docker).
import { fileURLToPath } from "node:url";

import { cloudflare } from "@cloudflare/vite-plugin";
import tailwindcss from "@tailwindcss/vite";
import vinext from "vinext";
import { defineConfig } from "vite";

export default defineConfig({
  resolve: {
    alias: {
      "@/lib/platform": fileURLToPath(new URL("./lib/platform.cloudflare.ts", import.meta.url)),
    },
  },
  plugins: [
    vinext(),
    tailwindcss(),
    cloudflare({
      // Not in the project root: see the note at the top of that file.
      configPath: "./cloudflare/wrangler.jsonc",
      viteEnvironment: {
        name: "rsc",
        childEnvironments: ["ssr"],
      },
    }),
  ],
});
