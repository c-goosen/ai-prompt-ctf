import "server-only";

import { keepAlive } from "@/lib/platform";

import { runAgent, type Upload } from "./adk";
import { adkRunMaxMs } from "./config";
import { getDb, timestampParam, toDate } from "./db";
import type { ChatMessage } from "./events";

/**
 * Agent runs that outlive the request that started them. A player can send a
 * prompt and then navigate away or close the tab: the run carries on (nothing
 * aborts it when the browser disconnects), ADK keeps its events in the
 * session, and the chat page asks isRunning() to show "still working" and
 * poll until the reply lands.
 *
 * Runs are tracked in the database so every server instance agrees. A row
 * older than the run time limit is stale (e.g. the server restarted mid-run).
 */

/** Grace on top of ADK_RUN_MAX_MS before a leftover row counts as stale. */
const STALE_GRACE_MS = 60_000;

/**
 * Run the agent detached from the HTTP request: it finishes even if the
 * player leaves. Resolves with the agent's messages for a player still waiting.
 */
export function startRun(
  player: { username: string; sessionId: string },
  message: string,
  upload?: Upload,
): Promise<ChatMessage[]> {
  const run = (async () => {
    await markRun(player, true);
    try {
      return await runAgent(player.username, player.sessionId, message, upload);
    } finally {
      await markRun(player, false);
    }
  })();
  // Workers would otherwise cancel the run once the response is sent.
  keepAlive(run.catch(() => undefined));
  return run;
}

/** Whether an agent run is in progress for this player's session. */
export async function isRunning(username: string, sessionId: string): Promise<boolean> {
  try {
    const db = await getDb();
    const rows = await db.query<{ started_at: unknown }>(
      "SELECT started_at FROM agent_runs WHERE username = $1 AND session_id = $2",
      [username, sessionId],
    );
    const started = toDate(rows[0]?.started_at);
    return started !== null && Date.now() - started.getTime() < adkRunMaxMs() + STALE_GRACE_MS;
  } catch (error) {
    console.error("Could not check for a running agent:", (error as Error).message);
    return false;
  }
}

/** Record a run starting or finishing. Bookkeeping only: never fails the run. */
async function markRun({ username, sessionId }: { username: string; sessionId: string }, running: boolean) {
  try {
    const db = await getDb();
    if (running) {
      await db.query(
        `INSERT INTO agent_runs (username, session_id, started_at) VALUES ($1, $2, $3)
         ON CONFLICT (username, session_id) DO UPDATE SET started_at = excluded.started_at`,
        [username, sessionId, timestampParam(db, new Date())],
      );
    } else {
      await db.query("DELETE FROM agent_runs WHERE username = $1 AND session_id = $2", [username, sessionId]);
    }
  } catch (error) {
    console.error("Could not record agent run state:", (error as Error).message);
  }
}
