"use client";

import { useState } from "react";
import type { EvaluationRunResult } from "@/lib/types";
import { CommandShell } from "@/components/shell/CommandShell";
import { EvaluationRunner } from "@/components/evaluation/EvaluationRunner";
import { EvaluationResults } from "@/components/evaluation/EvaluationResults";
import { MultiSeedMatrix } from "@/components/evaluation/MultiSeedMatrix";

export default function EvaluationPage() {
  const [result, setResult] = useState<EvaluationRunResult | null>(null);
  const [loading] = useState(false);

  const handleResult = (r: EvaluationRunResult) => {
    setResult(r);
  };

  return (
    <CommandShell evalResult={result}>
      <div className="mx-auto max-w-shell space-y-8 px-5 py-7 sm:px-7">
        <header className="border-b border-border-subtle pb-6">
          <h1 className="text-2xl font-bold tracking-tightest text-text-primary">
            Policy Stress Test
          </h1>
          <p className="mt-1.5 max-w-prose text-[13px] text-text-secondary">
            Same cohort · same world · same potential outcomes - only the recovery policy
            changes.
          </p>
        </header>

        <EvaluationRunner onResult={handleResult} />

        {(result || loading) && <EvaluationResults result={result} loading={loading} />}

        <div className="border-t border-border-subtle" />

        <MultiSeedMatrix />
      </div>
    </CommandShell>
  );
}
