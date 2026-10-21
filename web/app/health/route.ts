import { NextResponse } from "next/server";

import { checkAdkHealth } from "@/lib/adk";
import { adkApiUrl } from "@/lib/config";

export const dynamic = "force-dynamic";

/** Frontend + ADK API status. "health" stays "ok" for existing probes. */
export async function GET() {
  const adk = await checkAdkHealth();
  return NextResponse.json({
    health: "ok",
    status: adk.healthy ? "healthy" : "degraded",
    services: {
      adk_api: {
        status: adk.healthy ? "healthy" : "unhealthy",
        url: adkApiUrl(),
        ...(adk.error ? { error: adk.error } : {}),
      },
    },
  });
}
