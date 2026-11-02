import { notFound } from "next/navigation";

import { ChatPage } from "@/components/chat/chat-page";
import { isValidSessionId, isValidUsername } from "@/lib/validation";

export const dynamic = "force-dynamic";

/** A bookmarkable chat session: /ctf/<username>/<session id>. */
export default async function PlayerSessionChatPage({
  params,
}: {
  params: Promise<{ segment: string; sessionId: string }>;
}) {
  const { segment: username, sessionId } = await params;
  if (!isValidUsername(username) || !isValidSessionId(sessionId)) {
    notFound();
  }
  return <ChatPage username={username} sessionId={sessionId} />;
}
