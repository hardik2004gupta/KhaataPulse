"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { EvaluationRunResult } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatINR, formatPct } from "@/lib/utils/format";

interface RevenueExposureProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

interface Segment {
  key: string;
  label: string;
  amount: number;
  pct: number;
  bar: string;
  text: string;
  note: string;
  onClick?: () => void;
}

/**
 * Proportional decomposition of the at-risk revenue pool for this run:
 *   baseline recovered · incremental delta · still exposed
 * Widths are computed from the evaluation figures — nothing is authored.
 */
export function RevenueExposure({ result, loading }: RevenueExposureProps) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const id = window.setTimeout(() => setMounted(true), 60);
    return () => window.clearTimeout(id);
  }, []);

  if (loading) {
    return (
      <div className="rounded-panel border border-border bg-surface p-6">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="mt-5 h-8 w-full" />
        <Skeleton className="mt-5 h-3 w-48" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="rounded-panel border border-border bg-surface p-6">
        <Eyebrow>Revenue Exposure</Eyebrow>
        <p className="mt-3 text-xs text-text-muted">Awaiting evaluation run.</p>
      </div>
    );
  }

  const kp = result.khaatapulse;
  const sr = result.smart_retry;

  const atRisk = parseFloat(kp.total_at_risk_amount);
  const kpRecovered = parseFloat(kp.recovered_amount);
  const srRecovered = parseFloat(sr.recovered_amount);

  const baseline = Math.min(kpRecovered, srRecovered);
  const delta = kpRecovered - srRecovered;
  const exposed = Math.max(atRisk - Math.max(kpRecovered, srRecovered), 0);

  const pct = (v: number) => (atRisk > 0 ? (v / atRisk) * 100 : 0);

  const deltaPositive = delta >= 0;

  const segments: Segment[] = [
    {
      key: "baseline",
      label: "Baseline Recovered",
      amount: baseline,
      pct: pct(baseline),
      bar: "bg-recovery/45",
      text: "text-recovery-text",
      note: "Smart Retry floor",
    },
    {
      key: "delta",
      label: deltaPositive ? "Incremental Gain" : "Incremental Loss",
      amount: Math.abs(delta),
      pct: pct(Math.abs(delta)),
      bar: deltaPositive ? "bg-recovery" : "bg-critical",
      text: deltaPositive ? "text-recovery-text" : "text-critical-text",
      note: "KhaataPulse delta",
    },
    {
      key: "exposed",
      label: "Still Exposed",
      amount: exposed,
      pct: pct(exposed),
      bar: "bg-warning/70",
      text: "text-warning-text",
      note: "Open risk → Risk Queue",
      onClick: () => router.push("/cases"),
    },
  ];

  return (
    <div className="flex h-full flex-col rounded-panel border border-border bg-surface p-6">
      <div className="flex items-baseline justify-between gap-4">
        <Eyebrow>Exposure Decomposition</Eyebrow>
        <span className="tabular text-sm font-semibold text-text-primary">
          {formatINR(kp.total_at_risk_amount)}
        </span>
      </div>

      <p className="mono mt-1.5 text-[10px] uppercase tracking-eyebrow text-text-faint">
        At-risk pool · {kp.cases_evaluated.toLocaleString("en-IN")} cases
      </p>

      {/* ── Proportional bar ─────────────────────────────────────────────── */}
      <div className="mt-6 flex h-9 w-full overflow-hidden rounded border border-border-subtle bg-bg-primary">
        {segments.map((s) => (
          <div
            key={s.key}
            role={s.onClick ? "button" : undefined}
            tabIndex={s.onClick ? 0 : undefined}
            onClick={s.onClick}
            onKeyDown={
              s.onClick
                ? (e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      s.onClick?.();
                    }
                  }
                : undefined
            }
            title={`${s.label} — ${formatINR(s.amount)}`}
            className={`${s.bar} h-full transition-[width] duration-slow ease-out ${
              s.onClick ? "cursor-pointer hover:brightness-125" : ""
            }`}
            style={{ width: mounted ? `${s.pct}%` : "0%" }}
          />
        ))}
      </div>

      {/* ── Legend ───────────────────────────────────────────────────────── */}
      <dl className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {segments.map((s) => (
          <div key={s.key} className="border-l-2 border-border-subtle pl-3">
            <dt className="flex items-center gap-1.5">
              <span className={`inline-block h-2 w-2 rounded-sm ${s.bar}`} />
              <span className="mono text-[10px] uppercase tracking-eyebrow text-text-muted">
                {s.label}
              </span>
            </dt>
            <dd className={`tabular mt-1 text-base font-semibold ${s.text}`}>
              {formatINR(s.amount)}
            </dd>
            <dd className="mono mt-0.5 text-[10px] text-text-faint">
              {formatPct(s.pct / 100)} · {s.note}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
