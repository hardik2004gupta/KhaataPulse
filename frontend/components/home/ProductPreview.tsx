import type { ReactNode } from "react";

/* ── Card shell ───────────────────────────────────────────────────────────── */

function PreviewCard({
  label,
  title,
  children,
}: {
  label: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <article className="flex flex-col rounded-panel border border-border-subtle bg-surface/50 p-5 transition-colors duration-base hover:border-border">
      <header className="mb-5 flex items-start justify-between gap-3">
        <span className="mono text-[9px] uppercase tracking-eyebrow text-text-faint">{label}</span>
        <span className="mono shrink-0 border border-border-subtle px-1.5 py-0.5 text-[8px] uppercase tracking-eyebrow text-text-faint">
          Example
        </span>
      </header>

      <h3 className="text-[15px] font-semibold tracking-tight text-text-primary">{title}</h3>

      <div className="mt-5 flex-1">{children}</div>
    </article>
  );
}

/* ── Shared primitives ────────────────────────────────────────────────────── */

function Bar({ pct, tone }: { pct: number; tone: "warning" | "ai" | "recovery" | "neutral" }) {
  const fill = {
    warning: "bg-warning/70",
    ai: "bg-ai/70",
    recovery: "bg-recovery/70",
    neutral: "bg-text-faint",
  }[tone];

  return (
    <div className="h-1 w-full overflow-hidden rounded-sm bg-border-subtle">
      <div className={`h-full ${fill}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

/* ── 1 · Risk Sieve ───────────────────────────────────────────────────────── */

const SIGNALS = [
  { feature: "payment_success_rate", impact: 82 },
  { feature: "previous_failures", impact: 61 },
  { feature: "checkout_reopens", impact: 44 },
];

function RiskPreview() {
  return (
    <div>
      <div className="flex items-center justify-between border-b border-border-subtle pb-4">
        <span className="mono text-[10px] uppercase tracking-eyebrow text-text-muted">
          Risk Score
        </span>
        <span className="flex items-center gap-2">
          <span aria-hidden="true" className="mono text-[11px] tracking-[0.2em] text-warning">
            ●●●○○
          </span>
          <span className="mono text-[10px] uppercase tracking-eyebrow text-warning-text">
            High
          </span>
        </span>
      </div>

      <p className="mono mt-4 text-[9px] uppercase tracking-eyebrow text-text-faint">
        Top Signals
      </p>

      <ul className="mt-3 space-y-3">
        {SIGNALS.map((s) => (
          <li key={s.feature}>
            <p className="mono mb-1.5 text-[10px] text-text-secondary">{s.feature}</p>
            <Bar pct={s.impact} tone="warning" />
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ── 2 · AI Reasoner ──────────────────────────────────────────────────────── */

function DiagnosisPreview() {
  return (
    <div className="space-y-5">
      <div>
        <p className="mono text-[9px] uppercase tracking-eyebrow text-text-faint">Cause</p>
        <p className="mt-1.5 text-[13px] text-text-primary">Temporary Cash Flow</p>
      </div>

      <div>
        <div className="mb-2 flex items-baseline justify-between">
          <span className="mono text-[9px] uppercase tracking-eyebrow text-text-faint">
            Confidence
          </span>
          <span className="mono tabular text-[11px] text-ai-text">95%</span>
        </div>
        <Bar pct={95} tone="ai" />
      </div>

      <div>
        <p className="mono text-[9px] uppercase tracking-eyebrow text-text-faint">
          Proposed Action
        </p>
        <p className="mono mt-1.5 inline-block border border-ai/35 px-2 py-0.5 text-[11px] text-ai-text">
          grace_period
        </p>
      </div>
    </div>
  );
}

/* ── 3 · ENR Optimizer ────────────────────────────────────────────────────── */

const RANKINGS = [
  { action: "grace_period", rank: 100, selected: true },
  { action: "smart_link", rank: 72, selected: false },
  { action: "silent_retry", rank: 41, selected: false },
];

function OptimizerPreview() {
  return (
    <div>
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <span className="mono text-[9px] uppercase tracking-eyebrow text-text-faint">Action</span>
        <span className="mono text-[9px] uppercase tracking-eyebrow text-text-faint">
          Relative ENR
        </span>
      </div>

      <ul className="mt-4 space-y-4">
        {RANKINGS.map((r) => (
          <li key={r.action}>
            <div className="mb-1.5 flex items-center justify-between gap-3">
              <span
                className={`mono text-[11px] ${
                  r.selected ? "text-recovery-text" : "text-text-secondary"
                }`}
              >
                {r.selected && (
                  <span aria-hidden="true" className="mr-1">
                    ▲
                  </span>
                )}
                {r.action}
              </span>
              {r.selected && (
                <span className="mono text-[8px] uppercase tracking-eyebrow text-recovery-text">
                  Selected
                </span>
              )}
            </div>
            <Bar pct={r.rank} tone={r.selected ? "recovery" : "neutral"} />
          </li>
        ))}
      </ul>

      <p className="mono mt-5 text-[9px] leading-relaxed text-text-faint">
        ENR = P(payment|action) × amount − P(churn|action) × LTV − cost
      </p>
    </div>
  );
}

/* ── 4 · Policy Guard ─────────────────────────────────────────────────────── */

const CHECKS = [
  "Kill Switch",
  "Dispute Hold",
  "Legal Hold",
  "Contact Limit",
  "Cooldown",
] as const;

function GuardPreview() {
  return (
    <div>
      <ul className="space-y-2.5">
        {CHECKS.map((check) => (
          <li key={check} className="flex items-center gap-3">
            <span aria-hidden="true" className="mono text-[11px] text-recovery">
              ✓
            </span>
            <span className="mono text-[11px] text-text-secondary">{check}</span>
          </li>
        ))}
        <li className="flex items-center gap-3 border-t border-border-subtle pt-3">
          <span aria-hidden="true" className="mono text-[11px] text-recovery">
            →
          </span>
          <span className="mono text-[11px] text-text-secondary">Amount Threshold</span>
        </li>
      </ul>

      <p className="mono mt-5 inline-block border border-recovery/40 bg-recovery/[0.06] px-2 py-1 text-[10px] uppercase tracking-eyebrow text-recovery-text">
        Approved
      </p>
    </div>
  );
}

/* ── Section ──────────────────────────────────────────────────────────────── */

export function ProductPreview() {
  return (
    <section className="relative mx-auto max-w-shell px-5 py-section-sm sm:px-8 lg:py-section">
      <header className="max-w-prose">
        <h2 className="text-[1.75rem] font-bold tracking-tightest text-text-primary sm:text-[2rem]">
          Every layer, visible.
        </h2>
        <p className="mt-3 text-[15px] leading-relaxed text-text-secondary">
          From risk signal to audit trail - the full pipeline in view.
        </p>
      </header>

      <div className="mt-12 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <PreviewCard label="Risk Sieve" title="Risk Intelligence">
          <RiskPreview />
        </PreviewCard>

        <PreviewCard label="AI Reasoner" title="AI Diagnosis">
          <DiagnosisPreview />
        </PreviewCard>

        <PreviewCard label="ENR Optimizer" title="Economic Optimizer">
          <OptimizerPreview />
        </PreviewCard>

        <PreviewCard label="Policy Guard · Deterministic" title="Policy Guard">
          <GuardPreview />
        </PreviewCard>
      </div>

      <p className="mono mt-8 text-[9px] uppercase tracking-eyebrow text-text-faint">
        Structural previews · illustrative values · not live data
      </p>
    </section>
  );
}
