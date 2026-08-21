"use client";
import { formatINR, formatPct, formatCount } from "@/lib/utils/format";
import type { EvaluationRunResult, PolicyEvaluationResult } from "@/lib/types";
import { Skeleton } from "@/components/ui/Skeleton";

interface PolicyMatrixProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

const POLICY_META: Record<string, { label: string; accent: string; desc: string }> = {
  static_dunning: {
    label:  "Static Dunning",
    accent: "text-text-muted",
    desc:   "Fixed 24h retry → escalation",
  },
  smart_retry: {
    label:  "Smart Retry",
    accent: "text-warning-text",
    desc:   "Failure-code routing → payment link",
  },
  khaatapulse: {
    label:  "KhaataPulse",
    accent: "text-recovery-text",
    desc:   "Risk → AI → Optimizer → Policy Guard",
  },
};

const METRICS: Array<{
  key: keyof PolicyEvaluationResult;
  label: string;
  format: (v: unknown) => string;
  highlight?: boolean;
}> = [
  { key: "recovered_amount",    label: "Recovered",           format: (v) => formatINR(String(v)),          highlight: true },
  { key: "recovery_rate",       label: "Recovery Rate",       format: (v) => formatPct(v as number)         },
  { key: "contacts_sent",       label: "Contacts Sent",       format: (v) => formatCount(v as number)       },
  { key: "contacts_avoided",    label: "Contacts Avoided",    format: (v) => formatCount(v as number)       },
  { key: "human_escalations",   label: "Human Escalations",   format: (v) => String(v)                      },
  { key: "false_positives",     label: "False Positives",     format: (v) => String(v)                      },
  { key: "policy_blocks",       label: "Policy Blocks",       format: (v) => String(v)                      },
  { key: "cases_evaluated",     label: "Cases Evaluated",     format: (v) => formatCount(v as number)       },
];

export function PolicyMatrix({ result, loading }: PolicyMatrixProps) {
  const policies: Array<[string, PolicyEvaluationResult]> = result
    ? [
        ["static_dunning", result.static_dunning],
        ["smart_retry",    result.smart_retry],
        ["khaatapulse",    result.khaatapulse],
      ]
    : [];

  return (
    <section>
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <p className="text-xs font-semibold tracking-widest uppercase text-text-muted mb-0.5">
            Policy Comparison Matrix
          </p>
          <p className="text-xs text-text-faint">
            Same cohort · same world · same potential outcomes — only the policy changes
          </p>
        </div>
        {result && (
          <p className="mono text-xs text-text-muted">
            seed={result.seed} · n={result.cohort_size.toLocaleString()}
          </p>
        )}
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-5 w-full" />
            ))}
          </div>
        ) : !result ? (
          <div className="py-12 text-center text-text-muted text-sm">
            Run an evaluation to populate the policy comparison matrix.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 text-text-muted text-xs font-semibold uppercase tracking-wider w-36">
                    Metric
                  </th>
                  {policies.map(([key]) => {
                    const meta = POLICY_META[key];
                    const isKP = key === "khaatapulse";
                    return (
                      <th
                        key={key}
                        className={`text-right px-4 py-3 ${isKP ? "bg-recovery-dim/30" : ""}`}
                      >
                        <p className={`font-semibold ${meta.accent}`}>{meta.label}</p>
                        <p className="text-xs text-text-faint font-normal mt-0.5">{meta.desc}</p>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {METRICS.map(({ key, label, format, highlight }) => (
                  <tr
                    key={key}
                    className="border-b border-border/60 hover:bg-surface-elevated/50 transition-colors"
                  >
                    <td className="px-4 py-3 text-text-muted text-xs font-medium uppercase tracking-wide">
                      {label}
                    </td>
                    {policies.map(([policyKey, policyData]) => {
                      const isKP = policyKey === "khaatapulse";
                      const raw = policyData[key];
                      const formatted = raw !== undefined && raw !== null ? format(raw) : "—";
                      return (
                        <td
                          key={policyKey}
                          className={`
                            px-4 py-3 text-right tabular font-semibold
                            ${isKP ? "bg-recovery-dim/20" : ""}
                            ${isKP && highlight ? "text-recovery-text text-base" : "text-text-primary"}
                          `}
                        >
                          {formatted}
                          {isKP && key === "recovered_amount" && result.incremental_recovery && (
                            <span className={`ml-2 text-xs mono ${parseFloat(result.incremental_recovery) >= 0 ? "text-recovery-text" : "text-critical-text"}`}>
                              {parseFloat(result.incremental_recovery) >= 0 ? "+" : ""}{formatINR(result.incremental_recovery)}
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
