"use client";

import { useState } from "react";
import type { HeroCase } from "@/lib/types";
import { PayloadViewer } from "@/components/risk/PayloadViewer";
import { PolicyBadge } from "@/components/ui/PolicyBadge";
import {
  formatAction,
  formatCause,
  formatDateTime,
  formatINR,
  formatTime,
} from "@/lib/utils/format";

type Tone = "neutral" | "critical" | "warning" | "ai" | "recovery";

export interface TimelineEntry {
  id: string;
  eventType: string;
  timestamp: string;
  headline: string;
  detail?: string;
  tone: Tone;
  /** Phase separator label - pipeline entries are derived, not observed. */
  stage: "OBSERVED" | "PIPELINE";
  payload: Record<string, unknown>;
  badge?: React.ReactNode;
}

const TONE: Record<Tone, { dot: string; ring: string; text: string; border: string }> = {
  neutral: {
    dot: "bg-text-muted",
    ring: "ring-border",
    text: "text-text-secondary",
    border: "border-border",
  },
  critical: {
    dot: "bg-critical",
    ring: "ring-critical/25",
    text: "text-critical-text",
    border: "border-critical/35",
  },
  warning: {
    dot: "bg-warning",
    ring: "ring-warning/25",
    text: "text-warning-text",
    border: "border-warning/35",
  },
  ai: { dot: "bg-ai", ring: "ring-ai/25", text: "text-ai-text", border: "border-ai/35" },
  recovery: {
    dot: "bg-recovery",
    ring: "ring-recovery/25",
    text: "text-recovery-text",
    border: "border-recovery/35",
  },
};

const OBSERVABLE_LABEL: Record<string, string> = {
  invoice_viewed: "Invoice Viewed",
  checkout_reopened: "Checkout Reopened",
  payment_method_changed: "Payment Method Changed",
  payment_failed: "Payment Failed",
  subscription_changed: "Subscription Changed",
  support_message: "Support Message",
  payment_delayed: "Payment Delayed",
  renewal_approaching: "Renewal Approaching",
};

const OBSERVABLE_TONE: Record<string, Tone> = {
  payment_failed: "critical",
  payment_delayed: "warning",
  support_message: "warning",
  checkout_reopened: "warning",
};

/**
 * Reconstructs one customer's story: the observable event stream the agent was
 * allowed to see, followed by the decisions the pipeline derived from it.
 * Hidden simulator state and ground-truth outcome probabilities never appear -
 * every entry originates from the observable feed or the recorded audit trail.
 */
export function buildTimeline(hero: HeroCase): TimelineEntry[] {
  const observed: TimelineEntry[] = [...hero.observable_events]
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map((ev, i) => ({
      id: `obs-${i}-${ev.event_type}`,
      eventType: ev.event_type,
      timestamp: ev.timestamp,
      headline: OBSERVABLE_LABEL[ev.event_type] ?? ev.event_type.replace(/_/g, " "),
      tone: OBSERVABLE_TONE[ev.event_type] ?? "neutral",
      stage: "OBSERVED",
      payload: ev.payload ?? {},
    }));

  const auditAt = (type: string) =>
    hero.audit_events.find((e) => e.event_type === type)?.timestamp ??
    hero.observable_events[hero.observable_events.length - 1]?.timestamp ??
    new Date().toISOString();

  const best = hero.action_rankings[0];

  const pipeline: TimelineEntry[] = [
    {
      id: "risk_detected",
      eventType: "risk_detected",
      timestamp: auditAt("risk_detected"),
      headline: "Risk Detected",
      detail: `Logistic regression scored ${Math.round(
        hero.risk.risk_score * 100,
      )}% failure probability - routed to the reasoning graph.`,
      tone: "warning",
      stage: "PIPELINE",
      payload: {
        risk_score: hero.risk.risk_score,
        risk_level: hero.risk.risk_level,
        model_version: hero.risk.model_version,
        top_signals: hero.risk.top_signals,
      },
    },
    {
      id: "diagnosis_generated",
      eventType: "diagnosis_generated",
      timestamp: auditAt("diagnosis_generated"),
      headline: `Diagnosis · ${formatCause(hero.diagnosis.cause)}`,
      detail: hero.diagnosis.rationale,
      tone: "ai",
      stage: "PIPELINE",
      payload: {
        cause: hero.diagnosis.cause,
        confidence: hero.diagnosis.confidence,
        proposed_action: hero.diagnosis.proposed_action,
        risk_level: hero.diagnosis.risk_level,
      },
    },
    {
      id: "action_ranked",
      eventType: "action_ranked",
      timestamp: auditAt("action_proposed"),
      headline: best
        ? `Action Ranked · ${formatAction(best.action_type)}`
        : "Action Ranked",
      detail: best
        ? `Highest expected net revenue across ${hero.action_rankings.length} eligible actions · ENR ${formatINR(
            best.enr,
          )}`
        : undefined,
      tone: "ai",
      stage: "PIPELINE",
      payload: {
        rankings: hero.action_rankings.map((r) => ({
          rank: r.rank,
          action_type: r.action_type,
          enr: r.enr,
        })),
      },
    },
    {
      id: "policy_check",
      eventType: "policy_check",
      timestamp: auditAt("policy_check"),
      headline: `Policy Guard · ${hero.policy_decision.status}`,
      detail:
        hero.policy_decision.block_reason ??
        `${Object.values(hero.policy_decision.checks).filter(Boolean).length} of ${
          Object.keys(hero.policy_decision.checks).length
        } gates passed.`,
      tone:
        hero.policy_decision.status === "APPROVED"
          ? "neutral"
          : hero.policy_decision.status === "ESCALATED"
            ? "warning"
            : "critical",
      stage: "PIPELINE",
      payload: {
        status: hero.policy_decision.status,
        action_type: hero.policy_decision.action_type,
        checks: hero.policy_decision.checks,
        block_reason: hero.policy_decision.block_reason,
      },
      badge: <PolicyBadge status={hero.policy_decision.status} />,
    },
    {
      id: "action_executed",
      eventType: "action_executed",
      timestamp: auditAt("action_executed"),
      headline: `Gateway · ${formatAction(hero.execution.action_type)}`,
      detail: `Simulated gateway operation ${hero.execution.status}.`,
      tone: hero.execution.status === "executed" ? "recovery" : "warning",
      stage: "PIPELINE",
      payload: {
        action_type: hero.execution.action_type,
        status: hero.execution.status,
        idempotency_key: hero.execution.idempotency_key,
      },
    },
  ];

  return [...observed, ...pipeline];
}

