"use client";
import { useState } from "react";
import { evaluationApi } from "@/lib/api/evaluation";
import type { EvaluationRunResult, LoadingState } from "@/lib/types";

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
    <div className="bg-surface border border-border rounded-lg p-5">
      <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-4">
        Run Evaluation
      </p>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs text-text-muted mb-1.5">Cohort Size</label>
          <select
            value={cohortSize}
            onChange={(e) => setCohortSize(Number(e.target.value))}
            disabled={state === "loading"}
            className="w-full bg-bg-secondary border border-border rounded px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-ai/60"
          >
            <option value={500}>500 customers</option>
            <option value={1000}>1,000 customers</option>
            <option value={3000}>3,000 customers (spec)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-text-muted mb-1.5">Random Seed</label>
          <select
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
            disabled={state === "loading"}
            className="w-full bg-bg-secondary border border-border rounded px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-ai/60"
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
        onClick={run}
        disabled={state === "loading"}
        className={`w-full py-2.5 text-sm font-semibold rounded border transition-all ${
          state === "loading"
            ? "bg-surface-elevated border-border text-text-muted cursor-wait"
            : "bg-ai-dim border-ai/40 text-ai-text hover:bg-ai/20 cursor-pointer"
        }`}
      >
        {state === "loading" ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-pulse w-1.5 h-1.5 rounded-full bg-ai inline-block" />
            {pollMsg}
          </span>
        ) : (
          "▶ Run Same-Cohort Evaluation"
        )}
      </button>

      {state === "error" && (
        <p className="mt-2 text-xs text-critical-text">{error}</p>
      )}

      {runId && state !== "error" && (
        <p className="mt-2 mono text-xs text-text-faint">run_id: {runId}</p>
      )}
    </div>
  );
}
