import { ChatScreen } from "@/components/chat/chat-screen";
import challengesMarkdown from "@/content/challenges.generated";
import { getSessionHistory } from "@/lib/adk";
import { parseChallenges } from "@/lib/challenges";
import { getPlayerLevels, getRecentCompletions } from "@/lib/leaderboard";
import { isRunning } from "@/lib/runs";
import { currentPlayer } from "@/lib/session";
import { listSkills } from "@/lib/skills";

const levels = parseChallenges(challengesMarkdown).map(({ level, title }) => ({ level, title }));
const RECENT_SOLVES = 5;

/** Recent level completions, leaving out the level 0 entry every registration adds. */
async function recentSolves() {
  try {
    const recent = await getRecentCompletions(RECENT_SOLVES * 4);
    return recent
      .filter((solve) => solve.level > 0)
      .slice(0, RECENT_SOLVES)
      .map(({ username, level }) => ({ username, level }));
  } catch {
    return [];
  }
}

/**
 * The chat for /, /ctf and /ctf/<session>. Without a session in the URL it
 * shows the one in the player's cookie.
 */
export async function ChatPage({ sessionId }: { sessionId?: string }) {
  const player = await currentPlayer();
  if (!player) {
    return (
      <ChatScreen
        initialMessages={[]}
        initialSkills={[]}
        registered={false}
        sessionId={null}
        levels={levels}
        completedLevels={null}
        recentSolves={await recentSolves()}
      />
    );
  }
  const session = sessionId ?? player.sessionId;
  const [history, skills, completedLevels, solves, running] = await Promise.all([
    getSessionHistory(player.username, session),
    listSkills(player.username).catch(() => []),
    getPlayerLevels(player.username).catch(() => []),
    recentSolves(),
    isRunning(player.username, session),
  ]);
  return (
    <ChatScreen
      initialMessages={history}
      initialSkills={skills.map(({ name, description }) => ({ name, description }))}
      registered
      sessionId={session}
      levels={levels}
      completedLevels={completedLevels}
      recentSolves={solves}
      running={running}
    />
  );
}
