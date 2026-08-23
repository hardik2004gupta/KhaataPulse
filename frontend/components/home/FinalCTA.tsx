import Link from "next/link";

export function FinalCTA() {
  return (
    <section className="relative mx-auto max-w-shell px-5 py-section-sm sm:px-8 lg:py-section">
      <div className="relative overflow-hidden rounded-panel border border-border-subtle bg-surface/40 px-6 py-16 text-center sm:px-10 lg:py-24">
        {/* Single restrained accent — a horizon line, not a gradient wash */}
        <span
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-ai/40 to-transparent"
        />

        <p className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
          Detect · Diagnose · Optimize · Guard · Act · Measure · Audit
        </p>

        <h2 className="mx-auto mt-7 max-w-3xl text-[2rem] font-bold leading-[1.1] tracking-tightest text-text-primary sm:text-[2.75rem]">
          Revenue recovery, under control.
        </h2>

        <p className="mx-auto mt-5 max-w-prose text-[15px] leading-relaxed text-text-secondary">
          KhaataPulse turns payment friction into a policy decision — not a manual process.
        </p>

        <div className="mt-11 flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-5">
          <Link
            href="/dashboard"
            className="rounded border border-ai/50 bg-ai/10 px-6 py-3 text-sm font-medium text-text-primary transition-colors duration-base hover:border-ai hover:bg-ai/20"
          >
            Enter the Command Center →
          </Link>
          <Link
            href="/evaluation"
            className="text-sm text-text-secondary underline-offset-4 transition-colors duration-base hover:text-text-primary hover:underline"
          >
            Read the architecture →
          </Link>
        </div>
      </div>

      <footer className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-border-subtle pt-8 sm:flex-row">
        <p className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
          KhaataPulse · Revenue Intelligence Engine
        </p>
        <p className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
          Controlled recovery-policy evaluation environment
        </p>
      </footer>
    </section>
  );
}
