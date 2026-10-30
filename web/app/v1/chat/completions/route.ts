import { NextResponse, type NextRequest } from "next/server";

import { adkErrorReply, isAllowedUpload, type Upload } from "@/lib/adk";
import { PUBLIC_COMMANDS, runCommand, runPublicCommand, type CommandResult } from "@/lib/commands";
import { FALLBACK_MESSAGE, solvedLevels, stripMessageMarkers, type ChatMessage } from "@/lib/events";
import { authorizedIdentity, COOKIE_NAMES, IDENTITY_COOKIE_OPTIONS } from "@/lib/identity";
import { getPlayerLevels } from "@/lib/leaderboard";
import { RateLimiter, clientIp, describeLimit, limitFor } from "@/lib/rate-limit";
import { registerPlayer, setIdentityCookies } from "@/lib/register";
import { startRun } from "@/lib/runs";
import { identityCookies } from "@/lib/request-identity";
import { parseSlashCommand, type SlashCommand } from "@/lib/slash";
import { isValidSessionId } from "@/lib/validation";

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

const registerLimiter = new RateLimiter();

const errorMessage = (text: string): ChatMessage[] => [{ role: "assistant", text }];

/**
 * Send a chat message to the agent. multipart/form-data in
 * (text_input, optional file_input), JSON { messages } out. Slash commands
 * are answered here or rewritten into a prompt first (lib/commands.ts).
 */
export async function POST(request: NextRequest) {
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return NextResponse.json({ error: "bad_request", message: "Expected form data." }, { status: 400 });
  }
  const text = form.get("text_input");
  if (typeof text !== "string" || text.trim() === "") {
    return NextResponse.json({ error: "bad_request", message: "Message is empty." }, { status: 400 });
  }
  const file = form.get("file_input");
  const attachment = file instanceof File && file.size > 0 ? file : undefined;

  const command = parseSlashCommand(text);
  // /register and the public-content commands work without registering.
  if (command?.name === "register") {
    return registerFromChat(request, command.args);
  }
  if (command && PUBLIC_COMMANDS.has(command.name)) {
    return NextResponse.json({ messages: [{ role: "assistant", text: runPublicCommand(command).text }] });
  }

  // The identity cookie alone is forgeable, so require the owner token too.
  const identity = await authorizedIdentity(identityCookies(request));
  if (!identity) {
    return NextResponse.json(
      { error: "not_registered", message: "Please register first before chatting." },
      { status: 401 },
    );
  }

  // The chat page sends the session from its URL (/ctf/<session>). ADK keeps
  // sessions per user, so this can only reach the player's own sessions.
  const requested = form.get("session_id");
  const player = {
    username: identity.username,
    sessionId: isValidSessionId(requested) ? requested : identity.sessionId,
  };
  const response = await respond(player, text, command, attachment);
  // Remember it, so /ctf returns to the session last used (unless /newsession moved on).
  if (player.sessionId !== identity.sessionId && !response.cookies.has(COOKIE_NAMES.sessionId)) {
    response.cookies.set(COOKIE_NAMES.sessionId, player.sessionId, IDENTITY_COOKIE_OPTIONS);
  }
  return response;
}

