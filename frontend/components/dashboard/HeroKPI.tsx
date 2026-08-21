"use client";
import { formatINR, formatPct, formatCount } from "@/lib/utils/format";
import type { EvaluationRunResult } from "@/lib/types";
import { MetricCard } from "@/components/ui/MetricCard";
import { MetricSkeleton } from "@/components/ui/Skeleton";

interface HeroKPIProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

export function HeroKPI({ result, loading }: HeroKPIProps) {
  const kp = result?.khaatapulse;
  const sr = result?.smart_retry;

  const incrRecovery = result?.incremental_recovery ?? null;

  return (
    <section>
      {/* Primary hero metric */}
      <div className="mb-4">
        <p className="text-xs font-semibold tracking-widest uppercase text-text-muted mb-1">
          Primary KPI — Incremental Recovery
        </p>
        <p className="text-xs text-text-faint">
          KhaataPulse vs Smart Retry baseline · same cohort, same world
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <MetricSkeleton key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {/* Incremental Recovery — primary */}
          <MetricCard
            label="Incremental Recovery"
            value={incrRecovery ? formatINR(incrRecovery) : "—"}
            subValue={
              incrRecovery && sr
                ? `vs ₹${formatINR(sr.recovered_amount)} Smart Retry baseline`
                : "Run an evaluation to see results"
            }
            accent={
              incrRecovery === null ? "neutral"
              : parseFloat(incrRecovery) >= 0 ? "recovery"
              : "critical"
            }
            size="lg"
          />

          {/* KP Recovery Rate */}
          <MetricCard
            label="Recovery Rate"
            value={kp ? formatPct(kp.recovery_rate) : "—"}
            subValue={kp ? `${formatINR(kp.recovered_amount)} recovered` : undefined}
            accent="recovery"
          />

          {/* Contacts Avoided */}
          <MetricCard
            label="Contacts Avoided"
            value={kp ? formatCount(kp.contacts_avoided) : "—"}
            subValue={kp ? `${kp.contacts_sent} contacts sent of ${kp.cases_evaluated} cases` : undefined}
            accent="ai"
          />

          {/* Human Escalations */}
          <MetricCard
            label="Human Escalations"
            value={kp ? String(kp.human_escalations) : "—"}
            subValue={kp ? `${kp.false_positives} false positives · ${kp.policy_blocks} blocked` : undefined}
            accent="warning"
          />
        </div>
      )}
    </section>
  );
}
