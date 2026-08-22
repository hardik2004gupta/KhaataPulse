"use client";

import type { CSSProperties } from "react";
import type { DiagnosisInfo, RiskInfo, ActionRanking } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import {
  formatCause,
  formatAction,
  formatINR,
  riskTextClass,
} from "@/lib/utils/format";

interface DiagnosisPanelProps {
  risk: RiskInfo;
  diagnosis: DiagnosisInfo;
  actionRankings: ActionRanking[];
  /** Set while the reasoner is still working — the bar breathes until it settles. */
  isLoading?: boolean;
}

const LEVEL_TONE: Record<string, string> = {
  HIGH: "border-critical/30 bg-critical-dim/30 text-critical-text",
  MEDIUM: "border-warning/30 bg-warning-dim/30 text-warning-text",
  LOW: "border-recovery/30 bg-recovery-dim/30 text-recovery-text",
};

function RiskLevelBadge({ level }: { level: string }) {
  return (
    <span
      className={`mono rounded border px-2 py-0.5 text-[10px] uppercase tracking-eyebrow ${
        LEVEL_TONE[level] ?? "border-border text-text-secondary"
      }`}
    >
      {level}
    </span>
  );
}

/**
 * Animated fill — communicates model certainty, settles once and stays.
 * The fill is a CSS animation keyed off --bar-width rather than a JS-driven
 * width change, so reduced-motion readers see the final value immediately.
 */
export function ConfidenceBar({
  value,
  isLoading = false,
}: {
  value: number;
  isLoading?: boolean;
}) {
  const pct = Math.round(value * 100);
  // Below half the diagnosis is tentative; at or above it the reasoner is
  // speaking with the confidence the AI accent denotes.
  const confident = value >= 0.5;

  return (
    <div className="flex items-center gap-3">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-bg-primary">
        <div
          style={{ "--bar-width": `${pct}%` } as CSSProperties}
          className={`h-full rounded-full ${
            isLoading ? "bar-grow-pending" : "bar-grow"
          } ${confident ? "bg-ai" : "bg-warning"}`}
        />
      </div>
      <span
        className={`mono tabular text-xs font-semibold ${
          confident ? "text-ai-text" : "text-warning-text"
        }`}
      >
        {pct}%
      </span>
    </div>
  );
}

export function DiagnosisPanel({
  risk,
  diagnosis,
  actionRankings,
  isLoading = false,
}: DiagnosisPanelProps) {
  const maxImpact = Math.max(...risk.top_signals.map((s) => Math.abs(s.impact)), 0.0001);

  return (
    <div className="space-y-6">
      {/* ── Risk assessment ──────────────────────────────────────────────── */}
      <section>
        <div className="flex items-baseline justify-between gap-3">
          <Eyebrow>Risk Assessment</Eyebrow>
          <span className="mono text-[10px] text-text-faint">{risk.model_version}</span>
        </div>

        <div className="mt-3 flex items-baseline gap-3">
          <span
            className={`tabular text-3xl font-bold leading-none tracking-tightest sm:text-4xl ${riskTextClass(
              risk.risk_score,
            )}`}
          >
            {Math.round(risk.risk_score * 100)}
            <span className="text-lg">%</span>
          </span>
          <RiskLevelBadge level={risk.risk_level} />
        </div>

        <p className="mono mt-3 text-[10px] uppercase tracking-eyebrow text-text-faint">
          Top Signals
        </p>
        <div className="mt-2 space-y-2">
          {risk.top_signals.slice(0, 3).map((sig) => {
            const rel = Math.abs(sig.impact) / maxImpact;
            return (
              <div key={sig.feature}>
                <div className="mb-1 flex items-baseline justify-between gap-2">
                  <span className="text-[11px] capitalize text-text-secondary">
                    {sig.feature.replace(/_/g, " ")}
                  </span>
                  <span className="mono tabular text-[10px] text-warning-text">
                    {sig.impact >= 0 ? "+" : ""}
                    {sig.impact.toFixed(3)}
                  </span>
                </div>
                <div className="h-1 overflow-hidden rounded-full bg-bg-primary">
                  <div
                    className="h-full rounded-full bg-warning/80"
                    style={{ width: `${Math.max(rel * 100, 4)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── AI diagnosis ─────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden rounded-panel border-l-2 border-ai bg-ai-dim/20 p-4">
        <div className="flex items-center justify-between gap-3">
          <Eyebrow tone="ai">AI Diagnosis</Eyebrow>
          <RiskLevelBadge level={diagnosis.risk_level} />
        </div>

        <p className="mt-3 text-base font-semibold text-text-primary">
          {formatCause(diagnosis.cause)}
        </p>

        <div className="mt-3">
          <p className="mono mb-1.5 text-[10px] uppercase tracking-eyebrow text-text-faint">
            Confidence
          </p>
          <ConfidenceBar value={diagnosis.confidence} isLoading={isLoading} />
        </div>

        <p className="mt-3 border-t border-ai/15 pt-3 text-[11px] italic leading-relaxed text-text-muted">
          {diagnosis.rationale}
        </p>

        <p className="mono mt-3 text-[10px] uppercase tracking-eyebrow text-text-faint">
          Proposed · <span className="text-ai-text">{formatAction(diagnosis.proposed_action)}</span>
        </p>
      </section>

      {/* ── Economic optimiser ───────────────────────────────────────────── */}
      {actionRankings.length > 0 && (
        <section>
          <div className="flex items-baseline justify-between gap-3">
            <Eyebrow>Intervention</Eyebrow>
            <span className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
              Ranked by ENR
            </span>
          </div>

          <ol className="mt-3 space-y-1.5">
            {actionRankings.map((r) => {
              const selected = r.rank === 1;
              return (
                <li
                  key={r.action_type}
                  className={`flex items-center justify-between gap-3 rounded border px-3 py-2 transition-colors duration-base ${
                    selected
                      ? "border-recovery/35 bg-recovery-dim/25"
                      : "border-border-subtle bg-surface-elevated/50"
                  }`}
                >
                  <span className="flex min-w-0 items-center gap-2.5">
                    <span
                      className={`mono text-[10px] ${
                        selected ? "text-recovery-text" : "text-text-faint"
                      }`}
                    >
                      {String(r.rank).padStart(2, "0")}
                    </span>
                    <span
                      className={`truncate text-[13px] ${
                        selected ? "font-medium text-text-primary" : "text-text-secondary"
                      }`}
                    >
                      {formatAction(r.action_type)}
                    </span>
                  </span>

                  <span
                    className={`tabular shrink-0 text-[13px] font-semibold ${
                      selected ? "text-recovery-text" : "text-text-muted"
                    }`}
                  >
                    {formatINR(r.enr)}
                  </span>
                </li>
              );
            })}
          </ol>

          <p className="mono mt-2.5 text-[10px] uppercase tracking-eyebrow text-recovery-text">
            Selected · {formatAction(actionRankings[0].action_type)}
            <span className="text-text-faint"> — highest expected net revenue</span>
          </p>
        </section>
      )}
    </div>
  );
}
