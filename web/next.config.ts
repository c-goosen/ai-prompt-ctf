import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async redirects() {
    // /chat was an alias of /ctf in the FastAPI app.
    return [{ source: "/chat", destination: "/ctf", permanent: true }];
  },
};

export default nextConfig;
