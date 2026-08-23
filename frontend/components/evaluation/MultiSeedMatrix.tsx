"use client";
import { useState } from "react";
import { evaluationApi } from "@/lib/api/evaluation";
import type { MultiSeedResponse, EvaluationRunResult, LoadingState } from "@/lib/types";
import { formatINR } from "@/lib/utils/format";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorPanel, Eyebrow } from "@/components/ui/StateViews";

const REQUIRED_SEEDS = [42, 123, 456];

function avg(runs: EvaluationRunResult[], field: (r: EvaluationRunResult) => number): number {
  if (!runs.length) return 0;
  return runs.reduce((s, r) => s + field(r), 0) / runs.length;
}

export function MultiSeedMatrix() {
  const [state, setState] = useState<LoadingState>("idle");
  const [data, setData] = useState<MultiSeedResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cohortSize, setCohortSize] = useState(500);

  const run = async () => {
    setState("loading");
    setError(null);
    try {
      const result = await evaluationApi.runMultiSeed(cohortSize, REQUIRED_SEEDS);
      setData(result);
      setState("idle");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Multi-seed evaluation failed");
      setState("error");
    }
  };

  const avgIncremental = data ? avg(data.runs, (r) => parseFloat(r.incremental_recovery)) : 0;

  const HEADERS: { label: string; align: string; tone: string }[] = [
    { label: "Seed", align: "text-left", tone: "text-text-muted" },
    { label: "n", align: "text-left", tone: "text-text-muted" },
    { label: "Static Dunning", align: "text-right", tone: "text-text-muted" },
    { label: "Smart Retry", align: "text-right", tone: "text-warning-text" },
    { label: "KhaataPulse", align: "text-right", tone: "text-recovery-text" },
    { label: "Incremental", align: "text-right", tone: "text-text-muted" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Eyebrow>Multi-Seed Validation</Eyebrow>
          <p className="mt-1 max-w-prose text-xs text-text-faint">
            Seeds <span className="mono tabular">{REQUIRED_SEEDS.join(", ")}</span> — validates
            result stability across independent random worlds.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <label htmlFor="multiseed-cohort" className="sr-only">
            Cohort size
          </label>
          <select
            id="multiseed-cohort"
            value={cohortSize}
            onChange={(e) => setCohortSize(Number(e.target.value))}
            disabled={state === "loading"}
            className="mono tabular rounded border border-border bg-bg-secondary px-3 py-1.5 text-xs text-text-primary transition-colors duration-base hover:border-ai/40"
          >
            <option value={500}>n=500</option>
            <option value={1000}>n=1,000</option>
          </select>
          <button
            type="button"
            onClick={run}
            disabled={state === "loading"}
            className={`mono rounded border px-4 py-1.5 text-[10px] font-semibold uppercase tracking-eyebrow transition-colors duration-base ${
              state === "loading"
                ? "cursor-wait border-border bg-surface text-text-muted"
                : "cursor-pointer border-ai/40 bg-ai-dim text-ai-text hover:bg-ai/20"
            }`}
          >
            {state === "loading" ? "Running…" : "Run Multi-Seed"}
          </button>
        </div>
      </div>

      {state === "loading" && (
        <div className="space-y-2 rounded-panel border border-border bg-surface p-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-6 w-full" />
          ))}
        </div>
      )}

      {state === "error" && (
        <ErrorPanel
          title="Multi-Seed Run Failed"
          detail={error ?? "The evaluation service could not be reached."}
          onRetry={run}
        />
      )}

      {data && data.runs.length > 0 && (
        <div className="overflow-hidden rounded-panel border border-border bg-surface">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-xs">
              <thead>
                <tr className="border-b border-border">
                  {HEADERS.map((h) => (
                    <th
                      key={h.label}
                      className={`mono px-4 py-2.5 text-[10px] uppercase tracking-eyebrow ${h.align} ${h.tone}`}
                    >
                      {h.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.runs.map((run) => {
                  const incr = parseFloat(run.incremental_recovery);
                  return (
                    <tr
                      key={run.seed}
                      className="border-b border-border-subtle transition-colors duration-base hover:bg-surface-elevated/50"
                    >
                      <td className="mono tabular px-4 py-2.5 text-text-secondary">{run.seed}</td>
                      <td className="tabular px-4 py-2.5 text-text-muted">
                        {run.cohort_size.toLocaleString("en-IN")}
                      </td>
                      <td className="tabular px-4 py-2.5 text-right text-text-secondary">
                        {formatINR(run.static_dunning.recovered_amount)}
                      </td>
                      <td className="tabular px-4 py-2.5 text-right text-warning-text">
                        {formatINR(run.smart_retry.recovered_amount)}
                      </td>
                      <td className="tabular px-4 py-2.5 text-right font-semibold text-recovery-text">
                        {formatINR(run.khaatapulse.recovered_amount)}
                      </td>
                      <td
                        className={`tabular px-4 py-2.5 text-right font-semibold ${
                          incr >= 0 ? "text-recovery-text" : "text-critical-text"
                        }`}
                      >
                        {incr >= 0 ? "+" : ""}
                        {formatINR(String(incr))}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="border-t border-border bg-surface-elevated/50">
                  <td
                    className="mono px-4 py-2.5 text-[10px] uppercase tracking-eyebrow text-text-muted"
                    colSpan={2}
                  >
                    Avg ({data.summary.total_runs} runs)
                  </td>
                  <td className="tabular px-4 py-2.5 text-right text-text-muted">
                    {formatINR(
                      String(avg(data.runs, (r) => parseFloat(r.static_dunning.recovered_amount))),
                    )}
                  </td>
                  <td className="tabular px-4 py-2.5 text-right text-warning-text">
                    {formatINR(
                      String(avg(data.runs, (r) => parseFloat(r.smart_retry.recovered_amount))),
                    )}
                  </td>
                  <td className="tabular px-4 py-2.5 text-right font-semibold text-recovery-text">
                    {formatINR(
                      String(avg(data.runs, (r) => parseFloat(r.khaatapulse.recovered_amount))),
                    )}
                  </td>
                  <td
                    className={`tabular px-4 py-2.5 text-right font-semibold ${
                      avgIncremental >= 0 ? "text-recovery-text" : "text-critical-text"
                    }`}
                  >
                    {avgIncremental >= 0 ? "+" : ""}
                    {formatINR(String(avgIncremental))}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Summary badges */}
          <div className="flex flex-wrap gap-4 border-t border-border px-4 py-3">
            <span className="mono text-[10px] uppercase tracking-eyebrow text-text-muted">
              <span className="tabular font-semibold text-recovery-text">
                {data.summary.positive_runs}
              </span>{" "}
              / <span className="tabular">{data.summary.total_runs}</span> seeds positive
            </span>
            {data.summary.negative_runs > 0 && (
              <span className="mono tabular text-[10px] uppercase tracking-eyebrow text-critical-text">
                {data.summary.negative_runs} negative
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
