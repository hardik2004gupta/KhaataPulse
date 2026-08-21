"use client";

type PolicyStatus = "APPROVED" | "BLOCKED" | "ESCALATED";

const statusStyles: Record<PolicyStatus, string> = {
  APPROVED:  "bg-recovery-dim text-recovery-text border-recovery/30",
  BLOCKED:   "bg-critical-dim text-critical-text border-critical/30",
  ESCALATED: "bg-warning-dim  text-warning-text  border-warning/30",
};

const statusIcons: Record<PolicyStatus, string> = {
  APPROVED:  "✓",
  BLOCKED:   "✕",
  ESCALATED: "⚠",
};

export function PolicyBadge({ status }: { status: PolicyStatus }) {
  const styles = statusStyles[status] ?? "bg-surface text-text-secondary border-border";
  const icon   = statusIcons[status] ?? "?";
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold border rounded-full mono ${styles}`}>
      <span>{icon}</span>
      {status}
    </span>
  );
}
