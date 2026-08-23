interface Layer {
  name: string;
  role: string;
  /** The one layer that holds authority. */
  authority?: boolean;
}

const LAYERS: readonly Layer[] = [
  { name: "RISK MODEL", role: "finds risk" },
  { name: "AI REASONER", role: "understands context" },
  { name: "ECONOMIC OPTIMIZER", role: "determines value" },
  { name: "POLICY GUARD", role: "authorizes action", authority: true },
  { name: "AUDIT LOG", role: "records everything" },
];

function Connector() {
  return (
    <div className="flex justify-center py-2" aria-hidden="true">
      <svg width="10" height="18" viewBox="0 0 10 18" className="text-text-faint">
        <line x1="5" y1="0" x2="5" y2="12" stroke="currentColor" strokeWidth="1" />
        <path d="M1.5 11.5 L5 16 L8.5 11.5" fill="none" stroke="currentColor" strokeWidth="1" />
      </svg>
    </div>
  );
}

export function ArchitectureStory() {
  return (
    <section className="relative mx-auto max-w-shell px-5 py-section-sm sm:px-8 lg:py-section">
      <div className="grid gap-14 lg:grid-cols-12 lg:gap-16">
        {/* ── Statement ──────────────────────────────────────────────────── */}
        <header className="lg:col-span-5">
          <h2 className="text-[1.75rem] font-bold tracking-tightest text-text-primary sm:text-[2rem]">
            Intelligence without autonomy.
          </h2>
          <p className="mt-3 max-w-prose text-[15px] leading-relaxed text-text-secondary">
            Five layers. Each with a defined role. None exceeding its authority.
          </p>

          <div className="mt-8 border-l border-warning/40 pl-5">
            <p className="text-[15px] leading-relaxed text-text-secondary">
              The LLM diagnoses. The optimizer ranks. But only the{" "}
              <span className="text-warning-text">Policy Guard</span> approves.
            </p>
          </div>
        </header>

        {/* ── Layer stack ────────────────────────────────────────────────── */}
        <div className="lg:col-span-7">
          <ol>
            {LAYERS.map((layer, i) => (
              <li key={layer.name}>
                <div
                  className={`flex flex-col gap-2 rounded-panel border px-5 py-4 transition-colors duration-base sm:flex-row sm:items-center sm:justify-between sm:gap-6 ${
                    layer.authority
                      ? "border-warning/45 bg-warning/[0.05]"
                      : "border-border-subtle bg-surface/40 hover:border-border"
                  }`}
                >
                  <div className="flex items-baseline gap-3">
                    <span
                      className={`mono text-[12px] uppercase tracking-eyebrow ${
                        layer.authority ? "text-warning-text" : "text-text-primary"
                      }`}
                    >
                      {layer.name}
                    </span>
                    {layer.authority && (
                      <span aria-hidden="true" className="text-warning-text">
                        *
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4">
                    {layer.authority && (
                      <span className="mono hidden border border-warning/40 px-1.5 py-0.5 text-[9px] uppercase tracking-eyebrow text-warning-text sm:inline">
                        Deterministic Boundary
                      </span>
                    )}
                    <span className="text-[13px] text-text-muted">→ {layer.role}</span>
                  </div>
                </div>

                {layer.authority && (
                  <p className="mono mt-2 px-5 text-[9px] uppercase tracking-eyebrow text-warning-text sm:hidden">
                    Deterministic Boundary
                  </p>
                )}

                {i < LAYERS.length - 1 && <Connector />}
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
