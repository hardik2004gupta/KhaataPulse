"use client";
import React from "react";

interface MetricCardProps {
  label: string;
  value: React.ReactNode;
  subValue?: React.ReactNode;
  accent?: "recovery" | "warning" | "critical" | "ai" | "neutral";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  className?: string;
}

const accentMap = {
  recovery: { text: "text-recovery-text", glow: "glow-recovery", border: "border-recovery/20" },
  warning:  { text: "text-warning-text",  glow: "glow-warning",  border: "border-warning/20"  },
  critical: { text: "text-critical-text", glow: "glow-critical", border: "border-critical/20" },
  ai:       { text: "text-ai-text",       glow: "glow-ai",       border: "border-ai/20"       },
  neutral:  { text: "text-text-primary",  glow: "",              border: "border-border"      },
};

/* Value type scales down on narrow viewports so a long ₹ figure never
   overflows a two-up grid at 390px. */
const sizeMap = {
  sm: { value: "text-xl sm:text-2xl", label: "text-[10px]" },
  md: { value: "text-2xl sm:text-3xl", label: "text-[10px]" },
  lg: { value: "text-4xl sm:text-5xl", label: "text-[11px]" },
};

export function MetricCard({
  label,
  value,
  subValue,
  accent = "neutral",
  size = "md",
  loading = false,
  className = "",
}: MetricCardProps) {
  const ac = accentMap[accent];
  const sz = sizeMap[size];

  return (
    <div
      className={`relative rounded-panel border bg-surface p-5 ${ac.border} ${ac.glow} transition-colors duration-base ${className}`}
    >
      <p
        className={`mono ${sz.label} mb-2 uppercase tracking-eyebrow text-text-muted`}
      >
        {label}
      </p>
      {loading ? (
        <div className="h-10 w-3/4 animate-pulse rounded bg-surface-elevated" />
      ) : (
        // `animate-fade-in` carries `animation-fill-mode: both`, so the value
        // is never painted at its pre-animation opacity on first frame.
        <p className={`tabular animate-fade-in ${sz.value} font-bold leading-none ${ac.text}`}>
          {value}
        </p>
      )}
      {subValue && !loading && (
        <p className="tabular mt-2 text-xs text-text-muted">{subValue}</p>
      )}
    </div>
  );
}
