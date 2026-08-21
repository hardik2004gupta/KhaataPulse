"use client";
import type { AuditEvent } from "@/lib/types";
import { formatDateTime } from "@/lib/utils/format";
import { useState } from "react";

const EVENT_STYLES: Record<string, { dot: string; label: string }> = {
  risk_detected:        { dot: "bg-warning",   label: "text-warning-text"  },
  diagnosis_generated:  { dot: "bg-ai",        label: "text-ai-text"       },
  action_proposed:      { dot: "bg-ai",        label: "text-ai-text"       },
  policy_check:         { dot: "bg-text-muted", label: "text-text-secondary" },
  action_executed:      { dot: "bg-recovery",  label: "text-recovery-text" },
  payment_received:     { dot: "bg-recovery",  label: "text-recovery-text" },
  case_closed:          { dot: "bg-text-muted", label: "text-text-muted"   },
  llm_fallback:         { dot: "bg-critical",  label: "text-critical-text" },
};

function AuditEventRow({ event }: { event: AuditEvent }) {
  const [open, setOpen] = useState(false);
  const style = EVENT_STYLES[event.event_type] ?? { dot: "bg-text-muted", label: "text-text-secondary" };

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className={`w-2 h-2 rounded-full shrink-0 mt-1.5 ${style.dot}`} />
        <div className="w-px flex-1 bg-border mt-1" />
      </div>
      <div className="flex-1 pb-4">
        <div className="flex items-baseline justify-between gap-2">
          <span className={`mono text-xs font-semibold ${style.label}`}>{event.event_type}</span>
          <span className="mono text-xs text-text-faint shrink-0">{formatDateTime(event.timestamp)}</span>
        </div>
        <p className="text-xs text-text-muted mt-0.5">{event.actor}</p>
        {event.idempotency_key && (
          <p className="mono text-xs text-text-faint mt-0.5">{event.idempotency_key}</p>
        )}
        <button
          onClick={() => setOpen(!open)}
          className="mt-1 text-xs text-text-faint hover:text-text-muted transition-colors mono"
        >
          {open ? "▾ hide payload" : "▸ show payload"}
        </button>
        {open && (
          <pre className="mt-2 text-xs mono text-text-secondary bg-bg-secondary border border-border rounded p-3 overflow-x-auto max-h-48">
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

interface AuditTimelineProps {
  events: AuditEvent[];
}

export function AuditTimeline({ events }: AuditTimelineProps) {
  if (events.length === 0) {
    return <p className="text-xs text-text-muted text-center py-6">No audit events recorded.</p>;
  }
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-4">
        Audit Trail — {events.length} events
      </p>
      <div className="space-y-0">
        {events.map((ev) => (
          <AuditEventRow key={ev.id} event={ev} />
        ))}
      </div>
    </div>
  );
}
