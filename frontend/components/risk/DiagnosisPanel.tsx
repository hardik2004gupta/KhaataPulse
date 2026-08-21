"use client";
import type { DiagnosisInfo, RiskInfo, ActionRanking } from "@/lib/types";
import { formatCause, formatAction, formatINR } from "@/lib/utils/format";

interface DiagnosisPanelProps {
  risk: RiskInfo;
  diagnosis: DiagnosisInfo;
  actionRankings: ActionRanking[];
}

export function DiagnosisPanel({ risk, diagnosis, actionRankings }: DiagnosisPanelProps) {
  return (
    <div className="space-y-5">
      {/* Risk signals */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
          Risk Signals — Top 3
        </p>
        <div className="space-y-2">
          {risk.top_signals.map((sig) => {
            const pct = Math.round(sig.impact * 100);
            return (
              <div key={sig.feature}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-text-secondary capitalize">{sig.feature.replace(/_/g, " ")}</span>
                  <span className="mono text-warning-text tabular">{pct}%</span>
                </div>
                <div className="h-1.5 bg-surface-elevated rounded-full overflow-hidden">
                  <div
                    className="h-full bg-warning rounded-full"
                    style={{ width: `${Math.min(pct * 2.5, 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Diagnosis */}
      <div className="bg-ai-dim/30 border border-ai/20 rounded-lg p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-ai-text mb-3">
          AI Diagnosis
        </p>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <p className="text-xs text-text-muted mb-0.5">Cause</p>
            <p className="font-semibold text-text-primary">{formatCause(diagnosis.cause)}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted mb-0.5">Confidence</p>
            <p className={`font-semibold tabular ${diagnosis.confidence > 0.7 ? "text-recovery-text" : "text-warning-text"}`}>
              {Math.round(diagnosis.confidence * 100)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-text-muted mb-0.5">Proposed Action</p>
            <p className="font-semibold text-ai-text">{formatAction(diagnosis.proposed_action)}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted mb-0.5">Risk Level</p>
            <p className={`font-semibold ${
              diagnosis.risk_level === "HIGH" ? "text-critical-text"
              : diagnosis.risk_level === "MEDIUM" ? "text-warning-text"
              : "text-recovery-text"
            }`}>{diagnosis.risk_level}</p>
          </div>
        </div>
        <p className="text-xs text-text-muted leading-relaxed italic">{diagnosis.rationale}</p>
      </div>

      {/* Action Rankings */}
      {actionRankings.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
            Action Rankings — Expected Net Revenue
          </p>
          <div className="space-y-1.5">
            {actionRankings.map((r) => (
              <div
                key={r.action_type}
                className={`flex items-center justify-between px-3 py-2 rounded border ${
                  r.rank === 1
                    ? "bg-recovery-dim/30 border-recovery/30"
                    : "bg-surface-elevated border-border/50"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`mono text-xs ${r.rank === 1 ? "text-recovery-text" : "text-text-muted"}`}>
                    #{r.rank}
                  </span>
                  <span className={`text-sm font-medium ${r.rank === 1 ? "text-text-primary" : "text-text-secondary"}`}>
                    {formatAction(r.action_type)}
                  </span>
                </div>
                <span className={`tabular text-sm font-semibold ${r.rank === 1 ? "text-recovery-text" : "text-text-muted"}`}>
                  ENR {formatINR(r.enr)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
