import "server-only";

import { cookies } from "next/headers";

import { authorizedIdentity, COOKIE_NAMES } from "./identity";

/** The verified player for the current request (page/Server Action), if any. */
export async function currentPlayer() {
  const store = await cookies();
  return authorizedIdentity({
    username: store.get(COOKIE_NAMES.username)?.value,
    sessionId: store.get(COOKIE_NAMES.sessionId)?.value,
    playerToken: store.get(COOKIE_NAMES.playerToken)?.value,
  });
}
