import { NextResponse, type NextRequest } from "next/server";

import { isAllowedUpload, runAgent, type Upload } from "@/lib/adk";
import { stripMessageMarkers, type ChatMessage } from "@/lib/events";
import { authorizedIdentity } from "@/lib/identity";
import { identityCookies } from "@/lib/request-identity";

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

const errorMessage = (text: string): ChatMessage[] => [{ role: "assistant", text }];

/**
 * Send a chat message to the agent. multipart/form-data in
 * (text_input, optional file_input), JSON { messages } out.
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
  const text = form.get("text_input");
  if (typeof text !== "string" || text.trim() === "") {
    return NextResponse.json({ error: "bad_request", message: "Message is empty." }, { status: 400 });
  }

  let upload: Upload | undefined;
  const file = form.get("file_input");
  if (file instanceof File && file.size > 0) {
    if (!isAllowedUpload(file.type)) {
      return NextResponse.json(
        { error: "invalid_file", message: "Only PDF, JSON, image, and audio files are allowed." },
        { status: 415 },
      );
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      return NextResponse.json(
        { error: "file_too_large", message: "Files must be 10 MB or smaller." },
        { status: 413 },
      );
    }
    upload = { data: await file.arrayBuffer(), name: file.name, mimeType: file.type };
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
