/**
 * Tower-defence sprites for the quest map, drawn inline in the neon palette:
 * guard towers (one per level), the level 10 fortress, and the player's
 * gremlins. Decorative; the map's buttons carry the accessible labels.
 */

export type TowerState = "standing" | "siege" | "destroyed";

const TEAL = "#3cfcd1";
const PINK = "#ff2fd5";
const LAVENDER = "#a8a2ff";
const STONE = "#1c0937";
const DARK = "#060019";

const TOWER_COLORS: Record<Exclude<TowerState, "destroyed">, { stroke: string; fill: string; eye: string }> = {
  standing: { stroke: LAVENDER, fill: STONE, eye: TEAL },
  siege: { stroke: PINK, fill: "#29073f", eye: PINK },
};

/** The gremlins' flag, planted on a destroyed tower. */
function Flag({ x, y }: { x: number; y: number }) {
  return (
    <g>
      <line x1={x} y1={y} x2={x} y2={y - 16} stroke={LAVENDER} strokeWidth={1.5} strokeLinecap="round" />
      <path d={`M${x} ${y - 16} l9 3.5 -9 3.5 z`} fill={PINK} />
    </g>
  );
}

/** A guard tower: battlements, a scanning eye and a gate. 40x56. */
export function Tower({ state, className }: { state: TowerState; className?: string }) {
  if (state === "destroyed") {
    return (
      <svg viewBox="0 0 40 56" className={className} aria-hidden="true">
        <path
          d="M7 54V38l4-5 3 4 4-7 4 6 4-5 3 3 4 2v18z"
          fill={DARK}
          stroke={TEAL}
          strokeOpacity={0.7}
          strokeWidth={1.5}
          strokeLinejoin="round"
        />
        <path d="M13 54v-6a3 3 0 0 1 6 0v6" fill="none" stroke={TEAL} strokeOpacity={0.4} strokeWidth={1.2} />
        <rect x={2} y={50} width={5} height={4} rx={1} fill={STONE} stroke={TEAL} strokeOpacity={0.5} />
        <rect x={33} y={49} width={5} height={5} rx={1} fill={STONE} stroke={TEAL} strokeOpacity={0.5} />
        <Flag x={27} y={36} />
      </svg>
    );
  }
  const { stroke, fill, eye } = TOWER_COLORS[state];
  return (
    <svg viewBox="0 0 40 56" className={className} aria-hidden="true">
      <path
        d="M6 10h6v4h5v-4h6v4h5v-4h6v12h-2v32H8V22H6z"
        fill={fill}
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
      <line x1={8} y1={22} x2={32} y2={22} stroke={stroke} strokeOpacity={0.6} strokeWidth={1.2} />
      <circle cx={20} cy={31} r={4.5} fill={DARK} stroke={eye} strokeWidth={1.5} />
      <circle cx={20} cy={31} r={2} fill={eye} className="animate-pulse" />
      <path d="M15 54v-7a5 5 0 0 1 10 0v7" fill={DARK} stroke={stroke} strokeOpacity={0.7} strokeWidth={1.2} />
    </svg>
  );
}

/** The level 10 boss: a two-towered fortress with a gate. 72x60. */
export function Fortress({ state, className }: { state: TowerState; className?: string }) {
  if (state === "destroyed") {
    return (
      <svg viewBox="0 0 72 60" className={className} aria-hidden="true">
        <path
          d="M4 58V40l5-6 4 5 5-8 5 6 6-4 6 5 5-7 6 5 5-6 5 4 4 6 4-2v20z"
          fill={DARK}
          stroke={TEAL}
          strokeOpacity={0.7}
          strokeWidth={1.5}
          strokeLinejoin="round"
        />
        <path d="M29 58v-8a7 7 0 0 1 14 0v8" fill="none" stroke={TEAL} strokeOpacity={0.4} strokeWidth={1.2} />
        <Flag x={36} y={36} />
      </svg>
    );
  }
  const stroke = PINK;
  const fill = state === "siege" ? "#29073f" : STONE;
  return (
    <svg viewBox="0 0 72 60" className={className} aria-hidden="true">
      {/* Side towers */}
      <path d="M2 8h5v4h4V8h5v52H2z" fill={fill} stroke={stroke} strokeWidth={1.5} strokeLinejoin="round" />
      <path d="M56 8h5v4h4V8h5v52H56z" fill={fill} stroke={stroke} strokeWidth={1.5} strokeLinejoin="round" />
      {/* Keep */}
      <path
        d="M16 20h5v4h5v-4h5v4h5v-4h5v4h5v-4h5v40H16z"
        fill={fill}
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
      <circle cx={9} cy={22} r={2} fill={TEAL} className="animate-pulse" />
      <circle cx={63} cy={22} r={2} fill={TEAL} className="animate-pulse" />
      {/* Skull emblem */}
      <circle cx={36} cy={34} r={5} fill={DARK} stroke={stroke} strokeWidth={1.4} />
      <circle cx={34.2} cy={33.5} r={1.1} fill={stroke} />
      <circle cx={37.8} cy={33.5} r={1.1} fill={stroke} />
      <path d="M29 60v-9a7 7 0 0 1 14 0v9" fill={DARK} stroke={stroke} strokeOpacity={0.8} strokeWidth={1.2} />
    </svg>
  );
}

/** The gremlins' starting camp at Basecamp. 40x32. */
export function Camp({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 32" className={className} aria-hidden="true">
      <path d="M4 30L20 4l16 26z" fill={STONE} stroke={TEAL} strokeWidth={1.5} strokeLinejoin="round" />
      <path d="M16 30l4-10 4 10" fill={DARK} stroke={TEAL} strokeOpacity={0.7} strokeWidth={1.2} />
      <Flag x={20} y={5} />
    </svg>
  );
}

/** One gremlin: pointy ears, big pink eyes, stubby legs. Faces right. 24x24. */
export function Gremlin({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M5 9L1 3l7 3zM19 9l4-6-7 3z" fill={TEAL} stroke={DARK} strokeWidth={0.8} strokeLinejoin="round" />
      <ellipse cx={12} cy={13} rx={8} ry={7} fill={TEAL} stroke={DARK} strokeWidth={1} />
      <circle cx={9.5} cy={11.5} r={2.4} fill={DARK} />
      <circle cx={15.5} cy={11.5} r={2.4} fill={DARK} />
      <circle cx={10.2} cy={11.2} r={1.2} fill={PINK} />
      <circle cx={16.2} cy={11.2} r={1.2} fill={PINK} />
      <path d="M10 16.5q2 1.5 4 0" fill="none" stroke={DARK} strokeWidth={1} strokeLinecap="round" />
      <path d="M8.5 19.5v3M15.5 19.5v3" stroke={TEAL} strokeWidth={2} strokeLinecap="round" />
    </svg>
  );
}
