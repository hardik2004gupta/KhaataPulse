"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { demoApi } from "@/lib/api/demo";
import type { HeroCase, LoadingState } from "@/lib/types";
import { CommandShell } from "@/components/shell/CommandShell";
import { EventTimeline, buildTimeline } from "@/components/timemachine/EventTimeline";
import { ErrorPanel, LoadingPanel, Eyebrow } from "@/components/ui/StateViews";
import { formatINR, formatDateTime, riskTextClass } from "@/lib/utils/format";

export default function TimeMachinePage() {
  const [state, setState] = useState<LoadingState>("loading");
  const [hero, setHero] = useState<HeroCase | null>(null);

  const load = useCallback(async () => {
    setState("loading");
    try {
      const data = await demoApi.getHeroCase();
      setHero(data);
      setState("success");
    } catch {
      setState("error");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const entries = useMemo(() => (hero ? buildTimeline(hero) : []), [hero]);

  // Colour follows the score against the sieve's thresholds, not the label.
  const riskTone = riskTextClass(hero?.risk.risk_score ?? 0);

  return (
    <CommandShell>
      <div className="mx-auto max-w-shell space-y-7 px-5 py-7 sm:px-7">
        {/* ── Page header ──────────────────────────────────────────────────── */}
        <header className="border-b border-border-subtle pb-6">
          <h1 className="text-2xl font-bold tracking-tightest text-text-primary">
            Revenue Time Machine
          </h1>
          <p className="mt-1.5 max-w-prose text-[13px] text-text-secondary">
            Cinematic reconstruction of one account - the observable signals the agent saw, and
            every decision it derived from them.
          </p>
        </header>

        {state === "loading" && (
          <LoadingPanel
            title="Reconstructing Customer Timeline"
            detail="Replaying the observable event stream and the recorded pipeline decisions."
          />
        )}

        {state === "error" && (
          <ErrorPanel
            title="Time Machine Unavailable"
            detail="The demo service could not be reached."
            onRetry={load}
          />
        )}

        {hero && state === "success" && (
          <>
            {/* ── Customer header ────────────────────────────────────────── */}
            <section className="rounded-panel border border-border bg-surface px-5 py-4">
              <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <Eyebrow>Subject</Eyebrow>
                  <p className="mt-1.5 truncate text-lg font-semibold text-text-primary">
                    {hero.customer.name}
                  </p>
                  <p className="mono mt-0.5 truncate text-[10px] uppercase tracking-eyebrow text-text-muted">
                    ID {hero.customer.id} · {hero.customer.segment} · {hero.subscription.plan}
                  </p>
                </div>

                <dl className="grid grid-cols-3 gap-5 sm:gap-8">
                  <div>
                    <dt className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
                      Renewal
                    </dt>
                    <dd className="tabular mt-1 text-lg font-bold text-text-primary">
                      {formatINR(hero.subscription.amount)}
                    </dd>
                    <dd className="mono mt-0.5 text-[9px] text-text-faint">
                      {formatDateTime(hero.subscription.renewal_at)}
                    </dd>
                  </div>

                  <div>
                    <dt className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
                      Risk
                    </dt>
                    <dd className={`tabular mt-1 text-lg font-bold ${riskTone}`}>
                      {Math.round(hero.risk.risk_score * 100)}%
                    </dd>
                    <dd className="mono mt-0.5 text-[9px] text-text-faint">
                      {hero.risk.risk_level}
                    </dd>
                  </div>

                  <div>
                    <dt className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
                      LTV
                    </dt>
                    <dd className="tabular mt-1 text-lg font-bold text-text-secondary">
                      {formatINR(hero.customer.ltv)}
                    </dd>
                    <dd className="mono mt-0.5 text-[9px] text-text-faint">lifetime</dd>
                  </div>
                </dl>
              </div>
            </section>

            {/* ── Timeline ───────────────────────────────────────────────── */}
            <section>
              <div className="flex items-baseline justify-between gap-3">
                <Eyebrow>Reconstruction</Eyebrow>
                <span className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
                  {entries.length} entries · observable data only
                </span>
              </div>

              <div className="mt-5">
                <EventTimeline entries={entries} />
              </div>
            </section>
          </>
        )}
      </div>
    </CommandShell>
  );
}
