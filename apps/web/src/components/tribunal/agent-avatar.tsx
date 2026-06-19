import type { AgentName } from "@/lib/api";
import { PERSONAS } from "./personas";

/**
 * Neo-brutalist persona avatars — a solid pastel medallion with a thick black
 * outline and black line-work bust, so each specialist reads as a bold,
 * sticker-like character. Consistent framing communicates who is speaking.
 */

const INK = "#1a1a1a";

type Props = {
  agent: AgentName;
  size?: number;
  active?: boolean;
  className?: string;
};

function Bust({ opacity = 1 }: { opacity?: number }) {
  return (
    <g opacity={opacity}>
      <path d="M14 56c0-9.5 8-15 18-15s18 5.5 18 15" fill="rgba(26,26,26,0.12)" stroke={INK} strokeWidth={2} strokeLinecap="round" />
      <circle cx={32} cy={26} r={9.5} fill="rgba(26,26,26,0.12)" stroke={INK} strokeWidth={2} />
    </g>
  );
}

function Emblem({ agent }: { agent: AgentName }) {
  const s = { stroke: INK, strokeWidth: 1.8, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (agent) {
    case "CLERK":
      return (
        <g {...s}>
          <path d="M26 45h12v8H26z" />
          <path d="M32 45v8M28.5 48h2M33.5 48h2" />
        </g>
      );
    case "ADVOCATE":
      return (
        <g {...s}>
          <path d="M25 44c0-1.4 1.1-2.5 2.5-2.5h9c1.4 0 2.5 1.1 2.5 2.5v9c0 1.4-1.1 2.5-2.5 2.5h-9" />
          <path d="M25 44v9c0 1.4 1.1 2.5 2.5 2.5M29 46h6M29 49h6" />
        </g>
      );
    case "SURVEYOR":
      return (
        <g {...s}>
          <circle cx={30} cy={47} r={4.5} />
          <path d="M33.5 50.5 37 54" />
        </g>
      );
    case "WARDEN":
      return (
        <g {...s} strokeWidth={2}>
          <path d="M32 41l6 2v4c0 4-2.6 6.4-6 7.6-3.4-1.2-6-3.6-6-7.6v-4z" />
          <path d="M29.5 47.5l1.8 1.8 3.2-3.4" />
        </g>
      );
    case "ARBITER":
      return (
        <g {...s}>
          <rect x={27} y={43} width={8} height={4} rx={1} transform="rotate(-32 31 45)" />
          <path d="M33 46l4.5 6.5" transform="rotate(-32 33 46)" />
          <circle cx={38} cy={42} r={1.6} fill={INK} stroke="none" />
        </g>
      );
    default:
      return null;
  }
}

export function AgentAvatar({ agent, size = 48, active = false, className }: Props) {
  const color = PERSONAS[agent].color;
  const isGhost = agent === "GHOST";
  const isDrift = agent === "DRIFT";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label={`${agent} avatar`}
      className={className}
      style={{ overflow: "visible", filter: active ? "drop-shadow(2px 2px 0 #1a1a1a)" : undefined }}
    >
      {/* Medallion frame — solid pastel fill, thick ink outline */}
      <circle cx={32} cy={32} r={29} fill={isGhost ? "var(--bg-overlay)" : color} stroke={INK} strokeWidth={active ? 3 : 2.4} />
      <circle cx={32} cy={32} r={24.5} fill="none" stroke={INK} strokeWidth={0.8} opacity={0.25} />

      {isGhost ? (
        <g strokeDasharray="3 3">
          <Bust opacity={0.85} />
        </g>
      ) : isDrift ? (
        <>
          <g transform="translate(1.8 0)" opacity={0.35}>
            <Bust />
          </g>
          <Bust />
        </>
      ) : (
        <Bust />
      )}

      <Emblem agent={agent} />
    </svg>
  );
}
