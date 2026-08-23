"use client";
import { useState } from "react";
import { evaluationApi } from "@/lib/api/evaluation";
import type { EvaluationRunResult, LoadingState } from "@/lib/types";
import { ErrorPanel, Eyebrow } from "@/components/ui/StateViews";

interface EvaluationRunnerProps {
  onResult: (result: EvaluationRunResult) => void;
}

export function EvaluationRunner({ onResult }: EvaluationRunnerProps) {
  const [cohortSize, setCohortSize] = useState(3000);
  const [seed, setSeed] = useState(42);
  const [state, setState] = useState<LoadingState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [pollMsg, setPollMsg] = useState<string>("");

  const run = async () => {
    setState("loading");
    setError(null);
    setPollMsg("Running evaluation…");

    try {
      // POST runs synchronously and returns completed result immediately.
      // If backend ever moves to async, the GET polling path below handles it.
      const response = await evaluationApi.runEvaluation(seed, cohortSize);
      setRunId(response.run_id);

      if (response.status === "completed" && response.results) {
        onResult(response.results);
        setState("idle");
        setPollMsg("");
        return;
      }

      // Async fallback: poll GET until completed or failed (max 120s)
      setPollMsg("Evaluation running…");
      let attempts = 0;
      while (attempts < 60) {
        await new Promise<void>((r) => setTimeout(r, 2000));
        const data = await evaluationApi.getRun(response.run_id);
        if (data.status === "completed" && data.results) {
          onResult(data.results);
          setState("idle");
          setPollMsg("");
          return;
        }
        if (data.status === "failed") {
          throw new Error("Evaluation run failed on the server.");
        }
        attempts++;
        setPollMsg(`Processing… (${attempts * 2}s)`);
      }
      throw new Error("Evaluation timed out after 120s.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evaluation failed");
      setState("error");
      setPollMsg("");
    }
  };

  return (
    <div className="rounded-panel border border-border bg-surface p-5">
      <Eyebrow>Run Evaluation</Eyebrow>

      <div className="mb-4 mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label
            htmlFor="eval-cohort-size"
            className="mono mb-1.5 block text-[10px] uppercase tracking-eyebrow text-text-muted"
          >
            Cohort Size
          </label>
          <select
            id="eval-cohort-size"
            value={cohortSize}
            onChange={(e) => setCohortSize(Number(e.target.value))}
            disabled={state === "loading"}
            className="tabular w-full rounded border border-border bg-bg-secondary px-3 py-2 text-sm text-text-primary transition-colors duration-base hover:border-ai/40"
          >
            <option value={500}>500 customers</option>
            <option value={1000}>1,000 customers</option>
            <option value={3000}>3,000 customers (spec)</option>
          </select>
        </div>
        <div>
          <label
            htmlFor="eval-seed"
            className="mono mb-1.5 block text-[10px] uppercase tracking-eyebrow text-text-muted"
          >
            Random Seed
          </label>
          <select
            id="eval-seed"
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
            disabled={state === "loading"}
            className="mono tabular w-full rounded border border-border bg-bg-secondary px-3 py-2 text-sm text-text-primary transition-colors duration-base hover:border-ai/40"
          >
            <option value={42}>42 (default)</option>
            <option value={123}>123</option>
            <option value={456}>456</option>
            <option value={789}>789</option>
            <option value={1337}>1337</option>
          </select>
        </div>
      </div>

      <button
        type="button"
        onClick={run}
        disabled={state === "loading"}
        className={`mono w-full rounded border py-2.5 text-[11px] font-semibold uppercase tracking-eyebrow transition-colors duration-base ${
          state === "loading"
            ? "cursor-wait border-border bg-surface-elevated text-text-muted"
            : "cursor-pointer border-ai/40 bg-ai-dim text-ai-text hover:bg-ai/20"
        }`}
      >
        {state === "loading" ? (
          <span className="flex items-center justify-center gap-2">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-ai animate-pulse-glow" />
            {pollMsg}
          </span>
        ) : (
          "▶ Run Same-Cohort Evaluation"
        )}
      </button>

      {state === "error" && (
        <ErrorPanel
          className="mt-4"
          title="Evaluation Failed"
          detail={error ?? "The evaluation service could not be reached."}
          onRetry={run}
        />
      )}

      {runId && state !== "error" && (
        <p className="mono mt-2 text-xs text-text-faint">run_id: {runId}</p>
      )}
    </div>
  );
}
