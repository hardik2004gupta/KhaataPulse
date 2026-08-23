"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { EvaluationRunResult } from "@/lib/types";

interface TopBarProps {
  evalResult?: EvaluationRunResult | null;
  navOpen: boolean;
  onToggleNav: () => void;
}

/** Live UTC-ish clock. Rendered client-only to avoid hydration drift. */
function Clock() {
  const [now, setNow] = useState<string | null>(null);

  useEffect(() => {
    const tick = () =>
      setNow(
        new Date().toLocaleTimeString("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        }),
      );
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <span className="mono tabular text-[10px] text-text-muted" aria-label="Current time">
      {now ?? "--:--:--"}
    </span>
  );
}

function TelemetryChip({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "recovery" | "ai";
}) {
  const dot = tone === "recovery" ? "bg-recovery" : "bg-ai";
  const text = tone === "recovery" ? "text-recovery-text" : "text-ai-text";
  return (
    <span className="mono flex items-center gap-1.5 text-[10px] uppercase tracking-eyebrow text-text-faint">
      {label}
      <span className={`inline-flex items-center gap-1 ${text}`}>
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${dot} animate-pulse-glow`} />
        {value}
      </span>
    </span>
  );
}

export function TopBar({ evalResult = null, navOpen, onToggleNav }: TopBarProps) {
  const runLabel = evalResult
    ? `SEED ${evalResult.seed} · ${evalResult.cohort_size.toLocaleString("en-IN")} ACCOUNTS`
    : "NO EVALUATION";

  return (
    <header className="surface-chrome sticky top-0 z-nav h-12 border-b border-border/60 backdrop-blur-xl">
      <div className="flex h-full items-center gap-4 px-4 sm:px-5">
        {/* ── Nav toggle (tablet + mobile) ──────────────────────────────── */}
        <button
          type="button"
          onClick={onToggleNav}
          aria-expanded={navOpen}
          aria-label={navOpen ? "Close navigation" : "Open navigation"}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded border border-border text-text-secondary transition-colors duration-base hover:border-ai/50 hover:text-text-primary lg:hidden"
        >
          <span className="relative block h-2.5 w-3.5">
            <span
              className={`absolute left-0 block h-px w-3.5 bg-current transition-transform duration-base ${
                navOpen ? "top-1 rotate-45" : "top-0"
              }`}
            />
            <span
              className={`absolute left-0 top-1 block h-px w-3.5 bg-current transition-opacity duration-fast ${
                navOpen ? "opacity-0" : "opacity-100"
              }`}
            />
            <span
              className={`absolute left-0 block h-px w-3.5 bg-current transition-transform duration-base ${
                navOpen ? "top-1 -rotate-45" : "top-2"
              }`}
            />
          </span>
        </button>

        {/* ── Brand ─────────────────────────────────────────────────────── */}
        <Link href="/" className="group flex shrink-0 items-baseline gap-2.5">
          <span className="text-[13px] font-semibold tracking-tightest text-text-primary">
            KhaataPulse
          </span>
          <span className="mono hidden text-[9px] uppercase tracking-eyebrow text-text-faint transition-colors duration-base group-hover:text-text-muted xl:inline">
            Revenue Intelligence Engine
          </span>
        </Link>

        {/* ── Run context (centre) ──────────────────────────────────────── */}
        <div className="mono hidden min-w-0 flex-1 justify-center text-[10px] uppercase tracking-eyebrow md:flex">
          <span
            className={`truncate rounded border px-2.5 py-1 ${
              evalResult
                ? "border-recovery/25 bg-recovery-dim/25 text-recovery-text"
                : "border-border text-text-faint"
            }`}
          >
            {runLabel}
          </span>
        </div>

        {/* ── Telemetry (right) ─────────────────────────────────────────── */}
        <div className="ml-auto flex items-center gap-4">
          <span className="hidden lg:inline">
            <TelemetryChip label="System" value="Healthy" tone="recovery" />
          </span>
          <span className="hidden xl:inline">
            <TelemetryChip label="Automation" value="Active" tone="ai" />
          </span>
          <Clock />
        </div>
      </div>
    </header>
  );
}
