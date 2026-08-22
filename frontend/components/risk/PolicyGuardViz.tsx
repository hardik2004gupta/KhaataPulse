"use client";

import { useEffect, useState } from "react";
import type { PolicyDecision } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import { formatAction } from "@/lib/utils/format";

const CHECK_LABELS: Record<string, string> = {
  kill_switch: "Kill Switch",
  dispute_hold: "Dispute Hold",
  legal_hold: "Legal Hold",
  opt_out: "Customer Opt-out",
  idempotency: "Idempotency",
  contact_limit: "Contact Limit (3/7d)",
  cooldown: "Cooldown (24h)",
  amount_threshold: "Amount Threshold",
};

/** Canonical gate order — the guard is evaluated as a sequence, not a set. */
const CHECK_ORDER = [
  "kill_switch",
  "dispute_hold",
  "legal_hold",
  "opt_out",
  "idempotency",
  "contact_limit",
  "cooldown",
  "amount_threshold",
];

interface PolicyGuardVizProps {
  decision: PolicyDecision;
}

const VERDICT: Record<string, { text: string; border: string; bg: string; glyph: string }> = {
  APPROVED: {
    text: "text-recovery-text",
    border: "border-recovery/35",
    bg: "bg-recovery-dim/25",
    glyph: "✓",
  },
  BLOCKED: {
    text: "text-critical-text",
    border: "border-critical/35",
    bg: "bg-critical-dim/25",
    glyph: "✕",
  },
  ESCALATED: {
    text: "text-warning-text",
    border: "border-warning/35",
    bg: "bg-warning-dim/25",
    glyph: "⚠",
  },
};

export function PolicyGuardViz({ decision }: PolicyGuardVizProps) {
  const entries = Object.entries(decision.checks);
  const ordered = [
    ...CHECK_ORDER.filter((k) => k in decision.checks).map(
      (k) => [k, decision.checks[k]] as [string, boolean],
    ),
    ...entries.filter(([k]) => !CHECK_ORDER.includes(k)),
  ];

  // Gates settle one after another — the checkpoint reads as sequential.
  const [revealed, setRevealed] = useState(0);
  useEffect(() => {
    setRevealed(0);
    const timers = ordered.map((_, i) =>
      window.setTimeout(() => setRevealed(i + 1), 90 * (i + 1)),
    );
    return () => timers.forEach((t) => window.clearTimeout(t));
    // Re-run whenever the decision identity changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [decision.status, decision.action_type, ordered.length]);

  const verdict = VERDICT[decision.status] ?? VERDICT.BLOCKED;

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <Eyebrow>Policy Guard</Eyebrow>
        <span className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
          Deterministic
        </span>
      </div>

      {/* ── Sequential gates ─────────────────────────────────────────────── */}
      <ol className="mt-3">
        {ordered.map(([key, passed], i) => {
          const shown = i < revealed;
          return (
            <li
              key={key}
              className={`flex items-center gap-3 border-l border-border-subtle py-1.5 pl-3 transition-all duration-base ${
                shown ? "opacity-100" : "translate-x-1 opacity-0"
              }`}
            >
              <span className="mono w-5 shrink-0 text-[10px] text-text-faint">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span
                className={`mono min-w-0 flex-1 truncate text-[11px] uppercase tracking-wider ${
                  passed ? "text-text-secondary" : "text-critical-text"
                }`}
              >
                {CHECK_LABELS[key] ?? key.replace(/_/g, " ")}
              </span>
              <span
                className={`mono shrink-0 text-[10px] font-semibold ${
                  passed ? "text-recovery-text" : "text-critical-text"
                }`}
              >
                {passed ? "✓ PASS" : "✕ FAIL"}
              </span>
            </li>
          );
        })}
      </ol>

      {/* ── Verdict ──────────────────────────────────────────────────────── */}
      <div
        className={`mt-4 rounded-panel border ${verdict.border} ${verdict.bg} px-4 py-3 transition-opacity duration-base ${
          revealed >= ordered.length ? "opacity-100" : "opacity-0"
        }`}
      >
        <div className="flex items-center justify-between gap-3">
          <span className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
            Verdict
          </span>
          <span className="mono text-[10px] uppercase tracking-eyebrow text-text-muted">
            {formatAction(decision.action_type)}
          </span>
        </div>
        <p className={`mono mt-1.5 text-xl font-bold tracking-wider ${verdict.text}`}>
          {verdict.glyph} {decision.status}
        </p>

        {decision.block_reason && (
          <p className="mono mt-2 text-[10px] uppercase tracking-wider text-critical-text">
            {decision.block_reason}
          </p>
        )}
        {decision.status === "ESCALATED" && !decision.block_reason && (
          <p className="mono mt-2 text-[10px] uppercase tracking-wider text-warning-text">
            Amount threshold — human approval required
          </p>
        )}
      </div>
    </div>
  );
}
