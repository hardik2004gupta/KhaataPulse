"use client";

import { useCallback, useEffect, useState } from "react";
import { casesApi } from "@/lib/api/cases";
import type { RecoveryCase } from "@/lib/types";
import {
  formatINR,
  formatDateTime,
  formatCause,
  formatAction,
  riskBarClass,
  riskTextClass,
} from "@/lib/utils/format";
import { PolicyBadge } from "@/components/ui/PolicyBadge";
import { RowSkeleton } from "@/components/ui/Skeleton";
import { ErrorPanel } from "@/components/ui/StateViews";
import { EmptyState } from "@/components/ui/EmptyState";

interface RiskQueueProps {
  onSelect: (case_: RecoveryCase) => void;
  selectedId?: number | null;
  /** Lets the page render the case count in its header. */
  onLoaded?: (total: number) => void;
  /** Reported when the queue cannot be reached, so the header can say so. */
  onFailed?: () => void;
}

const COLUMNS = ["Customer", "Risk", "Amount", "Diagnosis", "Action", "Policy", "Created"];

/**
 * Colour tracks the score against the sieve's own thresholds, and the level is
 * always spelled out beside it - the strip colour never carries meaning alone.
 */
function RiskCell({ score, level }: { score: number; level: string }) {
  const pct = Math.round(score * 100);
  return (
    <span className="flex items-center gap-2">
      <span aria-hidden="true" className="h-1 w-10 overflow-hidden rounded-full bg-bg-primary">
        <span
          className={`block h-full rounded-full ${riskBarClass(score)}`}
          style={{ width: `${pct}%` }}
        />
      </span>
      <span className={`mono tabular text-[11px] font-semibold ${riskTextClass(score)}`}>
        {pct}%
      </span>
      <span className="mono text-[9px] uppercase tracking-eyebrow text-text-faint">{level}</span>
    </span>
  );
}

export function RiskQueue({
  onSelect,
  selectedId = null,
  onLoaded,
  onFailed,
}: RiskQueueProps) {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await casesApi.listCases(50);
      setCases(res.cases);
      onLoaded?.(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load cases");
      onFailed?.();
    } finally {
      setLoading(false);
    }
  }, [onLoaded, onFailed]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) {
    return (
      <ErrorPanel
        title="Risk Queue Unavailable"
        detail="The case service could not be reached. Confirm the backend and database are running, then retry."
        onRetry={load}
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-panel border border-border bg-surface">
      {/* ── Console header ───────────────────────────────────────────────── */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
        <span className="mono text-[10px] uppercase tracking-eyebrow text-text-muted">
          Recovery Queue
        </span>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="mono text-[10px] uppercase tracking-eyebrow text-text-faint transition-colors duration-base hover:text-text-secondary disabled:opacity-50"
        >
          ↺ Refresh
        </button>
      </div>

      {loading ? (
        <div>
          {Array.from({ length: 8 }).map((_, i) => (
            <RowSkeleton key={i} />
          ))}
        </div>
      ) : cases.length === 0 ? (
        <EmptyState
          title="No high-risk accounts in current cohort"
          description="The risk sieve routed no accounts into the recovery pipeline for this run."
        />
      ) : (
        <>
          {/* ── Desktop console ─────────────────────────────────────────── */}
          <table className="hidden w-full border-collapse md:table">
            <thead>
              <tr className="border-b border-border">
                {COLUMNS.map((c) => (
                  <th
                    key={c}
                    className={`mono px-4 py-2 text-[9px] uppercase tracking-eyebrow text-text-faint ${
                      c === "Amount" || c === "Created" ? "text-right" : "text-left"
                    }`}
                  >
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => {
                const selected = selectedId === c.id;
                return (
                  <tr
                    key={c.id}
                    onClick={() => onSelect(c)}
                    tabIndex={0}
                    role="button"
                    aria-label={`Open case ${c.id}${
                      c.customer_name ? ` - ${c.customer_name}` : ""
                    }`}
                    aria-pressed={selected}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        onSelect(c);
                      }
                    }}
                    className={`h-10 cursor-pointer border-b border-border-subtle transition-colors duration-base last:border-b-0 ${
                      selected ? "bg-surface-elevated" : "hover:bg-surface-elevated/60"
                    }`}
                  >
                    <td className="relative px-4 py-0">
                      <span
                        aria-hidden="true"
                        className={`absolute left-0 top-0 h-full w-0.5 ${
                          selected ? "bg-ai" : riskBarClass(c.risk_score)
                        }`}
                      />
                      <span className="flex min-w-0 items-baseline gap-2">
                        <span className="truncate text-[13px] font-medium text-text-primary">
                          {c.customer_name ?? `Case #${c.id}`}
                        </span>
                        <span className="mono shrink-0 text-[9px] uppercase tracking-eyebrow text-text-faint">
                          #{c.id}
                        </span>
                      </span>
                    </td>

                    <td className="px-4">
                      <RiskCell score={c.risk_score} level={c.risk_level} />
                    </td>

                    <td className="tabular px-4 text-right text-[13px] text-text-secondary">
                      {c.subscription_amount ? formatINR(c.subscription_amount) : "-"}
                    </td>

                    <td className="px-4 text-[12px] text-text-secondary">
                      {c.diagnosis ? formatCause(c.diagnosis) : "-"}
                    </td>

                    <td className="px-4 text-[12px] text-ai-text">
                      {c.selected_action
                        ? formatAction(c.selected_action)
                        : c.proposed_action
                          ? formatAction(c.proposed_action)
                          : "-"}
                    </td>

                    <td className="px-4">
                      {c.policy_status ? (
                        <PolicyBadge
                          status={c.policy_status as "APPROVED" | "BLOCKED" | "ESCALATED"}
                        />
                      ) : (
                        <span className="text-xs text-text-faint">-</span>
                      )}
                    </td>

                    <td className="mono tabular px-4 text-right text-[10px] text-text-faint">
                      {formatDateTime(c.created_at)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* ── Mobile cards ────────────────────────────────────────────── */}
          <ul className="divide-y divide-border-subtle md:hidden">
            {cases.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => onSelect(c)}
                  aria-label={`Open case ${c.id}${
                    c.customer_name ? ` - ${c.customer_name}` : ""
                  }`}
                  className="relative w-full px-4 py-3 text-left transition-colors duration-base hover:bg-surface-elevated/60"
                >
                  <span
                    aria-hidden="true"
                    className={`absolute left-0 top-0 h-full w-0.5 ${riskBarClass(c.risk_score)}`}
                  />
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="truncate text-[13px] font-medium text-text-primary">
                      {c.customer_name ?? `Case #${c.id}`}
                    </span>
                    <span className="tabular shrink-0 text-[13px] text-text-secondary">
                      {c.subscription_amount ? formatINR(c.subscription_amount) : "-"}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-3">
                    <RiskCell score={c.risk_score} level={c.risk_level} />
                    {c.diagnosis && (
                      <span className="text-[11px] text-text-muted">
                        {formatCause(c.diagnosis)}
                      </span>
                    )}
                    {c.policy_status && (
                      <PolicyBadge
                        status={c.policy_status as "APPROVED" | "BLOCKED" | "ESCALATED"}
                      />
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
