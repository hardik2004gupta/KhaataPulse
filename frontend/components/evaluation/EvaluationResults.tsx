"use client";
import type { EvaluationRunResult } from "@/lib/types";
import { formatINR, formatPct, formatCount } from "@/lib/utils/format";
import { Skeleton } from "@/components/ui/Skeleton";
import { Eyebrow } from "@/components/ui/StateViews";

interface EvaluationResultsProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

export function EvaluationResults({ result, loading }: EvaluationResultsProps) {
  if (loading) {
    return (
      <div className="space-y-4 rounded-panel border border-border bg-surface p-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </div>
    );
  }

  if (!result) return null;

  const { static_dunning: sd, smart_retry: sr, khaatapulse: kp } = result;
  const incr = result.incremental_recovery ? parseFloat(result.incremental_recovery) : 0;
  const positive = incr >= 0;

  const ROWS: { label: string; value: (p: typeof kp) => string }[] = [
    { label: "Recovered", value: (p) => formatINR(p.recovered_amount) },
    { label: "Rate", value: (p) => formatPct(p.recovery_rate) },
    { label: "Contacts", value: (p) => formatCount(p.contacts_sent) },
    { label: "Escalations", value: (p) => p.human_escalations.toLocaleString("en-IN") },
    { label: "Policy Blocks", value: (p) => p.policy_blocks.toLocaleString("en-IN") },
  ];

  return (
    <div className="space-y-6">
      {/* Headline incremental recovery — the primary KPI of the run. */}
      <div
        className={`relative overflow-hidden rounded-panel border p-6 text-center ${
          positive
            ? "border-recovery/30 bg-recovery-dim/30 glow-recovery"
            : "border-critical/30 bg-critical-dim/30 glow-critical"
        }`}
      >
        <div
          aria-hidden="true"
          className={`pointer-events-none absolute inset-0 ${
            positive ? "wash-recovery" : "wash-critical"
          }`}
        />
        <div className="relative">
          <Eyebrow tone={positive ? "recovery" : "critical"}>Incremental Recovery</Eyebrow>
          <p
            className={`tabular mt-3 text-3xl font-bold tracking-tightest sm:text-4xl ${
              positive ? "text-recovery-text" : "text-critical-text"
            }`}
          >
            {positive ? "+" : ""}
            {formatINR(String(incr))}
          </p>
          <p className="mono tabular mt-2 text-[10px] uppercase tracking-eyebrow text-text-faint">
            KhaataPulse − Smart Retry · seed {result.seed} · n{" "}
            {result.cohort_size.toLocaleString("en-IN")}
          </p>
        </div>
      </div>

      {/* Per-policy cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: "Static Dunning", data: sd, accent: "text-text-muted", bg: "" },
          {
            label: "Smart Retry",
            data: sr,
            accent: "text-warning-text",
            bg: "border-warning/20",
          },
          {
            label: "KhaataPulse",
            data: kp,
            accent: "text-recovery-text",
            bg: "border-recovery/30 bg-recovery-dim/20",
          },
        ].map(({ label, data, accent, bg }) => (
          <div key={label} className={`rounded-panel border border-border bg-surface p-4 ${bg}`}>
            <p className={`mono mb-3 text-[10px] uppercase tracking-eyebrow ${accent}`}>{label}</p>
            <dl className="space-y-2">
              {ROWS.map((row) => (
                <div key={row.label} className="flex justify-between gap-3 text-sm">
                  <dt className="text-text-muted">{row.label}</dt>
                  <dd
                    className={`tabular ${
                      row.label === "Recovered"
                        ? "font-bold text-text-primary"
                        : "text-text-secondary"
                    }`}
                  >
                    {row.value(data)}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
    </div>
  );
}
