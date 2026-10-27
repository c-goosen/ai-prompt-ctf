import { NextResponse, type NextRequest } from "next/server";

import { isAllowedUpload, runAgent, type Upload } from "@/lib/adk";
import { runCommand, type CommandResult } from "@/lib/commands";
import { stripMessageMarkers, type ChatMessage } from "@/lib/events";
import { authorizedIdentity, COOKIE_NAMES, IDENTITY_COOKIE_OPTIONS } from "@/lib/identity";
import { identityCookies } from "@/lib/request-identity";
import { parseSlashCommand } from "@/lib/slash";

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

const errorMessage = (text: string): ChatMessage[] => [{ role: "assistant", text }];

/**
 * Send a chat message to the agent. multipart/form-data in
 * (text_input, optional file_input), JSON { messages } out. Slash commands
 * are answered here or rewritten into a prompt first (lib/commands.ts).
 */
export async function POST(request: NextRequest) {
  // The identity cookie alone is forgeable, so require the owner token too.
  const identity = await authorizedIdentity(identityCookies(request));
  if (!identity) {
    return NextResponse.json(
      { error: "not_registered", message: "Please register first before chatting." },
      { status: 401 },
    );
  }

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return NextResponse.json({ error: "bad_request", message: "Expected form data." }, { status: 400 });
  }
  let text = form.get("text_input");
  if (typeof text !== "string" || text.trim() === "") {
    return NextResponse.json({ error: "bad_request", message: "Message is empty." }, { status: 400 });
  }
  const file = form.get("file_input");
  const attachment = file instanceof File && file.size > 0 ? file : undefined;

  const command = parseSlashCommand(text);
  if (command) {
    let result: CommandResult;
    try {
      // `/skills install` reads a SKILL.md attachment; every `/skills` command is answered here.
      result = await runCommand(identity.username, command, command.name === "skills" ? attachment : undefined);
    } catch (error) {
      console.error("Error running command:", (error as Error).message);
      return NextResponse.json({ messages: errorMessage("Sorry, that command failed. Please try again.") });
    }
    if (result.kind === "reply") {
      return NextResponse.json({ messages: [{ role: "assistant", text: result.text }] });
    }
    if (result.kind === "new-session") {
      const response = NextResponse.json({ messages: [{ role: "assistant", text: result.text }], newSession: true });
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
    messages = await runAgent(identity.username, identity.sessionId, text, upload);
  } catch (error) {
    console.error("Error calling ADK API:", (error as Error).message);
    return NextResponse.json({
      messages: errorMessage("Sorry, there was an error processing your request. Please try again."),
    });
  }

  // Display-only marker stripping. Leaderboard credit is recorded by the
  // agent's submit_answer_func, never derived from model text.
  return NextResponse.json({
    messages: messages
      .filter((message) => message.role !== "user")
      .map(stripMessageMarkers),
  });
}
