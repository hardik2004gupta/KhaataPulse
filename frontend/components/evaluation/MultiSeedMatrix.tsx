"use client";
import { useState } from "react";
import { evaluationApi } from "@/lib/api/evaluation";
import type { MultiSeedResponse, EvaluationRunResult, LoadingState } from "@/lib/types";
import { formatINR } from "@/lib/utils/format";
import { Skeleton } from "@/components/ui/Skeleton";

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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-0.5">
            Multi-Seed Validation
          </p>
          <p className="text-xs text-text-faint">
            Seeds {REQUIRED_SEEDS.join(", ")} — validates result stability across random worlds
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={cohortSize}
            onChange={(e) => setCohortSize(Number(e.target.value))}
            disabled={state === "loading"}
            className="bg-bg-secondary border border-border rounded px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-ai/60"
          >
            <option value={500}>n=500</option>
            <option value={1000}>n=1,000</option>
          </select>
          <button
            onClick={run}
            disabled={state === "loading"}
            className={`px-4 py-1.5 text-xs font-semibold rounded border transition-all ${
              state === "loading"
                ? "bg-surface border-border text-text-muted cursor-wait"
                : "bg-ai-dim border-ai/40 text-ai-text hover:bg-ai/20 cursor-pointer"
            }`}
          >
            {state === "loading" ? "Running…" : "Run Multi-Seed"}
          </button>
        </div>
      </div>

      {state === "loading" && (
        <div className="bg-surface border border-border rounded-lg p-4 space-y-2">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-6 w-full" />)}
        </div>
      )}

      {state === "error" && (
        <p className="text-xs text-critical-text">{error}</p>
      )}

      {data && data.runs.length > 0 && (
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-2.5 text-text-muted font-semibold uppercase tracking-wider">Seed</th>
                  <th className="text-left px-4 py-2.5 text-text-muted font-semibold uppercase tracking-wider">n</th>
                  <th className="text-right px-4 py-2.5 text-text-muted font-semibold uppercase tracking-wider">Static Dunning</th>
                  <th className="text-right px-4 py-2.5 text-warning-text font-semibold uppercase tracking-wider">Smart Retry</th>
                  <th className="text-right px-4 py-2.5 text-recovery-text font-semibold uppercase tracking-wider">KhaataPulse</th>
                  <th className="text-right px-4 py-2.5 text-text-muted font-semibold uppercase tracking-wider">Incremental</th>
                </tr>
              </thead>
              <tbody>
                {data.runs.map((run) => {
                  const incr = parseFloat(run.incremental_recovery);
                  return (
                    <tr key={run.seed} className="border-b border-border/60 hover:bg-surface-elevated/50">
                      <td className="mono px-4 py-2.5 text-text-secondary">{run.seed}</td>
                      <td className="tabular px-4 py-2.5 text-text-muted">{run.cohort_size.toLocaleString()}</td>
                      <td className="tabular text-right px-4 py-2.5 text-text-secondary">
                        {formatINR(run.static_dunning.recovered_amount)}
                      </td>
                      <td className="tabular text-right px-4 py-2.5 text-warning-text">
                        {formatINR(run.smart_retry.recovered_amount)}
                      </td>
                      <td className="tabular text-right px-4 py-2.5 text-recovery-text font-semibold">
                        {formatINR(run.khaatapulse.recovered_amount)}
                      </td>
                      <td className={`tabular text-right px-4 py-2.5 font-semibold ${incr >= 0 ? "text-recovery-text" : "text-critical-text"}`}>
                        {incr >= 0 ? "+" : ""}{formatINR(String(incr))}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="border-t border-border bg-surface-elevated/50">
                  <td className="px-4 py-2.5 text-text-muted font-semibold" colSpan={2}>
                    Avg ({data.summary.total_runs} runs)
                  </td>
                  <td className="tabular text-right px-4 py-2.5 text-text-muted">
                    {formatINR(String(avg(data.runs, r => parseFloat(r.static_dunning.recovered_amount))))}
                  </td>
                  <td className="tabular text-right px-4 py-2.5 text-warning-text">
                    {formatINR(String(avg(data.runs, r => parseFloat(r.smart_retry.recovered_amount))))}
                  </td>
                  <td className="tabular text-right px-4 py-2.5 text-recovery-text font-semibold">
                    {formatINR(String(avg(data.runs, r => parseFloat(r.khaatapulse.recovered_amount))))}
                  </td>
                  <td className={`tabular text-right px-4 py-2.5 font-semibold ${
                    avg(data.runs, r => parseFloat(r.incremental_recovery)) >= 0 ? "text-recovery-text" : "text-critical-text"
                  }`}>
                    +{formatINR(String(avg(data.runs, r => parseFloat(r.incremental_recovery))))}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Summary badges */}
          <div className="px-4 py-3 border-t border-border flex gap-4 text-xs">
            <span className="text-text-muted">
              <span className="font-semibold text-recovery-text">{data.summary.positive_runs}</span> / {data.summary.total_runs} seeds positive
            </span>
            {data.summary.negative_runs > 0 && (
              <span className="text-critical-text">{data.summary.negative_runs} negative</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
