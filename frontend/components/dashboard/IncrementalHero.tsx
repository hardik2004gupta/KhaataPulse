"use client";

import type { EvaluationRunResult } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatINR, formatPct, formatPP } from "@/lib/utils/format";

interface IncrementalHeroProps {
  result: EvaluationRunResult | null;
  loading: boolean;
}

/**
 * The primary KPI surface — Incremental Recovery = KhaataPulse − Smart Retry.
 * Every figure is derived from the evaluation run; nothing is authored here.
 */
export function IncrementalHero({ result, loading }: IncrementalHeroProps) {
  if (loading) {
    return (
      <div className="flex h-full flex-col justify-center gap-4 rounded-panel border border-recovery/20 bg-surface p-6">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-14 w-56" />
        <Skeleton className="h-3 w-40" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-panel border border-border bg-surface p-6 text-center">
        <Eyebrow>Incremental Recovery</Eyebrow>
        <p className="mt-3 text-xs text-text-muted">Awaiting evaluation run.</p>
      </div>
    );
  }

  const kp = result.khaatapulse;
  const sr = result.smart_retry;

  const incremental = parseFloat(result.incremental_recovery);
  const positive = incremental >= 0;
  const rateLift = kp.recovery_rate - sr.recovery_rate;
  const contactDelta = sr.contacts_sent - kp.contacts_sent;

  const accentText = positive ? "text-recovery-text" : "text-critical-text";
  const accentBorder = positive ? "border-recovery/25" : "border-critical/25";
  const accentGlow = positive ? "glow-recovery" : "glow-critical";

  return (
    <div
      className={`relative flex h-full flex-col justify-center overflow-hidden rounded-panel border ${accentBorder} bg-surface p-6 ${accentGlow} sm:p-8`}
    >
      {/* Directional wash — reinforces sign without decorating. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background: positive
            ? "radial-gradient(120% 100% at 0% 100%, rgba(16,185,129,0.10) 0%, transparent 60%)"
            : "radial-gradient(120% 100% at 0% 100%, rgba(239,68,68,0.10) 0%, transparent 60%)",
        }}
      />

      <div className="relative">
        <Eyebrow tone={positive ? "recovery" : "critical"}>Incremental Recovery</Eyebrow>

        <p
          className={`tabular mt-4 text-[clamp(2.75rem,7vw,4.25rem)] font-bold leading-[0.95] tracking-tightest ${accentText}`}
        >
          {positive ? "+" : ""}
          {formatINR(result.incremental_recovery)}
        </p>

        <p className="mono mt-3 flex items-center gap-1.5 text-[11px] uppercase tracking-eyebrow text-text-muted">
          <span className={accentText}>{positive ? "↑" : "↓"}</span>
          vs Smart Retry baseline
        </p>

        <dl className="mt-6 grid grid-cols-2 gap-x-5 gap-y-4 border-t border-border-subtle pt-5">
          <div>
            <dt className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
              Recovery Rate Lift
            </dt>
            <dd
              className={`tabular mt-1 text-lg font-semibold ${
                rateLift >= 0 ? "text-recovery-text" : "text-critical-text"
              }`}
            >
              {formatPP(rateLift)}
            </dd>
            <dd className="mono mt-0.5 text-[10px] text-text-faint">
              {formatPct(sr.recovery_rate)} → {formatPct(kp.recovery_rate)}
            </dd>
          </div>

          <div>
            <dt className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
              Contacts Saved
            </dt>
            <dd
              className={`tabular mt-1 text-lg font-semibold ${
                contactDelta >= 0 ? "text-ai-text" : "text-warning-text"
              }`}
            >
              {contactDelta >= 0 ? "−" : "+"}
              {Math.abs(contactDelta).toLocaleString("en-IN")}
            </dd>
            <dd className="mono mt-0.5 text-[10px] text-text-faint">
              {sr.contacts_sent.toLocaleString("en-IN")} →{" "}
              {kp.contacts_sent.toLocaleString("en-IN")} sent
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
