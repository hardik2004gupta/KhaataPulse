interface PipelineStage {
  n: string;
  name: string;
  description: string;
  /** The deterministic authority boundary gets distinct treatment. */
  guard?: boolean;
}

const STAGES: readonly PipelineStage[] = [
  {
    n: "01",
    name: "DETECT",
    description: "Observable customer signals routed through the risk model",
  },
  {
    n: "02",
    name: "DIAGNOSE",
    description: "LangGraph AI reasons over payment context to identify root cause",
  },
  {
    n: "03",
    name: "OPTIMIZE",
    description: "Expected Net Revenue ranks eligible actions by economic value",
  },
  {
    n: "04",
    name: "GUARD",
    description: "Deterministic Policy Guard authorizes or blocks every action",
    guard: true,
  },
  {
    n: "05",
    name: "ACT",
    description: "Typed, idempotent gateway action executed with full audit record",
  },
  {
    n: "06",
    name: "MEASURE",
    description: "Outcome tracked against same-cohort policy baseline",
  },
  {
    n: "07",
    name: "AUDIT",
    description: "Immutable event trail from signal to recovery",
  },
];

export function PipelineSection() {
  return (
    <section className="relative mx-auto max-w-shell px-5 py-section-sm sm:px-8 lg:py-section">
      <header className="max-w-prose">
        <h2 className="text-[1.75rem] font-bold tracking-tightest text-text-primary sm:text-[2rem]">
          The Intelligence Pipeline
        </h2>
        <p className="mt-3 text-[15px] leading-relaxed text-text-secondary">
          Seven deterministic stages. Every recovery decision visible and traceable.
        </p>
      </header>

      <ol className="mt-12 grid gap-x-4 gap-y-8 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
        {STAGES.map((stage, i) => {
          const last = i === STAGES.length - 1;
          return (
            <li key={stage.n} className="group relative">
              {/* ── Rail ──────────────────────────────────────────────── */}
              <div className="mb-5 flex items-center" aria-hidden="true">
                <span
                  className={`h-2 w-2 shrink-0 rotate-45 border transition-colors duration-base ${
                    stage.guard
                      ? "border-warning bg-warning/30"
                      : "border-border bg-surface group-hover:border-ai"
                  }`}
                />
                {!last && (
                  <span
                    className={`ml-2 h-px flex-1 transition-colors duration-base ${
                      stage.guard
                        ? "bg-warning/30 group-hover:bg-warning/60"
                        : "bg-border group-hover:bg-ai/50"
                    }`}
                  />
                )}
                {last && <span className="ml-2 h-px flex-1 bg-transparent" />}
              </div>

              {/* ── Body ──────────────────────────────────────────────── */}
              <div
                className={`rounded-panel border p-4 transition-colors duration-base ${
                  stage.guard
                    ? "border-warning/40 bg-warning/[0.04] hover:border-warning/70"
                    : "border-border-subtle bg-surface/30 hover:border-border"
                }`}
              >
                <p
                  className={`mono text-[10px] tracking-eyebrow ${
                    stage.guard ? "text-warning-text" : "text-text-faint"
                  }`}
                >
                  {stage.n}
                </p>

                <h3
                  className={`mono mt-2 text-[13px] uppercase tracking-eyebrow ${
                    stage.guard ? "text-warning-text" : "text-text-primary"
                  }`}
                >
                  {stage.name}
                </h3>

                <p className="mt-3 text-[13px] leading-relaxed text-text-muted transition-colors duration-base group-hover:text-text-secondary">
                  {stage.description}
                </p>

                {stage.guard && (
                  <p className="mono mt-4 inline-block border border-warning/40 px-1.5 py-0.5 text-[9px] uppercase tracking-eyebrow text-warning-text">
                    Deterministic
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
