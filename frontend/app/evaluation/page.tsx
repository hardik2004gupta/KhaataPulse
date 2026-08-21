"use client";
import { useState } from "react";
import type { EvaluationRunResult } from "@/lib/types";
import { NavBar } from "@/components/dashboard/NavBar";
import { EvaluationRunner } from "@/components/evaluation/EvaluationRunner";
import { EvaluationResults } from "@/components/evaluation/EvaluationResults";
import { MultiSeedMatrix } from "@/components/evaluation/MultiSeedMatrix";

export default function EvaluationPage() {
  const [result, setResult] = useState<EvaluationRunResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleResult = (r: EvaluationRunResult) => {
    setResult(r);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      <NavBar />

      <main className="max-w-screen-xl mx-auto px-6 py-8 space-y-10">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Policy Evaluation Engine</h1>
          <p className="text-text-muted text-sm mt-1">
            Same cohort · same world · same potential outcomes — only the recovery policy changes
          </p>
        </div>

        {/* Evaluation runner */}
        <EvaluationRunner onResult={handleResult} />

        {/* Results */}
        {(result || loading) && (
          <EvaluationResults result={result} loading={loading} />
        )}

        {/* Separator */}
        <div className="border-t border-border" />

        {/* Multi-seed validation */}
        <MultiSeedMatrix />
      </main>
    </div>
  );
}
