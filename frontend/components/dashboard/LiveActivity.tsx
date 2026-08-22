"use client";

import type { AuditEvent } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatTime } from "@/lib/utils/format";

interface LiveActivityProps {
  events: AuditEvent[];
  loading: boolean;
}

const EVENT_TONE: Record<string, { dot: string; text: string }> = {
  risk_detected: { dot: "bg-warning", text: "text-warning-text" },
  diagnosis_generated: { dot: "bg-ai", text: "text-ai-text" },
  action_proposed: { dot: "bg-ai", text: "text-ai-text" },
  policy_check: { dot: "bg-text-muted", text: "text-text-secondary" },
  action_executed: { dot: "bg-recovery", text: "text-recovery-text" },
  payment_received: { dot: "bg-recovery", text: "text-recovery-text" },
  case_closed: { dot: "bg-text-muted", text: "text-text-muted" },
  llm_fallback: { dot: "bg-critical", text: "text-critical-text" },
};

const FALLBACK_TONE = { dot: "bg-text-muted", text: "text-text-secondary" };

export function LiveActivity({ events, loading }: LiveActivityProps) {
  return (
    <section className="flex h-full flex-col rounded-panel border border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <Eyebrow>System Activity</Eyebrow>
        <span className="mono flex items-center gap-1.5 text-[10px] uppercase tracking-eyebrow text-text-faint">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-recovery animate-pulse-glow" />
          Streaming
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-3" style={{ maxHeight: "22rem" }}>
        {loading ? (
          <div className="space-y-3 py-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : events.length === 0 ? (
          <p className="py-8 text-center text-xs text-text-muted">
            No audit events on the current case.
          </p>
        ) : (
          <ul className="divide-y divide-border-subtle">
            {events.map((ev, i) => {
              const tone = EVENT_TONE[ev.event_type] ?? FALLBACK_TONE;
              return (
                <li
                  key={ev.id ?? `${ev.event_type}-${i}`}
                  className="flex items-center gap-3 py-2.5"
                >
                  <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${tone.dot}`} />
                  <span className="mono tabular shrink-0 text-[10px] text-text-faint">
                    {formatTime(ev.timestamp)}
                  </span>
                  <span className={`mono min-w-0 flex-1 truncate text-[11px] ${tone.text}`}>
                    {ev.event_type}
                  </span>
                  <span className="mono shrink-0 text-[10px] text-text-muted">{ev.actor}</span>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
