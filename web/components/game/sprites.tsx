/**
 * Quest map sprites in a cel-shaded cyberpunk cartoon style: flat colour, hard
 * shadows, ink outlines with a neon rim so they read on the dark background.
 * ICE towers (one per level), the final level's corp arcology, the runners'
 * rig, and the netrunner gremlins. Decorative; the map's buttons carry the
 * accessible labels.
 */

export type TowerState = "standing" | "siege" | "destroyed";

const TEAL = "#3cfcd1";
const PINK = "#ff2fd5";
const YELLOW = "#fcee0a";
const LAVENDER = "#a8a2ff";
const INK = "#05010f";

const TOWER_COLORS: Record<Exclude<TowerState, "destroyed">, { rim: string; fill: string; shade: string; eye: string }> = {
  standing: { rim: LAVENDER, fill: "#2c1b7d", shade: "#170b4d", eye: TEAL },
  siege: { rim: PINK, fill: "#651170", shade: "#330742", eye: YELLOW },
};

/** A shape with a neon rim outside its ink outline. */
function Inked({ d, rim, fill }: { d: string; rim: string; fill: string }) {
  return (
    <>
      <path d={d} fill={fill} stroke={rim} strokeWidth={2.6} strokeLinejoin="round" />
      <path d={d} fill="none" stroke={INK} strokeWidth={1.1} strokeLinejoin="round" />
    </>
  );
}

/** A hazard-striped band, `count` stripes wide. */
function Hazard({ x, y, count }: { x: number; y: number; count: number }) {
  return (
    <>
      <rect x={x} y={y} width={count * 4} height={3} fill={YELLOW} />
      {Array.from({ length: count }, (_, i) => (
        <path key={i} d={`M${x + i * 4 + 0.5} ${y + 3}l2-3h1.5l-2 3z`} fill={INK} />
      ))}
    </>
  );
}

/** The runners' flag, planted on a flatlined tower. */
function Flag({ x, y }: { x: number; y: number }) {
  return (
    <g>
      <line x1={x} y1={y} x2={x} y2={y - 17} stroke={INK} strokeWidth={2.4} strokeLinecap="round" />
      <line x1={x} y1={y} x2={x} y2={y - 17} stroke={LAVENDER} strokeWidth={1.2} strokeLinecap="round" />
      <path d={`M${x} ${y - 17}l11 1.5-3 2.5 3 3-11 1z`} fill={YELLOW} stroke={INK} strokeWidth={0.8} strokeLinejoin="round" />
    </g>
  );
}

/** Severed cables spilling out of a wreck. */
function Cables({ x, y }: { x: number; y: number }) {
  return (
    <g fill="none" strokeLinecap="round" strokeWidth={1.3}>
      <path d={`M${x} ${y}c-4-5-7-1-9 3`} stroke={PINK} />
      <path d={`M${x + 2} ${y}c-2-7-8-6-12-4`} stroke={TEAL} />
      <circle cx={x - 9} cy={y + 3} r={1} fill={YELLOW} stroke="none" className="animate-pulse" />
    </g>
  );
}

