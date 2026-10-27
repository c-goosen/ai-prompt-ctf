import { ChatBubble } from "@/components/chat/chat-bubble";

const TOOLS: Array<[string, string]> = [
  ["hints_func", "Get hints for the current level"],
  ["submit_answer_func", "Submit your answer/flag to check if it's correct and progress to the next level"],
  ["help_search", "Search the web for help and documentation"],
  ["get_leaderboard_stats", "View leaderboard statistics"],
  ["password_search_func", "Search the database for passwords and secrets using RAG"],
];

/** Intro shown before the player has any history. */
export function WelcomeMessages() {
  return (
    <>
      <ChatBubble role="assistant">
        Welcome to the AI agentic prompt challenge. Try different approaches, use fighting words, and
        see if you can convince me to share a secret.
      </ChatBubble>
      <ChatBubble role="assistant">
        I remember our conversation, so experiment with multiple prompts. Helper functions like hints
        or submitting an answer are available when needed.
      </ChatBubble>
      <ChatBubble role="assistant">
        <p>I have the following tools available to you:</p>
        <ul className="my-2 list-disc space-y-1 pl-5">
          {TOOLS.map(([name, description]) => (
            <li key={name}>
              <code className="rounded bg-background/80 px-1 py-0.5 font-mono text-[0.85em]">{name}</code>:{" "}
              {description}
            </li>
          ))}
        </ul>
        <p>
          Some levels might have additional tools available to you, so check the level description for
          more information.
        </p>
      </ChatBubble>
      <ChatBubble role="assistant">
        Start the challenge by sending Hi. Then to move between levels, send &quot;I want to try level
        X&quot;. If you get an answer, submit it to the leaderboard by sending &quot;submit answer:
        Flag/Password&quot;.
      </ChatBubble>
      <ChatBubble role="assistant">
        Type <code className="rounded bg-background/80 px-1 py-0.5 font-mono text-[0.85em]">/</code> for
        commands such as <code className="font-mono">/level 3</code>, <code className="font-mono">/hint</code>{" "}
        and <code className="font-mono">/submit</code>, or{" "}
        <code className="font-mono">/help</code> to see them all and to install your own skills.
      </ChatBubble>
    </>
  );
}
