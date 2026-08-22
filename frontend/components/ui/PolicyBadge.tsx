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
  const icon = statusIcons[status] ?? "?";
  return (
    <span
      className={`mono inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-eyebrow ${styles}`}
    >
      {/* The glyph reinforces the colour; the status word carries the meaning. */}
      <span aria-hidden="true">{icon}</span>
      {status}
    </span>
  );
}
