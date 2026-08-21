"use client";
import type { EvaluationRunResult } from "@/lib/types";
import { formatINR, formatPct, formatCount } from "@/lib/utils/format";
import { Skeleton } from "@/components/ui/Skeleton";

interface EvaluationResultsProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

export function EvaluationResults({ result, loading }: EvaluationResultsProps) {
  if (loading) {
    return (
      <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
        {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
      </div>
    );
  }

  if (!result) return null;

  const { static_dunning: sd, smart_retry: sr, khaatapulse: kp } = result;
  const incr = result.incremental_recovery ? parseFloat(result.incremental_recovery) : 0;

  return (
    <div className="space-y-6">
      {/* Headline incremental recovery */}
      <div className="bg-recovery-dim/30 border border-recovery/30 rounded-lg p-6 text-center">
        <p className="text-xs text-text-muted uppercase tracking-widest font-semibold mb-2">
          Incremental Recovery
        </p>
        <p className={`text-4xl font-bold tabular ${incr >= 0 ? "text-recovery-text" : "text-critical-text"}`}>
          {incr >= 0 ? "+" : ""}{formatINR(String(incr))}
        </p>
        <p className="text-xs text-text-faint mt-2">
          KhaataPulse − Smart Retry · seed={result.seed} · n={result.cohort_size.toLocaleString()}
        </p>
      </div>

      {/* Per-policy cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Static Dunning", data: sd, accent: "text-text-muted", bg: "" },
          { label: "Smart Retry",    data: sr, accent: "text-warning-text", bg: "border-warning/20" },
          { label: "KhaataPulse",    data: kp, accent: "text-recovery-text", bg: "border-recovery/30 bg-recovery-dim/20" },
        ].map(({ label, data, accent, bg }) => (
          <div key={label} className={`bg-surface border border-border rounded-lg p-4 ${bg}`}>
            <p className={`text-sm font-semibold mb-3 ${accent}`}>{label}</p>
            <dl className="space-y-2">
              <div className="flex justify-between text-sm">
                <dt className="text-text-muted">Recovered</dt>
                <dd className="tabular font-bold text-text-primary">{formatINR(data.recovered_amount)}</dd>
              </div>
              <div className="flex justify-between text-sm">
                <dt className="text-text-muted">Rate</dt>
                <dd className="tabular text-text-secondary">{formatPct(data.recovery_rate)}</dd>
              </div>
              <div className="flex justify-between text-sm">
                <dt className="text-text-muted">Contacts</dt>
                <dd className="tabular text-text-secondary">{formatCount(data.contacts_sent)}</dd>
              </div>
              <div className="flex justify-between text-sm">
                <dt className="text-text-muted">Escalations</dt>
                <dd className="tabular text-text-secondary">{data.human_escalations}</dd>
              </div>
              <div className="flex justify-between text-sm">
                <dt className="text-text-muted">Policy Blocks</dt>
                <dd className="tabular text-text-secondary">{data.policy_blocks}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </div>
  );
}
