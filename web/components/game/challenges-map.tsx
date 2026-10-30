"use client";

import { QuestMap, type QuestLevel } from "@/components/game/quest-map";

/**
 * The tower map on the Challenges page: the horde keeps re-marching to the
 * player's tower, and picking a tower scrolls to that level's briefing.
 */
export function ChallengesMap({ levels, progress }: { levels: QuestLevel[]; progress: number[] | null }) {
  return (
    <QuestMap
      levels={levels}
      progress={progress}
      replay
      onSelect={(level) => {
        document.getElementById(`level-${level}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
        window.history.replaceState(window.history.state, "", `#level-${level}`);
      }}
    />
  );
}
