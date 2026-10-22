import { NextResponse, type NextRequest } from "next/server";

import { getSessionHistory } from "@/lib/adk";
import { authorizedIdentity } from "@/lib/identity";
import { identityCookies } from "@/lib/request-identity";

/** The caller's chat history; empty unless the cookies prove ownership. */
export async function GET(request: NextRequest) {
  const identity = await authorizedIdentity(identityCookies(request));
  if (!identity) {
    return NextResponse.json({ messages: [] });
  }
  return NextResponse.json({
    messages: await getSessionHistory(identity.username, identity.sessionId),
  });
}
