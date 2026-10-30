export interface Challenge {
  level: number;
  title: string;
  /** The "## ..." line under the level heading, as markdown (may contain links). */
  subtitle: string | null;
  /** OWASP LLM Top 10 references, e.g. "LLM01: Prompt Injection". */
  owasp: string[];
  /** Remaining markdown body. */
  body: string;
}

export const DIFFICULTY = ["Warm-up", "Easy", "Medium", "Hard", "Insane"];

/** 1-based index into DIFFICULTY, spreading levels 0..finalLevel evenly. */
export function difficulty(level: number, finalLevel: number): number {
  return Math.min(DIFFICULTY.length, Math.floor((level / (finalLevel + 1)) * DIFFICULTY.length) + 1);
}

const LEVEL_HEADING = /^# Level (\d+):\s*(.+)$/;
const OWASP_LINE = /^(?:OWASP\s+)?(LLM\d{2}:.+)$/;

/** Split content/challenges.md into one entry per "# Level N: Title" section. */
export function parseChallenges(markdown: string): Challenge[] {
  const challenges: Challenge[] = [];
  let current: (Challenge & { lines: string[] }) | null = null;

  const flush = () => {
    if (current) {
      const { lines, ...challenge } = current;
      challenges.push({ ...challenge, body: lines.join("\n").trim() });
    }
  };

  for (const raw of markdown.split("\n")) {
    const line = raw.trimEnd();
    const heading = LEVEL_HEADING.exec(line);
    if (heading) {
      flush();
      current = { level: Number(heading[1]), title: heading[2].trim(), subtitle: null, owasp: [], body: "", lines: [] };
      continue;
    }
    if (!current) continue;
    const owasp = OWASP_LINE.exec(line.trim());
    if (owasp) {
      current.owasp.push(owasp[1].trim());
    } else if (line.startsWith("## ") && current.subtitle === null) {
      current.subtitle = line.slice(3).trim();
    } else {
      current.lines.push(line);
    }
  }
  flush();
  return challenges;
}
