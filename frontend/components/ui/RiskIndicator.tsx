"use client";

import { riskBarClass, riskTextClass } from "@/lib/utils/format";

type Level = "LOW" | "MEDIUM" | "HIGH";

const LEVEL_LABEL: Record<Level, string> = {
  LOW: "LOW",
  MEDIUM: "MED",
  HIGH: "HIGH",
};

interface RiskIndicatorProps {
  score: number; // 0.0–1.0
  level: Level;
  compact?: boolean;
}

/**
 * Colour is driven by the score itself (riskTone thresholds), not the label,
 * so the same number always reads the same way. The level is always spelled
 * out in text as well — colour never carries meaning on its own.
 */
export function RiskIndicator({ score, level, compact = false }: RiskIndicatorProps) {
  const bar = riskBarClass(score);
  const text = riskTextClass(score);
  const label = LEVEL_LABEL[level] ?? level;
  const pct = Math.round(score * 100);

  if (compact) {
    return (
      <span className={`tabular inline-flex items-center gap-1.5 text-sm font-semibold ${text}`}>
        <span aria-hidden="true" className={`inline-block h-2 w-2 rounded-full ${bar}`} />
        {pct}%
        <span className="mono text-[10px] uppercase tracking-eyebrow">{label}</span>
      </span>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-elevated">
        <div
          className={`h-full rounded-full ${bar} transition-[width] duration-slow ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`mono tabular w-8 text-right text-xs font-semibold ${text}`}>{pct}%</span>
      <span className={`mono w-10 text-xs font-bold uppercase tracking-eyebrow ${text}`}>
        {label}
      </span>
    </div>
  );
}
