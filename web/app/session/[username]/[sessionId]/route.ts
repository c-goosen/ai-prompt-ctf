import { NextResponse, type NextRequest } from "next/server";

import { AdkError, getSession } from "@/lib/adk";
import { COOKIE_NAMES, verifyOwner } from "@/lib/identity";
import { isValidSessionId } from "@/lib/validation";

/** Whether the caller's own ADK session exists (owner-checked). */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ username: string; sessionId: string }> },
) {
  const { username, sessionId } = await params;
  if (!isValidSessionId(sessionId)) {
    return NextResponse.json({ detail: "Invalid session ID" }, { status: 400 });
  }
  const cookieIdentity = request.cookies.get(COOKIE_NAMES.username)?.value;
  const token = request.cookies.get(COOKIE_NAMES.playerToken)?.value;
  if (cookieIdentity !== username || !(await verifyOwner(username, token))) {
    return NextResponse.json({ detail: "You do not have access to this session" }, { status: 403 });
  }

  try {
    const session = await getSession(username, sessionId);
    if (session === null) {
      return NextResponse.json({ status: "success", exists: false, message: "Session not found" });
    }
    return NextResponse.json({ status: "success", exists: true, session });
  } catch (error) {
    const status = error instanceof AdkError && error.status ? error.status : 500;
    return NextResponse.json(
      { detail: { status: "error", message: "Failed to get session", error: (error as Error).message } },
      { status },
    );
  }
}
