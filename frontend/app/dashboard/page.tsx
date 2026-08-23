"use client";

import { useCallback, useEffect, useState } from "react";
import { evaluationApi } from "@/lib/api/evaluation";
import { demoApi } from "@/lib/api/demo";
import type { EvaluationRunResult, HeroCase, LoadingState } from "@/lib/types";
import { CommandShell } from "@/components/shell/CommandShell";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { HeroKPIGrid } from "@/components/dashboard/HeroKPIGrid";
import { IncrementalHero } from "@/components/dashboard/IncrementalHero";
import { RevenueExposure } from "@/components/dashboard/RevenueExposure";
import { PolicyComparison } from "@/components/dashboard/PolicyComparison";
import { HeroCasePanel } from "@/components/dashboard/HeroCasePanel";
import { LiveActivity } from "@/components/dashboard/LiveActivity";
import { LiveEventStream } from "@/components/simulation/LiveEventStream";
import { AuditTimeline } from "@/components/risk/AuditTimeline";
import { ErrorPanel, LoadingPanel, Eyebrow } from "@/components/ui/StateViews";

const DASHBOARD_SEED = 42;
const DASHBOARD_COHORT = 3000;
const POLL_INTERVAL_MS = 2000;
const POLL_MAX_ATTEMPTS = 60;

export default function CommandCenter() {
  const [evalState, setEvalState] = useState<LoadingState>("loading");
  const [evalResult, setEvalResult] = useState<EvaluationRunResult | null>(null);
  const [runId, setRunId] = useState<string | null>(null);

  const [heroState, setHeroState] = useState<LoadingState>("loading");
  const [hero, setHero] = useState<HeroCase | null>(null);

  // ── Evaluation ───────────────────────────────────────────────────────────
  const runEval = useCallback(async () => {
    setEvalState("loading");
    try {
      const response = await evaluationApi.runEvaluation(DASHBOARD_SEED, DASHBOARD_COHORT);
      setRunId(response.run_id);

      // The backend may complete synchronously - use the POST body when it does.
      if (response.status === "completed" && response.results) {
        setEvalResult(response.results);
        setEvalState("success");
        return;
      }

      for (let attempt = 0; attempt < POLL_MAX_ATTEMPTS; attempt++) {
        await new Promise<void>((r) => setTimeout(r, POLL_INTERVAL_MS));
        const data = await evaluationApi.getRun(response.run_id);
        if (data.status === "completed" && data.results) {
          setEvalResult(data.results);
          setEvalState("success");
          return;
        }
        if (data.status === "failed") throw new Error("Evaluation failed");
      }
      throw new Error("Evaluation timed out");
    } catch {
      setEvalState("error");
    }
  }, []);

  useEffect(() => {
    runEval();
  }, [runEval]);

  // ── Hero case ────────────────────────────────────────────────────────────
  const loadHero = useCallback(async () => {
    setHeroState("loading");
    try {
      const data = await demoApi.getHeroCase();
      setHero(data);
      setHeroState("success");
    } catch {
      setHeroState("error");
    }
  }, []);

  useEffect(() => {
    loadHero();
  }, [loadHero]);

  const evalLoading = evalState === "loading";

  return (
    <CommandShell evalResult={evalResult}>
      <div className="mx-auto max-w-shell space-y-10 px-5 py-7 sm:px-7">
        <DashboardHeader evalResult={evalResult} runId={runId} state={evalState} />

        {evalState === "error" ? (
          <ErrorPanel
            detail="The evaluation service could not be reached. Confirm the backend is running, then retry."
            onRetry={runEval}
          />
        ) : evalLoading ? (
          /* A same-cohort run takes several seconds. Say what is happening
             rather than leaving three skeleton blocks unexplained. Both figures
             are the request parameters, not authored results. */
          <LoadingPanel
            title="Running Same-Cohort Evaluation"
            detail={`Evaluating ${DASHBOARD_COHORT.toLocaleString(
              "en-IN",
            )} accounts across 3 recovery policies - static dunning, smart retry, and KhaataPulse - against one shared world (seed ${DASHBOARD_SEED}).`}
          />
        ) : (
          <>
            {/* ── Money ──────────────────────────────────────────────────── */}
            <HeroKPIGrid result={evalResult} loading={false} />

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.15fr_1fr]">
              <RevenueExposure result={evalResult} loading={false} />
              <IncrementalHero result={evalResult} loading={false} />
            </div>

            {/* ── Policy ─────────────────────────────────────────────────── */}
            <PolicyComparison result={evalResult} loading={false} />
          </>
        )}

        {/* ── Case + activity ──────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.6fr_1fr]">
          {heroState === "loading" ? (
            <LoadingPanel
              title="Reconstructing Risk Profile"
              detail="Scoring the demo cohort and replaying the recovery pipeline."
            />
          ) : hero ? (
            <HeroCasePanel hero={hero} />
          ) : (
            <ErrorPanel
              title="Hero Case Unavailable"
              detail="The demo service could not be reached."
              onRetry={loadHero}
            />
          )}

          <LiveActivity
            events={hero?.audit_events ?? []}
            loading={heroState === "loading"}
          />
        </div>

        {/* ── Live webhook ─────────────────────────────────────────────────── */}
        <LiveEventStream />

        {/* ── Governance ───────────────────────────────────────────────────── */}
        <section id="audit" className="scroll-mt-16">
          <Eyebrow>Governance</Eyebrow>
          <div className="mt-4 rounded-panel border border-border bg-surface p-5">
            {heroState === "loading" ? (
              <p className="mono py-6 text-center text-[10px] uppercase tracking-eyebrow text-text-muted">
                Replaying policy decision…
              </p>
            ) : (
              <AuditTimeline events={hero?.audit_events ?? []} />
            )}
          </div>
        </section>
      </div>
    </CommandShell>
  );
}