async function respond(
  player: { username: string; sessionId: string },
  text: string,
  command: SlashCommand | null,
  attachment: File | undefined,
): Promise<NextResponse> {
  if (command) {
    let result: CommandResult;
    try {
      // `/skills install` reads a SKILL.md attachment; every `/skills` command is answered here.
      result = await runCommand(player, command, command.name === "skills" ? attachment : undefined);
    } catch (error) {
      console.error("Error running command:", (error as Error).message);
      return NextResponse.json({ messages: errorMessage("Sorry, that command failed. Please try again.") });
    }
    if (result.kind === "reply") {
      return NextResponse.json({ messages: [{ role: "assistant", text: result.text }] });
    }
    if (result.kind === "new-session") {
      const response = NextResponse.json({
        messages: [{ role: "assistant", text: result.text }],
        newSession: true,
        sessionId: result.sessionId,
      });
      response.cookies.set(COOKIE_NAMES.sessionId, result.sessionId, IDENTITY_COOKIE_OPTIONS);
      return response;
    }
    text = result.text;
  }

  let upload: Upload | undefined;
  if (attachment) {
    if (!isAllowedUpload(attachment.type)) {
      return NextResponse.json(
        { error: "invalid_file", message: "Only PDF, JSON, image, and audio files are allowed." },
        { status: 415 },
      );
    }
    if (attachment.size > MAX_UPLOAD_BYTES) {
      return NextResponse.json(
        { error: "file_too_large", message: "Files must be 10 MB or smaller." },
        { status: 413 },
      );
    }
    upload = { data: await attachment.arrayBuffer(), name: attachment.name, mimeType: attachment.type };
  }

  let messages: ChatMessage[];
  try {
    // Runs on even if the player navigates away or closes the tab (lib/runs.ts).
    messages = await startRun(player, text, upload);
  } catch (error) {
    console.error("Error calling ADK API:", (error as Error).message);
    return NextResponse.json({ messages: errorMessage(adkErrorReply(error)) });
  }

  // Display-only marker stripping. Leaderboard credit is recorded by the
  // agent's submit_answer_func, never derived from model text.
  const replies = messages
    .filter((message) => message.role !== "user")
    .map(stripMessageMarkers)
    .filter((message) => message.text !== "" || message.thoughts);
  return NextResponse.json({
    messages: replies.length > 0 ? replies : [FALLBACK_MESSAGE],
    // From the leaderboard, which only the agent's password check writes;
    // never from model text, which a player can steer.
    progress: await progressOf(player.username),
    // Levels whose password submit_answer_func accepted in this run, for the
    // chat's celebration. Level 0 is on the board from registration, so
    // progress alone can't show it being solved.
    solved: solvedLevels(messages),
  });
}

/** The player's cleared levels for the quest map, or undefined if the database is unavailable. */
async function progressOf(username: string): Promise<number[] | undefined> {
  try {
    return await getPlayerLevels(username);
  } catch (error) {
    console.error("Could not read player progress:", (error as Error).message);
    return undefined;
  }
}

/**
 * `/register <username> [session-id]`: the register page, from the chat.
 * Held to the register page's rate limit, since the proxy only sees this
 * route's (looser) one.
 */
async function registerFromChat(request: NextRequest, args: string) {
  const limit = limitFor("/register");
  if (!registerLimiter.hit(clientIp(request.headers), limit).allowed) {
    return NextResponse.json({
      messages: errorMessage(`Too many registrations (${describeLimit(limit)}). Please wait a moment.`),
    });
  }
  const [username, sessionId, ...extra] = args.split(/\s+/).filter(Boolean);
  if (!username || extra.length > 0) {
    return NextResponse.json({ messages: errorMessage("Usage: `/register <username> [session-id]`") });
  }

  const outcome = await registerPlayer({
    username,
    sessionId,
    presentedToken: request.cookies.get(COOKIE_NAMES.playerToken)?.value,
  });
  if (!outcome.ok) {
    return NextResponse.json({ messages: errorMessage(`**${outcome.error}.** ${outcome.detail}`) });
  }

  const greeting = outcome.newToken ? "Registered as" : "Welcome back,";
  const response = NextResponse.json({
    messages: [
      {
        role: "assistant",
        text: `${greeting} **${outcome.username}** (session \`${outcome.sessionId}\`). Type \`/help\` for commands, or just start chatting.`,
      },
    ],
    // A different player's session, so the client drops the old conversation.
    newSession: true,
    sessionId: outcome.sessionId,
    progress: await progressOf(outcome.username),
  });
  setIdentityCookies(response.cookies, outcome);
  return response;
}
