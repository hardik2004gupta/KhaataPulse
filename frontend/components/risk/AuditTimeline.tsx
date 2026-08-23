"use client";

import type { AuditEvent } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import { formatDateTime } from "@/lib/utils/format";
import { PayloadViewer } from "./PayloadViewer";

const EVENT_STYLES: Record<string, { dot: string; label: string; ring: string }> = {
  risk_detected: { dot: "bg-warning", label: "text-warning-text", ring: "ring-warning/25" },
  diagnosis_generated: { dot: "bg-ai", label: "text-ai-text", ring: "ring-ai/25" },
  action_proposed: { dot: "bg-ai", label: "text-ai-text", ring: "ring-ai/25" },
  policy_check: { dot: "bg-text-muted", label: "text-text-secondary", ring: "ring-border" },
  action_executed: { dot: "bg-recovery", label: "text-recovery-text", ring: "ring-recovery/25" },
  payment_received: { dot: "bg-recovery", label: "text-recovery-text", ring: "ring-recovery/25" },
  case_closed: { dot: "bg-text-muted", label: "text-text-muted", ring: "ring-border" },
  llm_fallback: { dot: "bg-critical", label: "text-critical-text", ring: "ring-critical/25" },
};

const FALLBACK = { dot: "bg-text-muted", label: "text-text-secondary", ring: "ring-border" };

function AuditEventRow({ event, last }: { event: AuditEvent; last: boolean }) {
  const style = EVENT_STYLES[event.event_type] ?? FALLBACK;

  return (
    <li className="flex gap-3">
      {/* Rail */}
      <div className="flex flex-col items-center">
        <span
          className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ring-4 ${style.dot} ${style.ring}`}
        />
        {!last && <span className="mt-1 w-px flex-1 bg-border-subtle" />}
      </div>

      {/* Body */}
      <div className={`min-w-0 flex-1 ${last ? "pb-1" : "pb-5"}`}>
        <div className="flex items-baseline justify-between gap-3">
          <span className={`mono truncate text-[11px] font-semibold ${style.label}`}>
            {event.event_type}
          </span>
          <span className="mono tabular shrink-0 text-[10px] text-text-faint">
            {formatDateTime(event.timestamp)}
          </span>
        </div>

        <p className="mono mt-0.5 text-[10px] uppercase tracking-eyebrow text-text-muted">
          {event.actor}
          {event.idempotency_key ? (
            <span className="text-text-faint"> · {event.idempotency_key}</span>
          ) : null}
        </p>

        <PayloadViewer payload={event.payload} />
      </div>
    </li>
  );
}

interface AuditTimelineProps {
  events: AuditEvent[];
}

export function AuditTimeline({ events }: AuditTimelineProps) {
  if (events.length === 0) {
    return (
      <div>
        <Eyebrow>Audit Trail</Eyebrow>
        <p className="py-6 text-center text-xs text-text-muted">No audit events recorded.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <Eyebrow>Audit Trail</Eyebrow>
        <span className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
          {events.length} events · immutable
        </span>
      </div>

      <ol className="mt-4">
        {events.map((ev, i) => (
          <AuditEventRow
            key={ev.id ?? `${ev.event_type}-${i}`}
            event={ev}
            last={i === events.length - 1}
          />
        ))}
      </ol>
    </div>
  );
}
