"use client";

interface StatusBadgeProps {
  status: string;
  variant?: "default" | "outline";
}

function resolveStyle(status: string): string {
  const s = status.toLowerCase();
  if (["approved", "executed", "recovered", "completed"].includes(s))
    return "bg-recovery-dim text-recovery-text border-recovery/30";
  if (["blocked", "failed", "critical"].includes(s))
    return "bg-critical-dim text-critical-text border-critical/30";
  if (["escalated", "open", "running", "warning"].includes(s))
    return "bg-warning-dim text-warning-text border-warning/30";
  if (["running", "queued"].includes(s))
    return "bg-ai-dim text-ai-text border-ai/30";
  return "bg-surface-elevated text-text-secondary border-border";
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={`mono inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-eyebrow ${resolveStyle(status)}`}
    >
      {status}
    </span>
  );
}
