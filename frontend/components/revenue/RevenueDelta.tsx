"use client";
import { formatINR, formatPct } from "@/lib/utils/format";
import type { EvaluationRunResult } from "@/lib/types";
import { Skeleton } from "@/components/ui/Skeleton";

interface RevenueDeltaProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

export function RevenueDelta({ result, loading }: RevenueDeltaProps) {
  const policies = result
    ? [
        { key: "static_dunning", label: "Static Dunning", amount: result.static_dunning.recovered_amount, rate: result.static_dunning.recovery_rate, color: "#475569", width: 0 },
        { key: "smart_retry",    label: "Smart Retry",    amount: result.smart_retry.recovered_amount,    rate: result.smart_retry.recovery_rate,    color: "#F59E0B", width: 0 },
        { key: "khaatapulse",    label: "KhaataPulse",   amount: result.khaatapulse.recovered_amount,    rate: result.khaatapulse.recovery_rate,    color: "#10B981", width: 0 },
      ]
    : [];

  const maxAmount = policies.length
    ? Math.max(...policies.map(p => parseFloat(p.amount)))
    : 1;
  const policiesWithWidth = policies.map(p => ({
    ...p,
    width: maxAmount > 0 ? (parseFloat(p.amount) / maxAmount) * 100 : 0,
  }));

  return (
    <section>
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <p className="text-xs font-semibold tracking-widest uppercase text-text-muted mb-0.5">
            Revenue Time Machine
          </p>
          <p className="text-xs text-text-faint">
            Revenue recovered per policy — same cohort, evaluated in parallel
          </p>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg p-6">
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : !result ? (
          <p className="text-text-muted text-sm text-center py-8">
            Run an evaluation to visualize revenue recovery across policies.
          </p>
        ) : (
          <div className="space-y-5">
            {policiesWithWidth.map((p) => (
              <div key={p.key}>
                <div className="flex items-baseline justify-between mb-2">
                  <span className={`text-sm font-semibold ${p.key === "khaatapulse" ? "text-recovery-text" : "text-text-secondary"}`}>
                    {p.label}
                  </span>
                  <div className="flex items-baseline gap-3">
                    <span className="tabular font-bold text-text-primary">{formatINR(p.amount)}</span>
                    <span className="text-xs text-text-muted tabular">{formatPct(p.rate)}</span>
                  </div>
                </div>
                <div className="h-3 bg-surface-elevated rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${p.width}%`, backgroundColor: p.color }}
                  />
                </div>
              </div>
            ))}

            {/* Incremental Recovery delta callout */}
            {result.incremental_recovery && (
              <div className="mt-6 pt-4 border-t border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-text-muted uppercase tracking-wider font-semibold">
                      Incremental Recovery
                    </p>
                    <p className="text-xs text-text-faint mt-0.5">
                      KhaataPulse − Smart Retry baseline
                    </p>
                  </div>
                  <span className={`tabular font-bold text-xl ${parseFloat(result.incremental_recovery) >= 0 ? "text-recovery-text" : "text-critical-text"}`}>
                    {parseFloat(result.incremental_recovery) >= 0 ? "+" : ""}
                    {formatINR(result.incremental_recovery)}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
