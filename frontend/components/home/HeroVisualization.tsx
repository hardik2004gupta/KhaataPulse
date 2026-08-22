"use client";

import { useEffect, useState } from "react";

/* ── Geometry ─────────────────────────────────────────────────────────────── */

const NODE_X = [50, 164, 278, 392, 506, 630] as const;
const NODE_Y = 110;
const NODE_R = 26;
const LINK_GAP = 6;

/* ── Accents ──────────────────────────────────────────────────────────────
   Colours come from the design tokens in globals.css — never literal hex.
   ─────────────────────────────────────────────────────────────────────── */

type Accent = "warning" | "ai" | "critical" | "recovery";

const ACCENT_VAR: Record<Accent, string> = {
  warning: "var(--accent-warning)",
  ai: "var(--accent-ai)",
  critical: "var(--accent-critical)",
  recovery: "var(--accent-recovery)",
};

const ACCENT_GLOW: Record<Accent, string> = {
  warning: "svg-glow-warning",
  ai: "svg-glow-ai",
  critical: "svg-glow-critical",
  recovery: "svg-glow-recovery",
};

const ACCENT_TEXT: Record<Accent, string> = {
  warning: "text-warning-text",
  ai: "text-ai-text",
  critical: "text-critical-text",
  recovery: "text-recovery-text",
};

/* ── Pipeline stages ──────────────────────────────────────────────────────── */

interface Stage {
  label: string;
  sub: string;
  accent: Accent;
  /** Terminal readout line, e.g. "01 SIGNAL DETECTED". */
  readout: string;
}

const STAGES: readonly Stage[] = [
  {
    label: "SIGNALS",
    sub: "observable",
    accent: "warning",
    readout: "SIGNAL DETECTED",
  },
  {
    label: "RISK SIEVE",
    sub: "logistic",
    accent: "warning",
    readout: "RISK ANALYZED",
  },
  {
    label: "AI REASONER",
    sub: "langgraph",
    accent: "ai",
    readout: "CONTEXT UNDERSTOOD",
  },
  {
    label: "ENR OPTIMIZER",
    sub: "expected net",
    accent: "ai",
    readout: "ECONOMIC OPTION RANKED",
  },
  {
    label: "POLICY GUARD",
    sub: "deterministic",
    accent: "critical",
    readout: "POLICY VERIFIED",
  },
  {
    label: "RECOVERY",
    sub: "executed",
    accent: "recovery",
    readout: "RECOVERY EXECUTED",
  },
];

const STAGE_MS = 2000;

/* ── Node ─────────────────────────────────────────────────────────────────── */

function PipelineNode({ index, active }: { index: number; active: boolean }) {
  const stage = STAGES[index];
  const cx = NODE_X[index];
  const accent = ACCENT_VAR[stage.accent];

  return (
    <g>
      {/* Inner surface */}
      <circle
        cx={cx}
        cy={NODE_Y}
        r={NODE_R - 1}
        fill={active ? "var(--surface-elevated)" : "var(--surface)"}
        className="transition-[fill] duration-base"
      />

      {/* Outer ring */}
      <circle
        key={active ? `on-${index}` : `off-${index}`}
        cx={cx}
        cy={NODE_Y}
        r={NODE_R}
        fill="none"
        stroke={active ? accent : "var(--border)"}
        strokeWidth={active ? 1.5 : 1}
        strokeOpacity={active ? 0.9 : 1}
        className={
          active ? `${ACCENT_GLOW[stage.accent]} node-arrive` : undefined
        }
      />

      {/* Core marker */}
      <circle
        cx={cx}
        cy={NODE_Y}
        r={active ? 4 : 2.5}
        fill={active ? accent : "var(--text-faint)"}
        className="transition-all duration-base"
      />

      {/* Label — sized for the ~0.6 downscale this SVG renders at in the hero */}
      <text
        x={cx}
        y={NODE_Y + NODE_R + 24}
        textAnchor="middle"
        className="mono transition-colors duration-base"
        fontSize="13"
        letterSpacing="0.04em"
        fill={active ? "var(--text-primary)" : "var(--text-muted)"}
      >
        {stage.label}
      </text>

      {/* Sub-label */}
      <text
        x={cx}
        y={NODE_Y + NODE_R + 40}
        textAnchor="middle"
        className="mono transition-colors duration-base"
        fontSize="11"
        letterSpacing="0.02em"
        fill={active ? "var(--text-muted)" : "var(--text-faint)"}
      >
        {stage.sub}
      </text>
    </g>
  );
}

