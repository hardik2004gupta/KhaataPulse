"use client";
import { useEffect, useState, useCallback } from "react";
import { evaluationApi } from "@/lib/api/evaluation";
import { demoApi } from "@/lib/api/demo";
import type { EvaluationRunResult, HeroCase, LoadingState } from "@/lib/types";
import { NavBar } from "@/components/dashboard/NavBar";
import { HeroKPI } from "@/components/dashboard/HeroKPI";
import { PolicyMatrix } from "@/components/dashboard/PolicyMatrix";
import { RevenueDelta } from "@/components/revenue/RevenueDelta";
import { LiveEventStream } from "@/components/simulation/LiveEventStream";
import { DiagnosisPanel } from "@/components/risk/DiagnosisPanel";
import { PolicyGuardViz } from "@/components/risk/PolicyGuardViz";
import { AuditTimeline } from "@/components/risk/AuditTimeline";
import { formatINR } from "@/lib/utils/format";

function HeroCasePanel({ hero }: { hero: HeroCase }) {
  return (
    <section>
      <div className="mb-4">
        <p className="text-xs font-semibold tracking-widest uppercase text-text-muted mb-0.5">
          Hero Case — Deterministic Seed 42
        </p>
        <p className="text-xs text-text-faint">
          Highest-risk customer from the demo cohort — full pipeline executed
        </p>
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        {/* Customer bar */}
        <div className="px-5 py-4 border-b border-border bg-surface-elevated flex items-center justify-between">
          <div>
            <p className="font-semibold text-text-primary">{hero.customer.name}</p>
            <p className="text-xs text-text-muted mono mt-0.5">
              {hero.customer.segment} · LTV {formatINR(String(hero.customer.ltv))}
            </p>
          </div>
          <div className="text-right">
            <p className="tabular font-bold text-xl text-text-primary">
              {formatINR(hero.subscription.amount)}
            </p>
            <p className="text-xs text-text-muted">renewal exposure</p>
          </div>
        </div>

        {/* Three-column content */}
        <div className="grid grid-cols-3 divide-x divide-border">
          <div className="p-5">
            <DiagnosisPanel
              risk={hero.risk}
              diagnosis={hero.diagnosis}
              actionRankings={hero.action_rankings}
            />
          </div>
          <div className="p-5">
            <PolicyGuardViz decision={hero.policy_decision} />
          </div>
          <div className="p-5 overflow-y-auto max-h-96">
            <AuditTimeline events={hero.audit_events} />
          </div>
        </div>
      </div>
    </section>
  );
}

export default function CommandCenter() {
  const [evalState, setEvalState] = useState<LoadingState>("loading");
  const [evalResult, setEvalResult] = useState<EvaluationRunResult | null>(null);
  const [evalRunId, setEvalRunId] = useState<string | null>(null);

  const [heroState, setHeroState] = useState<LoadingState>("loading");
  const [hero, setHero] = useState<HeroCase | null>(null);

  // Fetch hero case
  useEffect(() => {
    demoApi.getHeroCase()
      .then(setHero)
      .catch(() => {/* hero unavailable without backend — non-fatal */})
      .finally(() => setHeroState("idle"));
  }, []);

  // Run seed-42 evaluation for the dashboard
  const runEval = useCallback(async () => {
    setEvalState("loading");
    try {
      const { run_id } = await evaluationApi.runEvaluation(42, 3000);
      setEvalRunId(run_id);

      let attempts = 0;
      while (attempts < 60) {
        await new Promise<void>((r) => setTimeout(r, 2000));
        const data = await evaluationApi.getRun(run_id);
        if (data.status === "completed" && data.results) {
          setEvalResult(data.results);
          setEvalState("idle");
          return;
        }
        if (data.status === "failed") throw new Error("Evaluation failed");
        attempts++;
      }
      throw new Error("Timeout");
    } catch {
      setEvalState("error");
    }
  }, []);

  useEffect(() => { runEval(); }, [runEval]);

  return (
    <div className="min-h-screen bg-bg-primary">
      <NavBar />

      <main className="max-w-screen-xl mx-auto px-6 py-8 space-y-10">
        {/* 1 — Hero KPIs */}
        <HeroKPI result={evalResult} loading={evalState === "loading"} />

        {/* 2 — Policy Comparison */}
        <PolicyMatrix result={evalResult} loading={evalState === "loading"} />

        {/* 3 — Revenue Time Machine */}
        <RevenueDelta result={evalResult} loading={evalState === "loading"} />

        {/* 4 — Hero Case */}
        {(heroState === "loading" || hero) && (
          <section>
            {heroState === "loading" ? (
              <div className="bg-surface border border-border rounded-lg h-48 flex items-center justify-center">
                <p className="text-text-muted text-sm animate-pulse">Loading hero case…</p>
              </div>
            ) : hero ? (
              <HeroCasePanel hero={hero} />
            ) : null}
          </section>
        )}

        {/* 5 — Live Pipeline Simulation */}
        <LiveEventStream />
      </main>
    </div>
  );
}
