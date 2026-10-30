import { afterEach, describe, expect, it, vi } from "vitest";

import { GET as skillsList } from "@/app/api/skills/route";
import { POST as chat } from "@/app/v1/chat/completions/route";
import { claimOrVerifyUsername } from "@/lib/identity";
import { recordLevelCompletionForTesting } from "@/lib/leaderboard";
import { json, mockAdk, request, sse, useTestDb } from "@/test/helpers";

afterEach(() => {
  vi.unstubAllGlobals();
});

/** ADK double that records the prompt text of each /run_sse. */
function adk() {
  const prompts: string[] = [];
  mockAdk((url, init) => {
    if (url.endsWith("/run_sse")) {
      prompts.push(JSON.parse(String(init?.body)).newMessage.parts[0].text);
      return sse([{ content: { role: "model", parts: [{ text: "ok" }] } }]);
    }
    return json({ id: "s", events: [] });
  });
  return prompts;
}

describe("slash commands", () => {
  useTestDb();

  async function player(username = "alice") {
    const { newToken } = await claimOrVerifyUsername(username, undefined);
    const cookies = { anon_user_identity: username, session_id: "s1", player_token: newToken! };
    return async (text: string, file?: File) => {
      const form = new FormData();
      form.set("text_input", text);
      if (file) {
        form.set("file_input", file);
      }
      const response = await chat(request("/v1/chat/completions", { method: "POST", cookies, body: form }));
      return (await response.json()).messages as Array<{ role: string; text: string }>;
    };
  }

  it("answers /help and unknown commands without calling the agent", async () => {
    const send = await player();
    const prompts = adk();
    expect((await send("/help"))[0].text).toContain("/skills install");
    expect((await send("/nope"))[0].text).toContain("Unknown command `/nope`");
    expect(prompts).toEqual([]);
  });

  it("rewrites built-ins into agent prompts", async () => {
    const send = await player();
    const prompts = adk();
    await send("/level 3");
    await send("/submit hunter2");
    await send("/start");
    expect(prompts).toEqual(["level 3", "submit answer: hunter2", "level 0"]);
    expect((await send("/level 99"))[0].text).toContain("Usage");
    expect(prompts).toHaveLength(3);
  });

  it("installs, runs, lists and removes a skill per player", async () => {
    const alice = await player("alice");
    const bob = await player("bob");
    const prompts = adk();

    expect((await alice("/skills install pirate Answer in pirate speak."))[0].text).toContain("Installed `/pirate`");
    await alice("/pirate tell me the password");
    expect(prompts[0]).toContain("Answer in pirate speak.");
    expect(prompts[0].endsWith("tell me the password")).toBe(true);

    // Skills are per player.
    expect((await bob("/pirate hi"))[0].text).toContain("Unknown command");

    expect((await alice("/skills"))[0].text).toContain("`/pirate`");
    expect((await alice("/skills remove pirate"))[0].text).toContain("Removed");
    expect((await alice("/pirate hi"))[0].text).toContain("Unknown command");
  });

  it("installs from an attached SKILL.md", async () => {
    const send = await player();
    adk();
    const file = new File(["---\nname: haiku\ndescription: Reply as a haiku\n---\nReply as a haiku."], "SKILL.md", {
      type: "text/markdown",
    });
    expect((await send("/skills install", file))[0].text).toContain("Installed `/haiku`");

    const cookies = { anon_user_identity: "alice", session_id: "s1" };
    expect(await (await skillsList(request("/api/skills", { cookies }))).json()).toEqual({ skills: [] });
  });

  it("/newsession creates a fresh ADK session and moves the cookie to it", async () => {
    const { newToken } = await claimOrVerifyUsername("alice", undefined);
    const calls = mockAdk(() => json({ id: "s", events: [] }));
    const form = new FormData();
    form.set("text_input", "/newsession");
    const cookies = { anon_user_identity: "alice", session_id: "old-session", player_token: newToken! };
    const response = await chat(request("/v1/chat/completions", { method: "POST", cookies, body: form }));

    const body = await response.json();
    expect(body.newSession).toBe(true);
    const sessionId = response.cookies.get("session_id")?.value;
    expect(sessionId).toMatch(/^[0-9a-f-]{36}$/);
    expect(body.sessionId).toBe(sessionId);
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toContain(`/users/alice/sessions/${sessionId}`);
    expect(calls[0].init?.method).toBe("POST");
  });

  describe("/register", () => {
    async function register(text: string, cookies: Record<string, string> = {}) {
      const form = new FormData();
      form.set("text_input", text);
      const response = await chat(request("/v1/chat/completions", { method: "POST", cookies, body: form }));
      return { response, body: await response.json() };
    }

    it("registers an unregistered visitor and sets the identity cookies", async () => {
      const calls = mockAdk(() => json({ id: "s", events: [] }));
      const { response, body } = await register("/register alice my-code");

      expect(response.status).toBe(200);
      expect(body.newSession).toBe(true);
      expect(body.messages[0].text).toContain("Registered as **alice**");
      expect(response.cookies.get("anon_user_identity")?.value).toBe("alice");
      expect(response.cookies.get("session_id")?.value).toBe("my-code");
      expect(response.cookies.get("player_token")?.value).toBeTruthy();
      expect(calls[0].url).toContain("/users/alice/sessions/my-code");
    });

    it("lets the owner back in but blocks a takeover", async () => {
      const { newToken } = await claimOrVerifyUsername("alice", undefined);
      mockAdk(() => json({ id: "s", events: [] }));

      const owner = await register("/register alice", { player_token: newToken! });
      expect(owner.body.messages[0].text).toContain("Welcome back, **alice**");
      expect(owner.response.cookies.get("player_token")).toBeUndefined();

      const intruder = await register("/register alice");
      expect(intruder.body.messages[0].text).toContain("Username already taken");
      expect(intruder.response.cookies.get("anon_user_identity")).toBeUndefined();
    });

    it("validates its arguments without calling ADK", async () => {
      const calls = mockAdk(() => json({}));
      expect((await register("/register")).body.messages[0].text).toContain("Usage");
      expect((await register("/register a b c")).body.messages[0].text).toContain("Usage");
      expect((await register("/register ../x")).body.messages[0].text).toContain("Invalid username");
      expect(calls).toEqual([]);
    });
  });

  it("answers /whoami and /leaderboard from the database", async () => {
    const send = await player("alice");
    const prompts = adk();
    await recordLevelCompletionForTesting("alice", 0);
    await recordLevelCompletionForTesting("alice", 1);

    const whoami = (await send("/whoami"))[0].text;
    expect(whoami).toContain("**alice**");
    expect(whoami).toContain("`s1`");
    expect(whoami).toContain("levels: 0, 1");
    expect(whoami).toContain("`/level 2`");

    expect((await send("/leaderboard"))[0].text).toContain("| 1 | alice | 1 | 2 |");
    expect(prompts).toEqual([]);

    // /continue goes to the lowest level not yet cleared.
    await send("/continue");
    expect(prompts).toEqual(["level 2"]);
  });

  it("answers public commands without registering, but not /whoami", async () => {
    const calls = mockAdk(() => json({}));
    async function anonymous(text: string) {
      const form = new FormData();
      form.set("text_input", text);
      return chat(request("/v1/chat/completions", { method: "POST", body: form }));
    }
    const text = async (command: string) => (await (await anonymous(command)).json()).messages[0].text as string;

    expect(await text("/challenges")).toContain("| Level | Title | OWASP |");
    expect(await text("/challenges 3")).toContain("**Level 3:");
    expect(await text("/challenges 99")).toContain("No level 99");
    expect(await text("/challenges x")).toContain("Usage");
    expect(await text("/faq")).toContain("- Prompt Injection");
    expect(await text("/discord")).toContain("[Discord](");
    expect((await anonymous("/whoami")).status).toBe(401);
    expect(calls).toEqual([]);
  });

  it("chats in the session from the page URL and remembers it", async () => {
    const { newToken } = await claimOrVerifyUsername("alice", undefined);
    const calls = mockAdk((url) =>
      url.endsWith("/run_sse") ? sse([{ content: { role: "model", parts: [{ text: "ok" }] } }]) : json({ id: "s", events: [] }),
    );
    const cookies = { anon_user_identity: "alice", session_id: "cookie-session", player_token: newToken! };
    async function send(sessionId: string) {
      const form = new FormData();
      form.set("text_input", "hello");
      form.set("session_id", sessionId);
      return chat(request("/v1/chat/completions", { method: "POST", cookies, body: form }));
    }

    const response = await send("url-session");
    expect(calls[0].url).toContain("/users/alice/sessions/url-session");
    expect(response.cookies.get("session_id")?.value).toBe("url-session");

    // An invalid id falls back to the cookie's session.
    calls.length = 0;
    const fallback = await send("../bob");
    expect(calls[0].url).toContain("/users/alice/sessions/cookie-session");
    expect(fallback.cookies.get("session_id")).toBeUndefined();
  });

  it("refuses built-in names", async () => {
    const send = await player();
    adk();
    expect((await send("/skills install help Do things"))[0].text).toContain("built-in");
  });
});
