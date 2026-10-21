import { describe, expect, it } from "vitest";

import { useTestDb } from "@/test/helpers";

import { authorizedIdentity, claimOrVerifyUsername, hashToken, newToken, verifyOwner } from "./identity";

describe("username ownership", () => {
  useTestDb();

  it("mints a token on first claim and verifies it later", async () => {
    const first = await claimOrVerifyUsername("alice", undefined);
    expect(first.allowed).toBe(true);
    expect(first.newToken).toMatch(/^[A-Za-z0-9_-]{43}$/);

    const again = await claimOrVerifyUsername("alice", first.newToken!);
    expect(again).toEqual({ allowed: true, newToken: null });
    expect(await verifyOwner("alice", first.newToken!)).toBe(true);
  });

  it("rejects a takeover without the owner token", async () => {
    await claimOrVerifyUsername("alice", undefined);
    expect(await claimOrVerifyUsername("alice", undefined)).toEqual({ allowed: false, newToken: null });
    expect(await claimOrVerifyUsername("alice", "guessed")).toEqual({ allowed: false, newToken: null });
  });

  it("hashes tokens like Python's hashlib.sha256().hexdigest()", async () => {
    expect(await hashToken("abc")).toBe("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    expect(newToken()).not.toBe(newToken());
  });

  it("authorizes only when the token matches the claimed username", async () => {
    const { newToken: aliceToken } = await claimOrVerifyUsername("alice", undefined);
    const { newToken: bobToken } = await claimOrVerifyUsername("bob", undefined);
    const base = { username: "alice", sessionId: "alice-session" };
    expect(await authorizedIdentity({ ...base, playerToken: aliceToken! })).toEqual(base);
    expect(await authorizedIdentity({ ...base, playerToken: bobToken! })).toBeNull();
    expect(await authorizedIdentity({ ...base })).toBeNull();
    expect(
      await authorizedIdentity({ username: "alice", sessionId: "../../bob/x", playerToken: aliceToken! }),
    ).toBeNull();
  });
});
