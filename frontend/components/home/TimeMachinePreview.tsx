interface TimelineEvent {
  time: string;
  event: string;
  detail: string;
  /** The moment the pipeline takes over. */
  risk?: boolean;
}

const TIMELINE: readonly TimelineEvent[] = [
  { time: "09:12", event: "Invoice Viewed", detail: "Renewal invoice opened" },
  { time: "10:04", event: "Checkout Reopened", detail: "Second attempt at payment" },
  { time: "10:16", event: "Payment Method Changed", detail: "New card added to account" },
  { time: "10:40", event: "Support Message", detail: "“Having trouble with payment”" },
  { time: "11:00", event: "Payment Failed", detail: "bank_declined" },
  {
    time: "11:01",
    event: "Risk Detected",
    detail: "Risk score: HIGH - routed to KhaataPulse",
    risk: true,
  },
];

export function TimeMachinePreview() {
  return (
    <section className="relative mx-auto max-w-shell px-5 py-section-sm sm:px-8 lg:py-section">
      <div className="grid gap-12 lg:grid-cols-12 lg:gap-16">
        {/* ── Statement ──────────────────────────────────────────────────── */}
        <header className="lg:col-span-5">
          <p className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">Preview</p>
          <h2 className="mt-4 text-[1.75rem] font-bold tracking-tightest text-text-primary sm:text-[2rem]">
            Revenue Time Machine
          </h2>
          <p className="mt-3 max-w-prose text-[15px] leading-relaxed text-text-secondary">
            Every observable customer signal, in context. The agent sees only what the customer
            world emits - never hidden state, never counterfactual outcomes.
          </p>
        </header>

        {/* ── Timeline ───────────────────────────────────────────────────── */}
        <div className="lg:col-span-7">
          <div className="rounded-panel border border-border-subtle bg-surface/50">
            <div className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
              <span className="mono text-[9px] uppercase tracking-eyebrow text-text-muted">
                Example Customer Journey
              </span>
              <span className="mono border border-border-subtle px-1.5 py-0.5 text-[8px] uppercase tracking-eyebrow text-text-faint">
                Example · Not Live Data
              </span>
            </div>

            <ol className="px-5 py-2">
              {TIMELINE.map((e, i) => {
                const last = i === TIMELINE.length - 1;
                return (
                  <li key={e.time} className="relative flex gap-4 py-3.5">
                    {/* Rail */}
                    <div className="flex flex-col items-center pt-1" aria-hidden="true">
                      <span
                        className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                          e.risk ? "bg-warning" : "bg-text-faint"
                        }`}
                      />
                      {!last && <span className="mt-1.5 w-px flex-1 bg-border-subtle" />}
                    </div>

                    {/* Content */}
                    <div className="flex flex-1 flex-col gap-1 sm:flex-row sm:items-baseline sm:gap-5">
                      <time className="mono tabular shrink-0 text-[11px] text-text-muted">
                        {e.time}
                      </time>

                      <div className="min-w-0 flex-1">
                        <p
                          className={`text-[13px] font-medium ${
                            e.risk ? "text-warning-text" : "text-text-primary"
                          }`}
                        >
                          {e.risk && (
                            <span aria-hidden="true" className="mr-1.5">
                              ●
                            </span>
                          )}
                          {e.event}
                        </p>
                        <p
                          className={`mono mt-0.5 text-[11px] ${
                            e.risk ? "text-warning-text/70" : "text-text-muted"
                          }`}
                        >
                          {e.detail}
                        </p>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
        </div>
      </div>
    </section>
  );
}
