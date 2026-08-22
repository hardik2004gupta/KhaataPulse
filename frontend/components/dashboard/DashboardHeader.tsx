"use client";

import type { EvaluationRunResult, LoadingState } from "@/lib/types";

interface DashboardHeaderProps {
  evalResult: EvaluationRunResult | null;
  runId: string | null;
  state: LoadingState;
}

export function DashboardHeader({ evalResult, runId, state }: DashboardHeaderProps) {
  const activeRun = evalResult?.run_id ?? runId ?? "";

  let badge: string;
  let badgeTone: string;

  if (state === "error") {
    badge = "EVALUATION UNAVAILABLE";
    badgeTone = "border-critical/30 bg-critical-dim/20 text-critical-text";
  } else if (evalResult) {
    badge = `RUN · ${activeRun} · SEED ${evalResult.seed} · ${evalResult.cohort_size.toLocaleString(
      "en-IN",
    )} ACCOUNTS`;
    badgeTone = "border-recovery/25 bg-recovery-dim/20 text-recovery-text";
  } else {
    badge = "INITIALIZING EVALUATION…";
    badgeTone = "border-ai/30 bg-ai-dim/25 text-ai-text";
  }

  return (
    <header className="flex flex-col gap-4 border-b border-border-subtle pb-6 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tightest text-text-primary sm:text-[28px]">
          Revenue Recovery Command Center
        </h1>
        <p className="mt-1.5 max-w-prose text-[13px] text-text-secondary">
          Live evaluation of KhaataPulse against established recovery policies.
        </p>
      </div>

      <span
        className={`mono shrink-0 self-start rounded border px-3 py-1.5 text-[10px] uppercase tracking-eyebrow lg:self-auto ${badgeTone}`}
      >
        {badge}
      </span>
    </header>
  );
}