/** An ICE tower: a server stack with a scanning visor and a hazard-striped hatch. 40x56. */
export function Tower({ state, className }: { state: TowerState; className?: string }) {
  if (state === "destroyed") {
    return (
      <svg viewBox="0 0 40 56" className={className} aria-hidden="true">
        <Cables x={15} y={37} />
        <Inked d="M7 54V39l4-6 3 5 4-9 4 7 4-5 3 4 4 2v17z" rim={TEAL} fill="#14103a" />
        <path d="M21 54V36l4-5 3 4 4 2v17z" fill={INK} opacity={0.55} />
        <path d="M11 44h8M11 48h6" stroke={TEAL} strokeOpacity={0.55} strokeWidth={1.3} />
        <path d="M2 54l2-4 3 1 1 3zM33 54l1-5 3 1 1 4z" fill="#14103a" stroke={TEAL} strokeOpacity={0.7} strokeLinejoin="round" />
        <Flag x={27} y={36} />
      </svg>
    );
  }
  const { rim, fill, shade, eye } = TOWER_COLORS[state];
  return (
    <svg viewBox="0 0 40 56" className={className} aria-hidden="true">
      <line x1={20} y1={9} x2={20} y2={3} stroke={rim} strokeWidth={1.5} />
      <circle cx={20} cy={2.5} r={1.5} fill={eye} className="animate-pulse" />
      <Inked d="M11 8h18l5 6v40H6V14z" rim={rim} fill={fill} />
      {/* Hard cel shadow down the right side. */}
      <path d="M22 9h6.5l4.5 5.4V53H22z" fill={shade} />
      <rect x={9} y={11} width={22} height={1.5} fill={rim} opacity={0.5} />
      {/* The scanning visor. */}
      <path d="M9 18h22l-2 8H11z" fill={INK} stroke={rim} strokeWidth={0.8} strokeLinejoin="round" />
      <path d="M12 21h16l-1 2.5H13z" fill={eye} className="animate-pulse" />
      {/* Server slots. */}
      <path d="M10 30h8M10 33h5M10 36h8" stroke={TEAL} strokeOpacity={0.75} strokeWidth={1.2} />
      <path d="M24 30h6M26 33h4M24 36h6" stroke={PINK} strokeOpacity={0.75} strokeWidth={1.2} />
      <path d="M15 53v-9l2-2h6l2 2v9z" fill={INK} stroke={rim} strokeOpacity={0.8} strokeWidth={0.8} />
      <Hazard x={16} y={46} count={2} />
    </svg>
  );
}

/** The final level's boss: a corp arcology with a chrome skull on its face. 72x60. */
export function Fortress({ state, className }: { state: TowerState; className?: string }) {
  if (state === "destroyed") {
    return (
      <svg viewBox="0 0 72 60" className={className} aria-hidden="true">
        <Cables x={20} y={39} />
        <Inked d="M4 58V40l5-6 4 5 5-8 5 6 6-4 6 5 5-7 6 5 5-6 5 4 4 6 4-2v20z" rim={TEAL} fill="#14103a" />
        <path d="M36 58V37l5-7 6 5 5-6 5 4 4 6 4-2v21z" fill={INK} opacity={0.55} />
        <path d="M29 57v-8l4-3h6l4 3v8" fill={INK} stroke={TEAL} strokeOpacity={0.6} />
        <Flag x={36} y={36} />
      </svg>
    );
  }
  const fill = state === "siege" ? "#651170" : "#3a1183";
  const shade = state === "siege" ? "#330742" : "#1c0a52";
  return (
    <svg viewBox="0 0 72 60" className={className} aria-hidden="true">
      <Inked d="M3 59V24l6-7h8V9l7-7h24l7 7v8h8l6 7v35z" rim={PINK} fill={fill} />
      <path d="M36 3h11.5l6.5 6.5V18h8.5l5.5 6.5V58H36z" fill={shade} />
      {/* The corp's sign. */}
      <path d="M24 8h24l2 5H22z" fill={YELLOW} stroke={INK} strokeWidth={0.8} strokeLinejoin="round" />
      <path d="M27 10.5h6M36 10.5h9" stroke={INK} strokeWidth={1.3} />
      {/* Wing windows. */}
      <path d="M7 27h7M7 32h7M7 37h7M7 42h7" stroke={TEAL} strokeOpacity={0.85} strokeWidth={1.5} />
      <path d="M58 27h7M58 32h7M58 37h7M58 42h7" stroke={PINK} strokeOpacity={0.85} strokeWidth={1.5} />
      <circle cx={10.5} cy={21} r={1.6} fill={TEAL} className="animate-pulse" />
      <circle cx={61.5} cy={21} r={1.6} fill={TEAL} className="animate-pulse" />
      {/* The chrome skull. */}
      <path
        d="M27 25c0-5 4-8 9-8s9 3 9 8c0 3-1 5-3 6v4H30v-4c-2-1-3-3-3-6z"
        fill="#e8e6ff"
        stroke={INK}
        strokeWidth={1.2}
        strokeLinejoin="round"
      />
      <path d="M36 17.5c5 0 8.5 3 8.5 7.5 0 3-1 5-3 6v3.5H36z" fill={LAVENDER} />
      <path d="M29.5 23l5 1.5-1 3.5h-3zM42.5 23l-5 1.5 1 3.5h3z" fill={INK} />
      <circle cx={32} cy={25.5} r={1} fill={PINK} className="animate-pulse" />
      <circle cx={40} cy={25.5} r={1} fill={PINK} className="animate-pulse" />
      <path d="M33 32v3M36 32v3M39 32v3" stroke={INK} strokeWidth={0.9} />
      {/* The blast door. */}
      <path d="M27 58v-12l4-4h10l4 4v12z" fill={INK} stroke={PINK} strokeWidth={0.9} strokeLinejoin="round" />
      <Hazard x={28} y={48} count={4} />
    </svg>
  );
}

