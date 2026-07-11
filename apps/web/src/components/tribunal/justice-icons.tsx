/** Refined illustrative justice icons — line + subtle fill, thematic, not generic. */

type IconProps = { size?: number; className?: string; color?: string };

export function ScalesIcon({ size = 22, className, color = "currentColor" }: IconProps) {
  const s = { stroke: color, strokeWidth: 1.4, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <g {...s}>
        <path d="M12 3v18M7 21h10" />
        <path d="M4 7h16M12 4l-1 0" />
        <path d="M4 7l-2.5 5.5h5z" />
        <path d="M20 7l-2.5 5.5h5z" />
        <path d="M1.5 12.5a2.5 2 0 0 0 5 0M17.5 12.5a2.5 2 0 0 0 5 0" />
      </g>
    </svg>
  );
}

export function GavelIcon({ size = 22, className, color = "currentColor" }: IconProps) {
  const s = { stroke: color, strokeWidth: 1.4, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <g {...s}>
        <rect x={12} y={3} width={7} height={4} rx={1} transform="rotate(45 15.5 5)" />
        <path d="M10 8l5 5" />
        <path d="M5 19l6-6" />
        <path d="M4 21h7" />
      </g>
    </svg>
  );
}

export function EvidenceTagIcon({ size = 16, className, color = "currentColor" }: IconProps) {
  const s = { stroke: color, strokeWidth: 1.4, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <g {...s}>
        <path d="M3 10l7-7 11 11-7 7z" />
        <circle cx={7.5} cy={7.5} r={1.4} fill={color} stroke="none" />
      </g>
    </svg>
  );
}

export function SealIcon({ size = 22, className, color = "currentColor" }: IconProps) {
  const s = { stroke: color, strokeWidth: 1.4, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <g {...s}>
        <circle cx={12} cy={10} r={6} />
        <path d="M9 15l-1.5 6 4.5-2.5L16.5 21 15 15" />
        <path d="M9.5 10l1.7 1.7L15 8" />
      </g>
    </svg>
  );
}
