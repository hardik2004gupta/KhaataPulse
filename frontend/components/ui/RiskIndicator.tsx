"use client";

type Level = "LOW" | "MEDIUM" | "HIGH";

const levelStyles: Record<Level, { bar: string; text: string; label: string }> = {
  LOW:    { bar: "bg-recovery",  text: "text-recovery-text", label: "LOW" },
  MEDIUM: { bar: "bg-warning",   text: "text-warning-text",  label: "MED" },
  HIGH:   { bar: "bg-critical",  text: "text-critical-text", label: "HIGH" },
};

interface RiskIndicatorProps {
  score: number;      // 0.0–1.0
  level: Level;
  compact?: boolean;
}

export function RiskIndicator({ score, level, compact = false }: RiskIndicatorProps) {
  const styles = levelStyles[level] ?? levelStyles.MEDIUM;
  const pct = Math.round(score * 100);

  if (compact) {
    return (
      <span className={`inline-flex items-center gap-1.5 font-semibold tabular text-sm ${styles.text}`}>
        <span className={`inline-block w-2 h-2 rounded-full ${styles.bar}`} />
        {pct}%
      </span>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-surface-elevated rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${styles.bar} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`mono text-xs font-semibold tabular w-8 text-right ${styles.text}`}>
        {pct}%
      </span>
      <span className={`mono text-xs font-bold ${styles.text} w-10`}>
        {styles.label}
      </span>
    </div>
  );
}
