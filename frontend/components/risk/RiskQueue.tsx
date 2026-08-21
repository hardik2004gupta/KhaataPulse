"use client";
import { useEffect, useState, useCallback } from "react";
import { casesApi } from "@/lib/api/cases";
import type { RecoveryCase } from "@/lib/types";
import { formatINR, formatDateTime, formatCause, formatAction } from "@/lib/utils/format";
import { RiskIndicator } from "@/components/ui/RiskIndicator";
import { PolicyBadge } from "@/components/ui/PolicyBadge";
import { RowSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

interface RiskQueueProps {
  onSelect: (case_: RecoveryCase) => void;
}

export function RiskQueue({ onSelect }: RiskQueueProps) {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await casesApi.listCases(50);
      setCases(res.cases);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load cases");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Recovery Queue
        </p>
        <button
          onClick={load}
          disabled={loading}
          className="text-xs text-text-muted hover:text-text-secondary transition-colors mono"
        >
          ↺ refresh
        </button>
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        {loading ? (
          <div className="divide-y divide-border">
            {Array.from({ length: 6 }).map((_, i) => <RowSkeleton key={i} />)}
          </div>
        ) : error ? (
          <EmptyState
            title="Could not load cases"
            description={error}
            action={
              <button
                onClick={load}
                className="px-3 py-1.5 text-xs rounded border border-border text-text-secondary hover:text-text-primary transition-colors"
              >
                Retry
              </button>
            }
          />
        ) : cases.length === 0 ? (
          <EmptyState
            title="No recovery cases"
            description="Run a simulation to create recovery cases."
          />
        ) : (
          <div className="divide-y divide-border">
            {cases.map((c) => (
              <button
                key={c.id}
                onClick={() => onSelect(c)}
                className="w-full text-left px-4 py-3 hover:bg-surface-elevated transition-colors group"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="font-medium text-text-primary text-sm truncate">
                        {c.customer_name ?? `Case #${c.id}`}
                      </span>
                      {c.customer_segment && (
                        <span className="text-xs text-text-muted shrink-0">{c.customer_segment}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-text-muted flex-wrap">
                      <span className="mono">#{c.id}</span>
                      {c.diagnosis && (
                        <span>{formatCause(c.diagnosis as Parameters<typeof formatCause>[0])}</span>
                      )}
                      {c.proposed_action && (
                        <span className="text-ai-text">{formatAction(c.proposed_action as Parameters<typeof formatAction>[0])}</span>
                      )}
                      {c.created_at && (
                        <span className="text-text-faint">{formatDateTime(c.created_at)}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {c.subscription_amount && (
                      <span className="tabular text-sm font-semibold text-text-secondary">
                        {formatINR(c.subscription_amount)}
                      </span>
                    )}
                    <RiskIndicator score={c.risk_score} level={c.risk_level ?? "LOW"} compact />
                    {c.policy_status && (
                      <PolicyBadge status={c.policy_status as "APPROVED" | "BLOCKED" | "ESCALATED"} />
                    )}
                    <span className="text-text-faint group-hover:text-text-muted transition-colors text-sm">›</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
