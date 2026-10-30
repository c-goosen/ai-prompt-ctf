import { notFound } from "next/navigation";

import { ChatPage } from "@/components/chat/chat-page";
import { isValidSessionId } from "@/lib/validation";

export const dynamic = "force-dynamic";

/** A bookmarkable chat session: /ctf/<session id>. */
export default async function SessionChatPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;
  if (!isValidSessionId(sessionId)) {
    notFound();
  }
  return <ChatPage sessionId={sessionId} />;
}
