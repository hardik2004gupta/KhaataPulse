"use client";

import { useEffect, useState } from "react";
import type {
  RecoveryCase,
  AuditEvent,
  ActionRanking,
  PolicyDecision,
} from "@/lib/types";
import { formatINR, formatDateTime, formatCause, formatAction } from "@/lib/utils/format";
import { PolicyBadge } from "@/components/ui/PolicyBadge";
import { Eyebrow } from "@/components/ui/StateViews";
import { AuditTimeline } from "./AuditTimeline";
import { PolicyGuardViz } from "./PolicyGuardViz";
import { casesApi } from "@/lib/api/cases";

interface CaseDetailResponse extends RecoveryCase {
  customer_ltv?: string | null;
  audit_events?: AuditEvent[];
}

interface CaseDetailDrawerProps {
  case_: RecoveryCase | null;
  onClose: () => void;
}

/* ── Audit-payload extraction ───────────────────────────────────────────────
   The case-detail endpoint returns the immutable audit trail. Intervention
   rankings and policy checks are read back out of those payloads rather than
   reconstructed, so the drawer never displays anything the pipeline did not
   actually record.                                                          */

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function extractRankings(events: AuditEvent[]): ActionRanking[] {
  const ev = events.find((e) => e.event_type === "action_proposed");
  if (!ev || !isRecord(ev.payload)) return [];
  const raw = ev.payload.rankings;
  if (!Array.isArray(raw)) return [];

  return raw.flatMap((r, i): ActionRanking[] => {
    if (!isRecord(r) || typeof r.action_type !== "string") return [];
    return [
      {
        rank: typeof r.rank === "number" ? r.rank : i + 1,
        action_type: r.action_type,
        enr: String(r.enr ?? "0"),
        estimated_p_payment:
          typeof r.estimated_p_payment === "number" ? r.estimated_p_payment : 0,
        estimated_p_churn: typeof r.estimated_p_churn === "number" ? r.estimated_p_churn : 0,
        action_cost: String(r.action_cost ?? "0"),
      },
    ];
  });
}

function extractPolicyDecision(events: AuditEvent[]): PolicyDecision | null {
  const ev = events.find((e) => e.event_type === "policy_check");
  if (!ev || !isRecord(ev.payload)) return null;
  const p = ev.payload;

  const status = p.status;
  if (status !== "APPROVED" && status !== "BLOCKED" && status !== "ESCALATED") return null;

  const checks: Record<string, boolean> = {};
  if (isRecord(p.checks)) {
    Object.entries(p.checks).forEach(([k, v]) => {
      if (typeof v === "boolean") checks[k] = v;
    });
  }

  return {
    status,
    action_type: typeof p.action_type === "string" ? p.action_type : "",
    checks,
    block_reason: typeof p.block_reason === "string" ? p.block_reason : null,
  };
}

/* ── Presentation ─────────────────────────────────────────────────────────── */

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">{label}</p>
      <div className="mt-1 text-[13px] text-text-secondary">{value}</div>
    </div>
  );
}