/** The runners' starting rig: a bolted-together hideout, a dish and a live screen. 40x32. */
export function Camp({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 32" className={className} aria-hidden="true">
      <Inked d="M4 30V15l4-4h20l5 4v15z" rim={TEAL} fill="#2c1b7d" />
      <path d="M19 12h8.5l4.5 3.5V29H19z" fill="#170b4d" />
      <path d="M8 16h10v8H8z" fill={INK} stroke={TEAL} strokeWidth={0.9} />
      <path d="M10 19h6M10 21.5h4" stroke={TEAL} strokeWidth={1.1} className="animate-pulse" />
      <path d="M23 30v-9h6v9z" fill={INK} stroke={PINK} strokeWidth={0.9} />
      <Hazard x={4} y={27} count={3} />
      {/* The dish. */}
      <path d="M26 11l3-4" stroke={LAVENDER} strokeWidth={1.3} />
      <path d="M25 3.5c1 4 4.5 6 8.5 5.5z" fill={LAVENDER} stroke={INK} strokeWidth={0.8} strokeLinejoin="round" />
      <Flag x={6} y={18} />
    </svg>
  );
}

/** One gremlin netrunner: pointy ears, wraparound visor, yellow jacket, trailing neural cables. Faces right. 24x24. */
export function Gremlin({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      {/* Neural cables, jacked into the back of the skull. */}
      <path d="M6 10C1.5 10 1 15 2.5 18.5" fill="none" stroke={PINK} strokeWidth={1.2} strokeLinecap="round" />
      <path d="M6.5 12C4 13 3.5 16 5 19.5" fill="none" stroke={TEAL} strokeWidth={1.2} strokeLinecap="round" />
      {/* Legs. */}
      <path d="M9.5 20.5v2.5M15 20.5v2.5" stroke={LAVENDER} strokeWidth={2} strokeLinecap="round" />
      {/* Jacket, with a hard shadow and a pink collar. */}
      <path d="M7.5 15h9.5l1.5 6.5H6z" fill={YELLOW} stroke={INK} strokeWidth={0.9} strokeLinejoin="round" />
      <path d="M12.5 15.5h4.1l1.3 5.5h-5.4z" fill="#c2a900" />
      <path d="M8.5 15h7.5l-1.2 2h-5.3z" fill={PINK} stroke={INK} strokeWidth={0.6} strokeLinejoin="round" />
      {/* Ears. */}
      <path d="M6 7.5L1 2.5l7.5 2.5zM18 7.5l5-5-7.5 2.5z" fill={TEAL} stroke={INK} strokeWidth={0.9} strokeLinejoin="round" />
      {/* Head. */}
      <ellipse cx={12} cy={9.5} rx={7} ry={6} fill={TEAL} stroke={INK} strokeWidth={1} />
      <path d="M12.5 3.6c3.8 0 6 2.6 6 5.9s-2.2 5.4-6 5.4z" fill="#1fb896" />
      {/* Visor. */}
      <path d="M5.5 6.8h13.5l.8 3.2-1.5 2.2H8z" fill={INK} />
      <path d="M8 8.2h10l.4 1.6-.8 1H8.8z" fill={PINK} />
      <path d="M10.5 8.2h2.5l-1.4 2.6H9.5z" fill="#ffd6f6" />
      {/* Grin. */}
      <path d="M11 13.1l1.5.5 2-.2 1-.6" fill="none" stroke={INK} strokeWidth={0.9} strokeLinecap="round" />
    </svg>
  );
}