function EntryNode({
  entry,
  last,
  showStageLabel,
}: {
  entry: TimelineEntry;
  last: boolean;
  showStageLabel: boolean;
}) {
  const [open, setOpen] = useState(false);
  const tone = TONE[entry.tone];

  return (
    <li>
      {showStageLabel && (
        <div className="flex items-center gap-3 py-4">
          <span className="mono text-[9px] uppercase tracking-eyebrow text-text-faint">
            {entry.stage === "OBSERVED" ? "Observable Event Stream" : "Pipeline Decisions"}
          </span>
          <span className="h-px flex-1 bg-border-subtle" />
        </div>
      )}

      <div className="flex gap-4 sm:gap-5">
        {/* ── Timestamp gutter ───────────────────────────────────────────── */}
        <div className="w-16 shrink-0 pt-0.5 text-right sm:w-24">
          <p className="mono tabular text-[11px] text-text-secondary sm:text-[13px]">
            {formatTime(entry.timestamp)}
          </p>
          <p className="mono hidden text-[9px] uppercase tracking-eyebrow text-text-faint sm:block">
            {formatDateTime(entry.timestamp).split(",")[0]}
          </p>
        </div>

        {/* ── Rail ───────────────────────────────────────────────────────── */}
        <div className="flex flex-col items-center">
          <span
            className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ring-4 transition-all duration-base ${tone.dot} ${tone.ring}`}
          />
          {!last && <span className="mt-1 w-px flex-1 bg-border-subtle" />}
        </div>

        {/* ── Panel ──────────────────────────────────────────────────────── */}
        <div className={`min-w-0 flex-1 ${last ? "pb-2" : "pb-6"}`}>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className={`group w-full rounded-panel border bg-surface px-4 py-3 text-left transition-all duration-base hover:bg-surface-elevated ${
              open ? tone.border : "border-border"
            }`}
          >
            <div className="flex items-baseline justify-between gap-3">
              <span className={`mono truncate text-[10px] uppercase tracking-eyebrow ${tone.text}`}>
                {entry.eventType}
              </span>
              {entry.badge}
            </div>

            <p className="mt-1.5 text-[14px] font-medium text-text-primary">{entry.headline}</p>

            {entry.detail && (
              <p className="mt-1 text-[12px] leading-relaxed text-text-muted">{entry.detail}</p>
            )}

            <span className="mono mt-2 inline-block text-[10px] uppercase tracking-eyebrow text-text-faint transition-colors duration-base group-hover:text-text-muted">
              {open ? "▾ collapse" : "▸ expand"}
            </span>
          </button>

          {open && (
            <div className="animate-fade-in mt-2 rounded-panel border border-border-subtle bg-bg-secondary/60 px-4 py-3">
              <PayloadViewer payload={entry.payload} defaultOpen />
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

export function EventTimeline({ entries }: { entries: TimelineEntry[] }) {
  let lastStage: string | null = null;

  return (
    <ol>
      {entries.map((entry, i) => {
        const showStageLabel = entry.stage !== lastStage;
        lastStage = entry.stage;
        return (
          <EntryNode
            key={entry.id}
            entry={entry}
            last={i === entries.length - 1}
            showStageLabel={showStageLabel}
          />
        );
      })}
    </ol>
  );
}
