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

const sizeMap = {
  sm: { value: "text-2xl", label: "text-xs" },
  md: { value: "text-3xl", label: "text-xs" },
  lg: { value: "text-5xl", label: "text-sm" },
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
      className={`
        relative bg-surface border ${ac.border} rounded-lg p-5
        ${ac.glow} transition-all duration-300
        ${className}
      `}
    >
      <p className={`${sz.label} font-medium tracking-widest uppercase text-text-muted mb-2`}>
        {label}
      </p>
      {loading ? (
        <div className="h-10 w-3/4 bg-surface-elevated rounded animate-pulse" />
      ) : (
        <p className={`${sz.value} font-bold tabular ${ac.text} leading-none`}>
          {value}
        </p>
      )}
      {subValue && !loading && (
        <p className="text-xs text-text-muted mt-2">{subValue}</p>
      )}
    </div>
  );
}
