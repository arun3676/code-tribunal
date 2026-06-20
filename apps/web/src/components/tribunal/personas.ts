import type { AgentName } from "@/lib/api";

export type Persona = {
  name: AgentName;
  /** Plain functional role shown as a chip. */
  role: string;
  /** Fun character nickname for the demo. */
  nickname: string;
  provider: string;
  color: string;
  /** One-line "what they do" in plain language. */
  summary: string;
  /** Personality — how they carry themselves. */
  tagline: string;
  /** A short line they'd "say" — flavor for the cast cards. */
  catchphrase: string;
  recruited?: boolean;
};

// Mirrors apps/api/code_council/tribunal/protocol.py AGENTS.
export const PERSONAS: Record<AgentName, Persona> = {
  CLERK: {
    name: "CLERK",
    role: "Orchestrator",
    nickname: "The Conductor",
    provider: "Band",
    color: "var(--clerk)",
    summary: "Opens the chamber, routes @mentions, and summons specialists.",
    tagline: "Runs the room with zero drama. Calls exactly the witnesses the case needs.",
    catchphrase: "Chamber's open. Let's hear it.",
  },
  ADVOCATE: {
    name: "ADVOCATE",
    role: "Intent Witness",
    nickname: "The Literalist",
    provider: "Groq",
    color: "var(--advocate)",
    summary: "Reads the ticket and turns it into a hard requirement checklist.",
    tagline: "Holds everyone to the receipts. If you asked for five things, all five get counted.",
    catchphrase: "You asked for five things. I'm counting all five.",
  },
  SURVEYOR: {
    name: "SURVEYOR",
    role: "Implementation Witness",
    nickname: "The Cartographer",
    provider: "Groq",
    color: "var(--surveyor)",
    summary: "Walks the diff line by line and maps what actually shipped.",
    tagline: "No opinions, just terrain. Reports exactly what the code does.",
    catchphrase: "Here's what the code really does.",
  },
  GHOST: {
    name: "GHOST",
    role: "Omission Auditor",
    nickname: "The Negative Space",
    provider: "Groq",
    color: "var(--ghost)",
    summary: "Finds work that was requested but never written — the silence.",
    tagline: "Hunts the gaps everyone else scrolls past. Sees what isn't there.",
    catchphrase: "You forgot something. I can feel it.",
  },
  DRIFT: {
    name: "DRIFT",
    role: "Scope Auditor",
    nickname: "The Tripwire",
    provider: "Cerebras",
    color: "var(--drift)",
    summary: "Flags changes that no requirement ever authorized.",
    tagline: "Catches the sneaky extras nobody approved. Trusts nothing on sight.",
    catchphrase: "Who authorized this?",
  },
  WARDEN: {
    name: "WARDEN",
    role: "Constraint Witness",
    nickname: "The Bouncer",
    provider: "Band",
    color: "var(--warden)",
    summary: "Recruited mid-trial when a change touches security or auth.",
    tagline: "Only appears when something's on the line — and never blinks.",
    catchphrase: "Not on my watch.",
    recruited: true,
  },
  ARBITER: {
    name: "ARBITER",
    role: "Judge",
    nickname: "The Gavel",
    provider: "Groq",
    color: "var(--arbiter)",
    summary: "Weighs every witness, scores trust, and issues the final ruling.",
    tagline: "Hears it all, then decides. The trust score is not a negotiation.",
    catchphrase: "The chamber has decided.",
  },
};

export const TRIAL_ORDER: AgentName[] = ["CLERK", "ADVOCATE", "SURVEYOR", "GHOST", "DRIFT", "WARDEN", "ARBITER"];
