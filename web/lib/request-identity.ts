import "server-only";

import type { NextRequest } from "next/server";

import { COOKIE_NAMES, type IdentityCookies } from "./identity";

export function identityCookies(request: NextRequest): IdentityCookies {
  return {
    username: request.cookies.get(COOKIE_NAMES.username)?.value,
    sessionId: request.cookies.get(COOKIE_NAMES.sessionId)?.value,
    playerToken: request.cookies.get(COOKIE_NAMES.playerToken)?.value,
  };
}
