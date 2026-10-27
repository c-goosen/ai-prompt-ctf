import { ChatScreen } from "@/components/chat/chat-screen";
import { getSessionHistory } from "@/lib/adk";
import { currentPlayer } from "@/lib/session";
import { listSkills } from "@/lib/skills";

export const dynamic = "force-dynamic";

export default async function ChatPage() {
  const player = await currentPlayer();
  const [history, skills] = player
    ? await Promise.all([
        getSessionHistory(player.username, player.sessionId),
        listSkills(player.username).catch(() => []),
      ])
    : [[], []];
  return (
    <ChatScreen
      initialMessages={history}
      initialSkills={skills.map(({ name, description }) => ({ name, description }))}
      registered={player !== null}
    />
  );
}