/* ── Visualization ────────────────────────────────────────────────────────── */

export function HeroVisualization() {
  const [stage, setStage] = useState(0);
  const [cycle, setCycle] = useState(0);
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (media.matches) {
      // Static, fully-resolved pipeline for reduced-motion readers.
      setStage(STAGES.length - 1);
      return;
    }

    setAnimated(true);
    const id = window.setInterval(() => {
      setStage((prev) => {
        const next = (prev + 1) % STAGES.length;
        if (next === 0) setCycle((c) => c + 1);
        return next;
      });
    }, STAGE_MS);

    return () => window.clearInterval(id);
  }, []);

  const current = STAGES[stage];
  // A signal travels into every stage except the first of a cycle.
  const showSignal = animated && stage > 0;

  return (
    <div className="w-full">
      {/* The diagram has a legibility floor — below it, scroll rather than
          shrink the labels into illegibility. */}
      <div className="overflow-x-auto pb-2">
        <svg
          viewBox="0 0 680 220"
          width="100%"
          role="img"
          aria-label="KhaataPulse pipeline: signals, risk sieve, AI reasoner, ENR optimizer, policy guard, recovery"
          className="block min-w-[480px] overflow-visible"
        >
          <title>KhaataPulse recovery pipeline</title>

          {/* ── Connections ──────────────────────────────────────────────── */}
          {NODE_X.slice(0, -1).map((x, i) => {
            const x1 = x + NODE_R + LINK_GAP;
            const x2 = NODE_X[i + 1] - NODE_R - LINK_GAP;
            const isActiveLink = showSignal && stage === i + 1;
            return (
              <g key={`link-${i}`}>
                {/* Base */}
                <line
                  x1={x1}
                  y1={NODE_Y}
                  x2={x2}
                  y2={NODE_Y}
                  stroke="var(--border)"
                  strokeWidth={1}
                />
                {/* Energised overlay */}
                {isActiveLink && (
                  <line
                    key={`link-active-${i}-${cycle}`}
                    x1={x1}
                    y1={NODE_Y}
                    x2={x2}
                    y2={NODE_Y}
                    stroke={ACCENT_VAR[STAGES[i + 1].accent]}
                    strokeWidth={1.5}
                    strokeLinecap="round"
                    className={`link-active ${ACCENT_GLOW[STAGES[i + 1].accent]}`}
                  />
                )}
              </g>
            );
          })}

          {/* ── Nodes ────────────────────────────────────────────────────── */}
          {NODE_X.map((_, i) => (
            <PipelineNode key={`node-${i}`} index={i} active={i === stage} />
          ))}

          {/* ── Travelling signal ────────────────────────────────────────── */}
          {showSignal && (
            <circle
              key={`signal-${stage}-${cycle}`}
              r={4}
              cx={0}
              cy={0}
              fill={ACCENT_VAR[current.accent]}
              className={`signal-dot ${ACCENT_GLOW[current.accent]}`}
              style={
                {
                  "--sig-from-x": `${NODE_X[stage - 1]}px`,
                  "--sig-to-x": `${NODE_X[stage]}px`,
                  "--sig-y": `${NODE_Y}px`,
                } as React.CSSProperties
              }
            />
          )}
        </svg>
      </div>

      {/* ── State readout ──────────────────────────────────────────────── */}
      <ol className="mono mt-6 space-y-1.5 text-[10px] uppercase tracking-eyebrow">
        {STAGES.map((s, i) => {
          const isCurrent = i === stage;
          return (
            <li
              key={s.readout}
              className={`flex items-center gap-3 transition-colors duration-base ${
                isCurrent ? ACCENT_TEXT[s.accent] : "text-text-faint"
              }`}
            >
              <span
                aria-hidden="true"
                className="inline-block h-px w-4 transition-colors duration-base"
                style={{
                  backgroundColor: isCurrent
                    ? ACCENT_VAR[s.accent]
                    : "var(--border)",
                }}
              />
              <span className="tabular">{String(i + 1).padStart(2, "0")}</span>
              <span>{s.readout}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
