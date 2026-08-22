"use client";

import type { EvaluationRunResult } from "@/lib/types";
import { MetricCard } from "@/components/ui/MetricCard";
import { MetricSkeleton } from "@/components/ui/Skeleton";
import { formatINR, formatPct, formatPP, formatCount } from "@/lib/utils/format";

interface HeroKPIGridProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

export function HeroKPIGrid({ result, loading }: HeroKPIGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <MetricSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!result) {
    return (
      <div className="rounded-panel border border-border bg-surface px-5 py-8 text-center">
        <p className="text-xs text-text-muted">Run evaluation to populate metrics.</p>
      </div>
    );
  }

  const kp = result.khaatapulse;
  const sr = result.smart_retry;

  const rateLift = kp.recovery_rate - sr.recovery_rate;
  const contactDelta = sr.contacts_sent - kp.contacts_sent;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
      {/* Incremental recovery is deliberately absent here — it owns the
          dominant hero panel below and must not compete with itself. */}
      <MetricCard
        label="Recovered · KhaataPulse"
        value={formatINR(kp.recovered_amount)}
        subValue={`of ${formatINR(kp.total_at_risk_amount)} at risk`}
        accent="recovery"
        size="lg"
        className="col-span-2 lg:col-span-1 lg:row-span-2"
      />
      <MetricCard
        label="KP Recovery Rate"
        value={formatPct(kp.recovery_rate)}
        subValue={`${formatPP(rateLift)} vs Smart Retry`}
        accent="recovery"
      />
      <MetricCard
        label="Revenue Exposure"
        value={formatINR(kp.total_at_risk_amount)}
        subValue={`${formatCount(kp.cases_evaluated)} cases evaluated`}
        accent="warning"
      />
      <MetricCard
        label="Contacts Avoided"
        value={formatCount(kp.contacts_avoided)}
        subValue={`${contactDelta >= 0 ? "−" : "+"}${Math.abs(
          contactDelta,
        )} contacts vs Smart Retry`}
        accent="ai"
      />
      {/* The escalation threshold is config-driven server-side (§11/§25), so it
          is described here rather than restated as a literal amount. */}
      <MetricCard
        label="Human Escalations"
        value={formatCount(kp.human_escalations)}
        subValue="above auto-action limit"
        accent="warning"
      />
      <MetricCard
        label="Policy Blocks"
        value={formatCount(kp.policy_blocks)}
        subValue="stopped by Policy Guard"
        accent={kp.policy_blocks > 0 ? "critical" : "neutral"}
      />
    </div>
  );
}
