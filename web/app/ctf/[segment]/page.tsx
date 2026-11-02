import { notFound } from "next/navigation";

import { ChatPage } from "@/components/chat/chat-page";
import { isValidSessionId } from "@/lib/validation";

export const dynamic = "force-dynamic";

/**
 * An older chat link, /ctf/<session id>; the chat rewrites it to
 * /ctf/<username>/<session id>. The folder is [segment] because the router
 * needs one name for this position, which holds the username in the longer URL.
 */
export default async function SessionChatPage({ params }: { params: Promise<{ segment: string }> }) {
  const { segment: sessionId } = await params;
  if (!isValidSessionId(sessionId)) {
    notFound();
  }
  return <ChatPage sessionId={sessionId} />;
}
