import { NextResponse, type NextRequest } from "next/server";

import { COOKIE_NAMES, IDENTITY_COOKIE_OPTIONS } from "@/lib/identity";
import { ADK_APP_NAME } from "@/lib/config";
import { registerPlayer } from "@/lib/register";

/** JSON registration API (the register page uses a Server Action instead). */
export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch (error) {
    return NextResponse.json(
      { detail: `Invalid request: ${(error as Error).message}` },
      { status: 400 },
    );
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return NextResponse.json({ detail: "Invalid request: expected an object" }, { status: 400 });
  }
  const { username, session_id } = body as Record<string, unknown>;

  const outcome = await registerPlayer({
    username,
    sessionId: session_id,
    presentedToken: request.cookies.get(COOKIE_NAMES.playerToken)?.value,
  });
  if (!outcome.ok) {
    return NextResponse.json({ detail: outcome.error, message: outcome.detail }, { status: outcome.status });
  }

  const response = NextResponse.json({
    status: "success",
    message: "User registered successfully",
    user_id: outcome.username,
    session_id: outcome.sessionId,
    app_name: ADK_APP_NAME,
    ...(outcome.newToken ? { player_token: outcome.newToken } : {}),
  });
  response.cookies.set(COOKIE_NAMES.username, outcome.username, IDENTITY_COOKIE_OPTIONS);
  response.cookies.set(COOKIE_NAMES.sessionId, outcome.sessionId, IDENTITY_COOKIE_OPTIONS);
  if (outcome.newToken) {
    response.cookies.set(COOKIE_NAMES.playerToken, outcome.newToken, IDENTITY_COOKIE_OPTIONS);
  }
  return response;
}
