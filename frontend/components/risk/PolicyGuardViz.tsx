"use client";
import type { PolicyDecision } from "@/lib/types";
import { PolicyBadge } from "@/components/ui/PolicyBadge";

const CHECK_LABELS: Record<string, string> = {
  kill_switch:      "Kill Switch",
  dispute_hold:     "Dispute Hold",
  legal_hold:       "Legal Hold",
  opt_out:          "Customer Opt-out",
  idempotency:      "Idempotency",
  contact_limit:    "Contact Limit (3/7d)",
  cooldown:         "24h Cooldown",
  amount_threshold: "Amount Threshold",
};

interface PolicyGuardVizProps {
  decision: PolicyDecision;
}

export function PolicyGuardViz({ decision }: PolicyGuardVizProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Policy Guard
        </p>
        <PolicyBadge status={decision.status} />
      </div>

      <div className="space-y-1.5">
        {Object.entries(decision.checks).map(([key, passed]) => (
          <div key={key} className="flex items-center gap-2.5 text-sm">
            <span className={`mono text-sm font-semibold ${passed ? "text-recovery-text" : "text-critical-text"}`}>
              {passed ? "✓" : "✕"}
            </span>
            <span className={passed ? "text-text-secondary" : "text-critical-text"}>
              {CHECK_LABELS[key] ?? key}
            </span>
          </div>
        ))}
      </div>

      {decision.block_reason && (
        <div className="mt-3 px-3 py-2 bg-critical-dim/30 border border-critical/30 rounded text-xs text-critical-text">
          Blocked: {decision.block_reason}
        </div>
      )}

      {decision.status === "ESCALATED" && (
        <div className="mt-3 px-3 py-2 bg-warning-dim/30 border border-warning/30 rounded text-xs text-warning-text">
          Escalated: Amount ≥ ₹10,000 — requires human approval
        </div>
      )}
    </div>
  );
}
