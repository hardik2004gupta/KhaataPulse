"use client";

import { useCallback, useState } from "react";
import type { RecoveryCase } from "@/lib/types";
import { CommandShell } from "@/components/shell/CommandShell";
import { RiskQueue } from "@/components/risk/RiskQueue";
import { CaseDetailDrawer } from "@/components/risk/CaseDetailDrawer";

type QueueStatus = { kind: "scanning" } | { kind: "ready"; total: number } | { kind: "failed" };

export default function CasesPage() {
  const [selected, setSelected] = useState<RecoveryCase | null>(null);
  const [status, setStatus] = useState<QueueStatus>({ kind: "scanning" });

  const handleLoaded = useCallback((n: number) => setStatus({ kind: "ready", total: n }), []);
  const handleFailed = useCallback(() => setStatus({ kind: "failed" }), []);

  return (
    <CommandShell>
      <div className="mx-auto max-w-shell space-y-6 px-5 py-7 sm:px-7">
        <header className="flex flex-col gap-4 border-b border-border-subtle pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tightest text-text-primary">Risk Queue</h1>
            <p className="mt-1.5 max-w-prose text-[13px] text-text-secondary">
              Accounts the risk sieve routed into the KhaataPulse recovery pipeline.
            </p>
          </div>

          <span
            className={`mono shrink-0 self-start rounded border px-3 py-1.5 text-[10px] uppercase tracking-eyebrow sm:self-auto ${
              status.kind === "failed"
                ? "border-critical/30 bg-critical-dim/20 text-critical-text"
                : "border-border text-text-muted"
            }`}
          >
            {status.kind === "scanning"
              ? "Scanning cohort…"
              : status.kind === "failed"
                ? "Queue unavailable"
                : `${status.total.toLocaleString("en-IN")} cases`}
          </span>
        </header>

        <RiskQueue
          onSelect={setSelected}
          selectedId={selected?.id ?? null}
          onLoaded={handleLoaded}
          onFailed={handleFailed}
        />
      </div>

      <CaseDetailDrawer case_={selected} onClose={() => setSelected(null)} />
    </CommandShell>
  );
}
