import { ChatScreen } from "@/components/chat/chat-screen";
import { getSessionHistory } from "@/lib/adk";
import { currentPlayer } from "@/lib/session";

export const dynamic = "force-dynamic";

export default async function ChatPage() {
  const player = await currentPlayer();
  const history = player ? await getSessionHistory(player.username, player.sessionId) : [];
  return <ChatScreen initialMessages={history} registered={player !== null} />;
}
