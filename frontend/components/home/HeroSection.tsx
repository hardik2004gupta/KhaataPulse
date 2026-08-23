import Link from "next/link";
import { HeroVisualization } from "./HeroVisualization";

export function HeroSection() {
  return (
    <section className="relative mx-auto flex min-h-[calc(100vh-4rem)] max-w-shell flex-col justify-center px-5 py-20 sm:px-8 lg:py-24">
      {/* The pipeline diagram is 680 units wide - it only sits beside the
          headline once the column can render its labels legibly (xl+). */}
      <div className="grid items-center gap-14 xl:grid-cols-12 xl:gap-12">
        {/* ── Statement ──────────────────────────────────────────────────── */}
        <div className="xl:col-span-6">
          <p className="mono text-[10px] uppercase tracking-eyebrow text-text-muted">
            KhaataPulse · Revenue Intelligence Engine
          </p>

          <h1 className="mt-6 text-[2.5rem] font-bold leading-[1.05] tracking-tightest text-text-primary sm:text-[3.25rem] lg:text-[3.75rem]">
            Recover revenue
            <br />
            before it becomes
            <br />
            <span className="text-recovery-text">lost.</span>
          </h1>

          <p className="mt-7 max-w-prose text-[15px] leading-relaxed text-text-secondary">
            KhaataPulse detects payment friction before failure, diagnoses the root cause,
            determines the economically optimal intervention, enforces deterministic policy
            controls, and measures recovery performance - end to end.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-3">
            <Link
              href="/dashboard"
              className="rounded border border-ai/50 bg-ai/10 px-5 py-2.5 text-sm font-medium text-text-primary transition-colors duration-base hover:border-ai hover:bg-ai/20"
            >
              Enter Command Center →
            </Link>
            <Link
              href="/evaluation"
              className="rounded border border-border px-5 py-2.5 text-sm font-medium text-text-secondary transition-colors duration-base hover:border-text-muted hover:text-text-primary"
            >
              Explore Evaluation
            </Link>
          </div>

          <p className="mono mt-10 text-[10px] uppercase tracking-eyebrow text-text-faint">
            Detect · Diagnose · Optimize · Guard · Act · Measure · Audit
          </p>
        </div>

        {/* ── Live pipeline ──────────────────────────────────────────────── */}
        {/* min-w-0 lets the diagram's scroll container clip instead of
            widening the grid track. */}
        <div className="min-w-0 xl:col-span-6">
          <div className="min-w-0 rounded-panel border border-border-subtle bg-surface/40 p-5 backdrop-blur-sm sm:p-6">
            <div className="mb-6 flex items-center justify-between">
              <span className="mono text-[10px] uppercase tracking-eyebrow text-text-muted">
                Pipeline
              </span>
              <span className="mono flex items-center gap-2 text-[10px] uppercase tracking-eyebrow text-text-faint">
                <span
                  aria-hidden="true"
                  className="h-1.5 w-1.5 rounded-full bg-recovery animate-pulse-glow"
                />
                Illustrative
              </span>
            </div>

            <HeroVisualization />
          </div>
        </div>
      </div>
    </section>
  );
}
