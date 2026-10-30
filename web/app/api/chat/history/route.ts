import { NextResponse, type NextRequest } from "next/server";

import { getSessionHistory } from "@/lib/adk";
import { authorizedIdentity } from "@/lib/identity";
import { getPlayerLevels } from "@/lib/leaderboard";
import { identityCookies } from "@/lib/request-identity";
import { isValidSessionId } from "@/lib/validation";

/**
 * The caller's chat history and quest progress; empty unless the cookies
 * prove ownership. `?session=` picks one of the player's own sessions (the
 * chat page's /ctf/<session>); ADK keeps sessions per user, so it can't
 * reach anyone else's.
 */
export async function GET(request: NextRequest) {
  const identity = await authorizedIdentity(identityCookies(request));
  if (!identity) {
    return NextResponse.json({ messages: [] });
  }
  const requested = request.nextUrl.searchParams.get("session");
  const sessionId = isValidSessionId(requested) ? requested : identity.sessionId;
  const [messages, progress] = await Promise.all([
    getSessionHistory(identity.username, sessionId),
    getPlayerLevels(identity.username).catch(() => undefined),
  ]);
  return NextResponse.json({ messages, progress });
}