export function CaseDetailDrawer({ case_, onClose }: CaseDetailDrawerProps) {
  const [detail, setDetail] = useState<CaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const caseId = case_?.id ?? null;

  useEffect(() => {
    if (caseId === null) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    casesApi
      .getCase(caseId)
      .then((d) => {
        if (!cancelled) setDetail(d as CaseDetailResponse);
      })
      .catch(() => {
        if (!cancelled) setDetail(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [caseId]);

  // Close on Escape.
  useEffect(() => {
    if (!case_) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [case_, onClose]);

  const open = case_ !== null;
  const data = detail ?? case_;
  const events = detail?.audit_events ?? [];
  const rankings = extractRankings(events);
  const decision = extractPolicyDecision(events);

  const confidence = data?.diagnosis_confidence ?? null;

  return (
    <>
      {open && <div className="drawer-overlay" onClick={onClose} aria-hidden="true" />}

      <aside
        className={`drawer transition-transform duration-base ease-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
        aria-hidden={!open}
      >
        {data && (
          <div className="flex h-full flex-col">
            {/* ── Header ─────────────────────────────────────────────────── */}
            <header className="shrink-0 border-b border-border bg-surface-elevated/50 px-6 py-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <Eyebrow>Recovery Case</Eyebrow>
                  <p className="mt-1.5 truncate font-semibold text-text-primary">
                    {data.customer_name ?? "Unknown customer"}
                  </p>
                  <p className="mono mt-0.5 truncate text-[10px] uppercase tracking-eyebrow text-text-muted">
                    {data.customer_segment ?? "—"} · case #{data.id}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={onClose}
                  aria-label="Close case detail"
                  className="shrink-0 rounded border border-border px-2 py-0.5 text-text-muted transition-colors duration-base hover:border-critical/40 hover:text-critical-text"
                >
                  ×
                </button>
              </div>
            </header>

            {/* ── Body ───────────────────────────────────────────────────── */}
            <div className="flex-1 space-y-6 overflow-y-auto px-6 py-5">
              {/* Customer */}
              <section>
                <Eyebrow>Customer</Eyebrow>
                <dl className="mt-3 grid grid-cols-2 gap-4">
                  <Stat label="Plan" value={data.subscription_plan ?? "—"} />
                  <Stat
                    label="Renewal Amount"
                    value={
                      <span className="tabular font-semibold text-text-primary">
                        {data.subscription_amount ? formatINR(data.subscription_amount) : "—"}
                      </span>
                    }
                  />
                  <Stat
                    label="Customer LTV"
                    value={
                      detail?.customer_ltv ? (
                        <span className="tabular">{formatINR(detail.customer_ltv)}</span>
                      ) : (
                        "—"
                      )
                    }
                  />
                  <Stat label="Created" value={formatDateTime(data.created_at)} />
                </dl>
              </section>

              {/* Risk */}
              <section className="border-t border-border-subtle pt-5">
                <Eyebrow>Risk</Eyebrow>
                <div className="mt-3 flex items-baseline gap-3">
                  <span
                    className={`tabular text-3xl font-bold leading-none tracking-tightest ${
                      data.risk_level === "HIGH"
                        ? "text-critical-text"
                        : data.risk_level === "MEDIUM"
                          ? "text-warning-text"
                          : "text-recovery-text"
                    }`}
                  >
                    {Math.round(data.risk_score * 100)}
                    <span className="text-base">%</span>
                  </span>
                  <span className="mono rounded border border-border px-2 py-0.5 text-[10px] uppercase tracking-eyebrow text-text-secondary">
                    {data.risk_level}
                  </span>
                </div>
              </section>

              {/* Diagnosis */}
              <section className="rounded-panel border-l-2 border-ai bg-ai-dim/20 p-4">
                <Eyebrow tone="ai">AI Diagnosis</Eyebrow>
                <p className="mt-2.5 text-base font-semibold text-text-primary">
                  {data.diagnosis ? formatCause(data.diagnosis) : "—"}
                </p>

                {confidence !== null && (
                  <div className="mt-3">
                    <p className="mono mb-1.5 text-[10px] uppercase tracking-eyebrow text-text-faint">
                      Confidence
                    </p>
                    <div className="flex items-center gap-3">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-bg-primary">
                        <div
                          className={`h-full rounded-full ${
                            confidence > 0.7 ? "bg-recovery" : "bg-warning"
                          }`}
                          style={{ width: `${Math.round(confidence * 100)}%` }}
                        />
                      </div>
                      <span
                        className={`mono tabular text-xs font-semibold ${
                          confidence > 0.7 ? "text-recovery-text" : "text-warning-text"
                        }`}
                      >
                        {Math.round(confidence * 100)}%
                      </span>
                    </div>
                  </div>
                )}

                <dl className="mt-4 grid grid-cols-2 gap-4 border-t border-ai/15 pt-3">
                  <Stat
                    label="Proposed"
                    value={
                      <span className="text-ai-text">
                        {data.proposed_action ? formatAction(data.proposed_action) : "—"}
                      </span>
                    }
                  />
                  <Stat
                    label="Selected"
                    value={
                      <span className="text-text-primary">
                        {data.selected_action ? formatAction(data.selected_action) : "—"}
                      </span>
                    }
                  />
                </dl>
              </section>

              {/* Intervention — from the action_proposed audit payload */}
              {rankings.length > 0 && (
                <section className="border-t border-border-subtle pt-5">
                  <div className="flex items-baseline justify-between gap-3">
                    <Eyebrow>Intervention</Eyebrow>
                    <span className="mono text-[10px] uppercase tracking-eyebrow text-text-faint">
                      Ranked by ENR
                    </span>
                  </div>
                  <ol className="mt-3 space-y-1.5">
                    {rankings.map((r) => {
                      const selected = r.rank === 1;
                      return (
                        <li
                          key={r.action_type}
                          className={`flex items-center justify-between gap-3 rounded border px-3 py-2 ${
                            selected
                              ? "border-recovery/35 bg-recovery-dim/25"
                              : "border-border-subtle bg-surface-elevated/50"
                          }`}
                        >
                          <span className="flex min-w-0 items-center gap-2.5">
                            <span
                              className={`mono text-[10px] ${
                                selected ? "text-recovery-text" : "text-text-faint"
                              }`}
                            >
                              {String(r.rank).padStart(2, "0")}
                            </span>
                            <span
                              className={`truncate text-[13px] ${
                                selected ? "font-medium text-text-primary" : "text-text-secondary"
                              }`}
                            >
                              {formatAction(r.action_type)}
                            </span>
                          </span>
                          <span
                            className={`tabular shrink-0 text-[13px] font-semibold ${
                              selected ? "text-recovery-text" : "text-text-muted"
                            }`}
                          >
                            {formatINR(r.enr)}
                          </span>
                        </li>
                      );
                    })}
                  </ol>
                </section>
              )}

              {/* Policy */}
              <section className="border-t border-border-subtle pt-5">
                {decision ? (
                  <PolicyGuardViz decision={decision} />
                ) : (
                  <>
                    <Eyebrow>Policy Guard</Eyebrow>
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <span className="text-[13px] text-text-secondary">Verdict</span>
                      {data.policy_status ? (
                        <PolicyBadge
                          status={data.policy_status as "APPROVED" | "BLOCKED" | "ESCALATED"}
                        />
                      ) : (
                        <span className="text-xs text-text-faint">—</span>
                      )}
                    </div>
                    <p className="mono mt-2 text-[10px] uppercase tracking-eyebrow text-text-faint">
                      Gate detail not present in this case&apos;s audit trail
                    </p>
                  </>
                )}
              </section>

              {/* Outcome */}
              <section className="border-t border-border-subtle pt-5">
                <Eyebrow>Outcome</Eyebrow>
                <dl className="mt-3 grid grid-cols-2 gap-4">
                  <Stat label="Status" value={data.outcome_status ?? "pending"} />
                  <Stat label="Closed" value={formatDateTime(data.closed_at)} />
                </dl>
              </section>

              {/* Audit */}
              <section className="border-t border-border-subtle pt-5">
                {loading ? (
                  <p className="mono py-4 text-center text-[10px] uppercase tracking-eyebrow text-text-muted">
                    Replaying policy decision…
                  </p>
                ) : events.length > 0 ? (
                  <AuditTimeline events={events} />
                ) : (
                  <>
                    <Eyebrow>Audit Trail</Eyebrow>
                    <p className="py-4 text-center text-xs text-text-muted">
                      No audit events recorded for this case.
                    </p>
                  </>
                )}
              </section>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
