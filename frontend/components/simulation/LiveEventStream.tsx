"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { demoApi } from "@/lib/api/demo";
import type { SimulationStep, SimulationResponse } from "@/lib/types";
import { Eyebrow } from "@/components/ui/StateViews";
import { PolicyBadge } from "@/components/ui/PolicyBadge";
import { PayloadViewer } from "@/components/risk/PayloadViewer";
import { formatINR } from "@/lib/utils/format";

const STEP_STYLES: Record<string, { dot: string; text: string; border: string }> = {
  payment_failed: { dot: "bg-critical", text: "text-critical-text", border: "border-critical/35" },
  risk_detected: { dot: "bg-warning", text: "text-warning-text", border: "border-warning/35" },
  diagnosis_generated: { dot: "bg-ai", text: "text-ai-text", border: "border-ai/35" },
  action_ranked: { dot: "bg-ai", text: "text-ai-text", border: "border-ai/35" },
  policy_check: { dot: "bg-text-muted", text: "text-text-secondary", border: "border-border" },
  action_executed: { dot: "bg-recovery", text: "text-recovery-text", border: "border-recovery/35" },
};

const FALLBACK = { dot: "bg-text-muted", text: "text-text-secondary", border: "border-border" };

/** Compact horizontal progress rail across the six pipeline stages. */
function StageRail({ steps, done }: { steps: SimulationStep[]; done: number }) {
  return (
    <ol className="flex items-center gap-1 overflow-x-auto pb-1">
      {steps.map((s, i) => {
        const style = STEP_STYLES[s.step] ?? FALLBACK;
        const reached = i < done;
        const active = i === done;
        return (
          <li key={s.step} className="flex min-w-0 flex-1 items-center gap-1">
            <div className="flex min-w-0 flex-col items-start gap-1.5">
              <span
                className={`h-1.5 w-1.5 shrink-0 rounded-full transition-all duration-base ${
                  reached ? style.dot : active ? `${style.dot} animate-pulse-glow` : "bg-border"
                }`}
              />
              <span
                className={`mono truncate text-[9px] uppercase tracking-eyebrow transition-colors duration-base ${
                  reached ? style.text : "text-text-faint"
                }`}
              >
                {s.step}
              </span>
            </div>
            {i < steps.length - 1 && (
              <span
                className={`mt-[-14px] h-px flex-1 transition-colors duration-base ${
                  reached ? "bg-border" : "bg-border-subtle"
                }`}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}

function StepCard({ step, index }: { step: SimulationStep; index: number }) {
  const style = STEP_STYLES[step.step] ?? FALLBACK;
  const policyStatus = (step.data as { status?: string })?.status;

  return (
    <li
      className={`animate-rise-in rounded-panel border-l-2 ${style.border} bg-surface-elevated/40 px-4 py-3`}
      style={{ animationDelay: `${index * 40}ms` }}
    >
      <div className="flex items-baseline justify-between gap-3">
        <span className={`mono truncate text-[11px] font-semibold ${style.text}`}>
          {step.step}
        </span>
        <span className="mono shrink-0 text-[10px] uppercase tracking-eyebrow text-text-faint">
          {step.actor}
        </span>
      </div>

      <p className="mt-1 text-[13px] text-text-secondary">{step.description}</p>

      {step.step === "policy_check" && policyStatus && (
        <div className="mt-2">
          <PolicyBadge status={policyStatus as "APPROVED" | "BLOCKED" | "ESCALATED"} />
        </div>
      )}

      <PayloadViewer payload={step.data} />
    </li>
  );
}

export function LiveEventStream() {
  const [state, setState] = useState<"idle" | "loading" | "streaming" | "done" | "error">("idle");
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [visibleCount, setVisibleCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const timers = useRef<number[]>([]);

  const clearTimers = () => {
    timers.current.forEach((t) => window.clearTimeout(t));
    timers.current = [];
  };

  useEffect(() => clearTimers, []);

  const runSimulation = useCallback(async () => {
    clearTimers();
    setState("loading");
    setSimulation(null);
    setVisibleCount(0);
    setError(null);

    try {
      const result = await demoApi.runSimulation();
      setSimulation(result);
      setState("streaming");

      result.steps.forEach((_, i) => {
        const id = window.setTimeout(
          () => {
            setVisibleCount(i + 1);
            if (i === result.steps.length - 1) setState("done");
          },
          550 * (i + 1),
        );
        timers.current.push(id);
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
      setState("error");
    }
  }, []);

  const busy = state === "loading" || state === "streaming";

  return (
    <section>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Eyebrow>Live Webhook Simulation</Eyebrow>
          <p className="mt-1.5 max-w-prose text-[13px] text-text-secondary">
            Replays a payment failure through the full pipeline — risk sieve, diagnosis,
            optimizer, policy guard, gateway.
          </p>
        </div>

        <button
          type="button"
          onClick={runSimulation}
          disabled={busy}
          className={`mono shrink-0 rounded px-4 py-2.5 text-[10px] font-semibold uppercase tracking-eyebrow transition-all duration-base ${
            busy
              ? "cursor-wait bg-surface text-text-muted"
              : "bg-ai text-white shadow-glow-ai hover:brightness-110"
          }`}
        >
          {state === "loading"
            ? "Dispatching…"
            : state === "streaming"
              ? "Streaming…"
              : "⚡ Simulate Payment Webhook"}
        </button>
      </div>

      <div className="mt-4 min-h-[220px] rounded-panel border border-border bg-surface p-5">
        {state === "idle" && (
          <div className="flex flex-col items-center justify-center gap-2 py-14 text-center">
            <span className="mono text-[10px] uppercase tracking-eyebrow text-text-muted">
              Pipeline idle
            </span>
            <p className="max-w-prose text-xs text-text-faint">
              Trigger a webhook to watch the full KhaataPulse pipeline execute stage by stage.
            </p>
          </div>
        )}

        {state === "loading" && (
          <div className="flex flex-col items-center justify-center gap-2 py-14 text-center">
            <span className="mono text-[10px] uppercase tracking-eyebrow text-ai-text">
              Dispatching webhook…
            </span>
          </div>
        )}

        {state === "error" && (
          <div className="flex flex-col items-center justify-center gap-2 py-14 text-center">
            <span className="mono text-[10px] uppercase tracking-eyebrow text-critical-text">
              ✕ Simulation Failed
            </span>
            <p className="max-w-prose text-xs text-text-muted">
              {error ?? "The demo service could not be reached."}
            </p>
            <button
              type="button"
              onClick={runSimulation}
              className="mono mt-1 rounded border border-critical/40 px-3 py-1.5 text-[10px] uppercase tracking-eyebrow text-critical-text transition-colors duration-base hover:bg-critical/10"
            >
              Retry
            </button>
          </div>
        )}

        {simulation && (
          <div>
            {/* Customer context */}
            <div className="flex items-center justify-between gap-4 border-b border-border pb-4">
              <div className="min-w-0">
                <p className="truncate font-semibold text-text-primary">
                  {simulation.customer.name}
                </p>
                <p className="mono truncate text-[10px] uppercase tracking-eyebrow text-text-muted">
                  {simulation.customer.segment} · {simulation.subscription.plan}
                </p>
              </div>
              <p className="tabular shrink-0 text-lg font-bold text-text-primary">
                {formatINR(simulation.subscription.amount)}
              </p>
            </div>

            {/* Stage rail */}
            <div className="py-4">
              <StageRail steps={simulation.steps} done={visibleCount} />
            </div>

            {/* Revealed steps */}
            <ol className="space-y-2">
              {simulation.steps.slice(0, visibleCount).map((step, i) => (
                <StepCard key={step.step} step={step} index={i} />
              ))}
            </ol>

            {state === "streaming" && (
              <p className="mono mt-3 flex items-center gap-2 text-[10px] uppercase tracking-eyebrow text-text-muted">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-ai animate-pulse-glow" />
                Processing stage {visibleCount + 1} of {simulation.steps.length}
              </p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
