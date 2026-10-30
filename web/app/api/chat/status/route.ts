import { NextResponse, type NextRequest } from "next/server";

import { authorizedIdentity } from "@/lib/identity";
import { identityCookies } from "@/lib/request-identity";
import { isRunning } from "@/lib/runs";
import { isValidSessionId } from "@/lib/validation";

/**
 * Whether the caller's agent run is still going, so a chat page opened
 * mid-run can wait for the reply. `?session=` as for /api/chat/history.
 */
export async function GET(request: NextRequest) {
  const identity = await authorizedIdentity(identityCookies(request));
  if (!identity) {
    return NextResponse.json({ running: false });
  }
  const requested = request.nextUrl.searchParams.get("session");
  const sessionId = isValidSessionId(requested) ? requested : identity.sessionId;
  return NextResponse.json({ running: await isRunning(identity.username, sessionId) });
}
