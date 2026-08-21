"use client";
import { useState, useEffect } from "react";
import type { RecoveryCase, AuditEvent } from "@/lib/types";
import { formatINR, formatDateTime, formatCause, formatAction } from "@/lib/utils/format";
import { PolicyBadge } from "@/components/ui/PolicyBadge";
import { RiskIndicator } from "@/components/ui/RiskIndicator";
import { AuditTimeline } from "./AuditTimeline";
import { casesApi } from "@/lib/api/cases";

interface CaseDetailResponse extends RecoveryCase {
  customer_ltv?: string | null;
  audit_events?: AuditEvent[];
}

interface CaseDetailDrawerProps {
  case_: RecoveryCase | null;
  onClose: () => void;
}

export function CaseDetailDrawer({ case_, onClose }: CaseDetailDrawerProps) {
  const [detail, setDetail] = useState<CaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!case_) { setDetail(null); return; }
    setLoading(true);
    casesApi.getCase(case_.id)
      .then((d) => setDetail(d as CaseDetailResponse))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [case_?.id]);

  const data = detail ?? case_;

  return (
    <>
      {/* Overlay */}
      <div
        className={`drawer-overlay ${case_ ? "active" : ""}`}
        onClick={onClose}
      />

      {/* Drawer */}
      <aside className={`drawer ${case_ ? "active" : ""}`}>
        {data && (
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b border-border shrink-0">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-semibold text-text-primary">{data.customer_name ?? "Unknown"}</p>
                  <p className="mono text-xs text-text-muted mt-0.5">
                    {data.customer_segment} · case #{data.id}
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="text-text-muted hover:text-text-primary transition-colors text-lg leading-none"
                >
                  ×
                </button>
              </div>

              {/* Quick stats */}
              <div className="grid grid-cols-3 gap-3 mt-4">
                <div>
                  <p className="text-xs text-text-muted">Renewal Amount</p>
                  <p className="tabular font-semibold text-text-primary text-sm">
                    {data.subscription_amount ? formatINR(data.subscription_amount) : "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-text-muted">Risk Score</p>
                  <RiskIndicator score={data.risk_score} level={data.risk_level ?? "LOW"} compact />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Policy</p>
                  {data.policy_status
                    ? <PolicyBadge status={data.policy_status as "APPROVED" | "BLOCKED" | "ESCALATED"} />
                    : <span className="text-text-muted text-xs">—</span>}
                </div>
              </div>
            </div>

            {/* Scrollable body */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
              {/* Diagnosis summary */}
              <div className="bg-ai-dim/30 border border-ai/20 rounded-lg p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-ai-text mb-3">
                  AI Diagnosis
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-text-muted mb-0.5">Cause</p>
                    <p className="font-semibold text-text-primary text-sm">
                      {data.diagnosis ? formatCause(data.diagnosis as Parameters<typeof formatCause>[0]) : "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-0.5">Confidence</p>
                    <p className={`font-semibold tabular text-sm ${
                      (data.diagnosis_confidence ?? 0) > 0.7 ? "text-recovery-text" : "text-warning-text"
                    }`}>
                      {data.diagnosis_confidence != null
                        ? `${Math.round(data.diagnosis_confidence * 100)}%`
                        : "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-0.5">Proposed Action</p>
                    <p className="font-semibold text-ai-text text-sm">
                      {data.proposed_action ? formatAction(data.proposed_action as Parameters<typeof formatAction>[0]) : "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-0.5">Selected Action</p>
                    <p className="font-semibold text-text-primary text-sm">
                      {data.selected_action ? formatAction(data.selected_action as Parameters<typeof formatAction>[0]) : "—"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Plan + Status */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface border border-border rounded-lg p-3">
                  <p className="text-xs text-text-muted mb-1">Plan</p>
                  <p className="text-sm font-medium text-text-secondary">{data.subscription_plan ?? "—"}</p>
                </div>
                <div className="bg-surface border border-border rounded-lg p-3">
                  <p className="text-xs text-text-muted mb-1">Outcome</p>
                  <p className="text-sm font-medium text-text-secondary">{data.outcome_status ?? "pending"}</p>
                </div>
                {(detail as CaseDetailResponse)?.customer_ltv && (
                  <div className="bg-surface border border-border rounded-lg p-3">
                    <p className="text-xs text-text-muted mb-1">Customer LTV</p>
                    <p className="tabular text-sm font-semibold text-text-primary">
                      {formatINR((detail as CaseDetailResponse).customer_ltv!)}
                    </p>
                  </div>
                )}
                {data.created_at && (
                  <div className="bg-surface border border-border rounded-lg p-3">
                    <p className="text-xs text-text-muted mb-1">Created</p>
                    <p className="mono text-xs text-text-secondary">{formatDateTime(data.created_at)}</p>
                  </div>
                )}
              </div>

              {/* Audit Trail */}
              {loading && (
                <p className="text-xs text-text-muted animate-pulse">Loading audit trail…</p>
              )}
              {!loading && detail?.audit_events && detail.audit_events.length > 0 && (
                <AuditTimeline events={detail.audit_events} />
              )}
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
