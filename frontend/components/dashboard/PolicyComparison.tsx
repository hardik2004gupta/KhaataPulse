"use client";

import type { EvaluationRunResult, PolicyEvaluationResult } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatINR, formatPct, formatPP } from "@/lib/utils/format";

interface PolicyComparisonProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

type Direction = "up-good" | "down-good";

interface Row {
  key: string;
  label: string;
  /** Cell rendering for one policy. */
  value: (p: PolicyEvaluationResult) => string;
  /** Raw numeric used for the KhaataPulse-vs-Smart-Retry delta badge. */
  raw: (p: PolicyEvaluationResult) => number;
  /** Delta formatter. */
  delta: (d: number) => string;
  direction: Direction;
}

const ROWS: Row[] = [
  {
    key: "recovered",
    label: "Recovered",
    value: (p) => formatINR(p.recovered_amount),
    raw: (p) => parseFloat(p.recovered_amount),
    delta: (d) => `${d >= 0 ? "+" : "−"}${formatINR(Math.abs(d))}`,
    direction: "up-good",
  },
  {
    key: "rate",
    label: "Recovery Rate",
    value: (p) => formatPct(p.recovery_rate),
    raw: (p) => p.recovery_rate,
    delta: (d) => formatPP(d),
    direction: "up-good",
  },
  {
    key: "contacts_sent",
    label: "Contacts Sent",
    value: (p) => p.contacts_sent.toLocaleString("en-IN"),
    raw: (p) => p.contacts_sent,
    delta: (d) => `${d >= 0 ? "+" : "−"}${Math.abs(d).toLocaleString("en-IN")}`,
    direction: "down-good",
  },
  {
    key: "contacts_avoided",
    label: "Contacts Avoided",
    value: (p) => p.contacts_avoided.toLocaleString("en-IN"),
    raw: (p) => p.contacts_avoided,
    delta: (d) => `${d >= 0 ? "+" : "−"}${Math.abs(d).toLocaleString("en-IN")}`,
    direction: "up-good",
  },
  {
    key: "escalations",
    label: "Human Escalations",
    value: (p) => p.human_escalations.toLocaleString("en-IN"),
    raw: (p) => p.human_escalations,
    delta: (d) => `${d >= 0 ? "+" : "−"}${Math.abs(d).toLocaleString("en-IN")}`,
    direction: "down-good",
  },
  {
    key: "false_positives",
    label: "False Positives",
    value: (p) => p.false_positives.toLocaleString("en-IN"),
    raw: (p) => p.false_positives,
    delta: (d) => `${d >= 0 ? "+" : "−"}${Math.abs(d).toLocaleString("en-IN")}`,
    direction: "down-good",
  },
];

function DeltaBadge({ text, good }: { text: string; good: boolean | null }) {
  if (good === null) {
    return (
      <span className="mono rounded border border-border px-1.5 py-0.5 text-[10px] text-text-faint">
        {text}
      </span>
    );
  }
  return (
    <span
      className={`mono rounded border px-1.5 py-0.5 text-[10px] ${
        good
          ? "border-recovery/30 bg-recovery-dim/30 text-recovery-text"
          : "border-critical/30 bg-critical-dim/30 text-critical-text"
      }`}
    >
      {text}
    </span>
  );
}

export function PolicyComparison({ result, loading }: PolicyComparisonProps) {
  if (loading) {
    return (
      <section id="policy" className="scroll-mt-16">
        <Eyebrow>Policy Comparison</Eyebrow>
        <div className="mt-4 rounded-panel border border-border bg-surface p-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="mb-3 h-8 w-full" />
          ))}
        </div>
      </section>
    );
  }

  if (!result) {
    return (
      <section id="policy" className="scroll-mt-16">
        <Eyebrow>Policy Comparison</Eyebrow>
        <div className="mt-4 rounded-panel border border-border bg-surface px-6 py-10 text-center">
          <p className="text-xs text-text-muted">Awaiting evaluation run.</p>
        </div>
      </section>
    );
  }

  const policies: { key: string; label: string; data: PolicyEvaluationResult; hero: boolean }[] = [
    { key: "static", label: "Static Dunning", data: result.static_dunning, hero: false },
    { key: "smart", label: "Smart Retry", data: result.smart_retry, hero: false },
    { key: "kp", label: "KhaataPulse", data: result.khaatapulse, hero: true },
  ];

  return (
    <section id="policy" className="scroll-mt-16">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
        <Eyebrow>Policy Comparison</Eyebrow>
        <p className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
          Same cohort · same world · only the policy changes
        </p>
      </div>

      <div className="mt-4 overflow-x-auto rounded-panel border border-border bg-surface">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="mono px-5 py-3 text-left text-[10px] uppercase tracking-eyebrow text-text-faint">
                Metric
              </th>
              {policies.map((p) => (
                <th
                  key={p.key}
                  className={`px-5 py-3 text-right ${p.hero ? "bg-recovery-dim/20" : ""}`}
                >
                  <span
                    className={`mono text-[10px] uppercase tracking-eyebrow ${
                      p.hero ? "text-recovery-text" : "text-text-muted"
                    }`}
                  >
                    {p.label}
                  </span>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {ROWS.map((row) => {
              const kpRaw = row.raw(result.khaatapulse);
              const srRaw = row.raw(result.smart_retry);
              const d = kpRaw - srRaw;

              let good: boolean | null;
              if (d === 0) good = null;
              else good = row.direction === "up-good" ? d > 0 : d < 0;

              return (
                <tr
                  key={row.key}
                  className="border-b border-border-subtle last:border-b-0 transition-colors duration-base hover:bg-surface-elevated/40"
                >
                  <td className="px-5 py-3 text-[13px] text-text-secondary">{row.label}</td>

                  {policies.map((p) => (
                    <td
                      key={p.key}
                      className={`px-5 py-3 text-right ${p.hero ? "bg-recovery-dim/20" : ""}`}
                    >
                      {p.hero ? (
                        <span className="flex items-center justify-end gap-2">
                          <DeltaBadge text={row.delta(d)} good={good} />
                          <span className="tabular font-semibold text-text-primary">
                            {row.value(p.data)}
                          </span>
                        </span>
                      ) : (
                        <span className="tabular text-text-secondary">{row.value(p.data)}</span>
                      )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mono mt-3 text-[10px] uppercase tracking-eyebrow text-text-faint">
        Badges show KhaataPulse delta vs Smart Retry · seed {result.seed} · model{" "}
        {result.model_version} · simulator {result.simulator_version}
      </p>
    </section>
  );
}
