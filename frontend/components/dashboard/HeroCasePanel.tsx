"use client";

import Link from "next/link";
import type { HeroCase } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import { DiagnosisPanel } from "@/components/risk/DiagnosisPanel";
import { PolicyGuardViz } from "@/components/risk/PolicyGuardViz";
import { formatINR, formatAction, formatDateTime } from "@/lib/utils/format";

interface HeroCasePanelProps {
  hero: HeroCase;
}

const EXEC_TONE: Record<string, string> = {
  executed: "text-recovery-text",
  escalated: "text-warning-text",
  blocked: "text-critical-text",
};

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">{label}</dt>
      <dd className="mt-1 text-[13px] text-text-secondary">{value}</dd>
    </div>
  );
}

export function HeroCasePanel({ hero }: HeroCasePanelProps) {
  const lastPayment = hero.payments[hero.payments.length - 1];
  const execTone = EXEC_TONE[hero.execution.status] ?? "text-text-secondary";

  return (
    <section className="flex h-full flex-col rounded-panel border border-border bg-surface">
      {/* ── Customer ─────────────────────────────────────────────────────── */}
      <header className="border-b border-border bg-surface-elevated/60 px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <Eyebrow>Hero Case</Eyebrow>
            <p className="mt-1.5 truncate font-semibold text-text-primary">
              {hero.customer.name}
            </p>
            <p className="mono mt-0.5 truncate text-[10px] uppercase tracking-eyebrow text-text-muted">
              {hero.customer.segment} · LTV {formatINR(hero.customer.ltv)} · ID{" "}
              {hero.customer.id}
            </p>
          </div>

          <div className="shrink-0 text-right">
            <p className="tabular text-xl font-bold text-text-primary">
              {formatINR(hero.subscription.amount)}
            </p>
            <p className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
              Renewal exposure
            </p>
          </div>
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-border-subtle pt-3 sm:grid-cols-3">
          <Field label="Plan" value={hero.subscription.plan} />
          <Field label="Renewal" value={formatDateTime(hero.subscription.renewal_at)} />
          <Field
            label="Last Payment"
            value={
              lastPayment ? (
                <span
                  className={
                    lastPayment.status === "failed" ? "text-critical-text" : "text-recovery-text"
                  }
                >
                  {lastPayment.status}
                  {lastPayment.failure_code ? (
                    <span className="mono text-text-faint"> · {lastPayment.failure_code}</span>
                  ) : null}
                </span>
              ) : (
                "—"
              )
            }
          />
        </dl>
      </header>

      {/* ── Pipeline ─────────────────────────────────────────────────────── */}
      <div className="grid flex-1 grid-cols-1 divide-y divide-border lg:grid-cols-2 lg:divide-x lg:divide-y-0">
        <div className="p-5">
          <DiagnosisPanel
            risk={hero.risk}
            diagnosis={hero.diagnosis}
            actionRankings={hero.action_rankings}
          />
        </div>

        <div className="flex flex-col gap-5 p-5">
          <PolicyGuardViz decision={hero.policy_decision} />

          {/* ── Outcome ──────────────────────────────────────────────────── */}
          <div className="mt-auto border-t border-border-subtle pt-4">
            <Eyebrow>Outcome</Eyebrow>
            <div className="mt-3 flex items-baseline justify-between gap-3">
              <span className="text-[13px] text-text-secondary">
                {formatAction(hero.execution.action_type)}
              </span>
              <span
                className={`mono text-[11px] font-semibold uppercase tracking-eyebrow ${execTone}`}
              >
                {hero.execution.status}
              </span>
            </div>
            <p className="mono mt-2 truncate text-[10px] text-text-faint">
              {hero.execution.idempotency_key}
            </p>

            <Link
              href="/dashboard/time-machine"
              className="mono mt-4 inline-block rounded border border-ai/40 px-3 py-1.5 text-[10px] uppercase tracking-eyebrow text-ai-text transition-colors duration-base hover:bg-ai/10 hover:text-text-primary"
            >
              Replay in Time Machine →
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
