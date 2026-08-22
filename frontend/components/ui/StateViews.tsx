"use client";

import React from "react";

/**
 * Product-specific system states. Language is operational, never generic
 * ("Loading…"), so the surface always reads as instrumentation.
 */

export function LoadingPanel({
  title,
  detail,
  className = "",
}: {
  title: string;
  detail?: string;
  className?: string;
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 rounded-panel border border-border bg-surface px-6 py-14 text-center ${className}`}
    >
      <div className="flex items-center gap-2">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-ai animate-pulse-glow" />
        <span
          className="inline-block h-1.5 w-1.5 rounded-full bg-ai animate-pulse-glow"
          style={{ animationDelay: "0.3s" }}
        />
        <span
          className="inline-block h-1.5 w-1.5 rounded-full bg-ai animate-pulse-glow"
          style={{ animationDelay: "0.6s" }}
        />
      </div>
      <p className="mono text-[10px] uppercase tracking-eyebrow text-text-secondary">{title}</p>
      {detail && <p className="max-w-prose text-xs text-text-muted">{detail}</p>}
    </div>
  );
}

export function ErrorPanel({
  title = "Command Center Unavailable",
  detail = "The evaluation service could not be reached.",
  onRetry,
  className = "",
}: {
  title?: string;
  detail?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 rounded-panel border border-critical/25 bg-critical-dim/15 px-6 py-14 text-center ${className}`}
    >
      <span className="mono text-[10px] uppercase tracking-eyebrow text-critical-text">
        ✕ {title}
      </span>
      <p className="max-w-prose text-xs text-text-muted">{detail}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mono mt-1 rounded border border-critical/40 px-3.5 py-1.5 text-[10px] uppercase tracking-eyebrow text-critical-text transition-colors duration-base hover:bg-critical/10 hover:text-text-primary"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function NoRunPanel({
  onRun,
  className = "",
}: {
  onRun?: () => void;
  className?: string;
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 rounded-panel border border-border bg-surface px-6 py-14 text-center ${className}`}
    >
      <span className="mono text-[10px] uppercase tracking-eyebrow text-text-secondary">
        No Evaluation Run
      </span>
      <p className="max-w-prose text-xs text-text-muted">
        Run an evaluation to populate the Command Center.
      </p>
      {onRun && (
        <button
          type="button"
          onClick={onRun}
          className="mono mt-1 rounded border border-ai/40 px-3.5 py-1.5 text-[10px] uppercase tracking-eyebrow text-ai-text transition-colors duration-base hover:bg-ai/10 hover:text-text-primary"
        >
          Run Evaluation
        </button>
      )}
    </div>
  );
}

/** Small uppercase section label used across every operational panel. */
export function Eyebrow({
  children,
  tone = "muted",
}: {
  children: React.ReactNode;
  tone?: "muted" | "recovery" | "warning" | "ai" | "critical";
}) {
  const toneMap = {
    muted: "text-text-muted",
    recovery: "text-recovery-text",
    warning: "text-warning-text",
    ai: "text-ai-text",
    critical: "text-critical-text",
  } as const;
  return (
    <p className={`mono text-[10px] uppercase tracking-eyebrow ${toneMap[tone]}`}>{children}</p>
  );
}
