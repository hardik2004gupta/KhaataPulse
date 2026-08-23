"use client";

import { useCallback, useState } from "react";
import type { AnimationEvent, CSSProperties } from "react";
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

/**
 * Compact horizontal progress rail across the six pipeline stages.
 * Each node lights up on the same 400ms CSS cadence as its step card.
 */
function StageRail({ steps }: { steps: SimulationStep[] }) {
  return (
    <ol className="flex items-center gap-1 overflow-x-auto pb-1">
      {steps.map((s, i) => {
        const style = STEP_STYLES[s.step] ?? FALLBACK;
        return (
          <li key={s.step} className="flex min-w-0 flex-1 items-center gap-1">
            <div
              style={{ "--step-index": i } as CSSProperties}
              className="rail-node flex min-w-0 flex-col items-start gap-1.5"
            >
              <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${style.dot}`} />
              <span
                className={`mono truncate text-[9px] uppercase tracking-eyebrow ${style.text}`}
              >
                {s.step}
              </span>
            </div>
            {i < steps.length - 1 && (
              <span
                style={{ "--step-index": i } as CSSProperties}
                className="rail-link mt-[-14px] h-px flex-1 bg-border"
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}

function StepCard({
  step,
  index,
  onSettled,
}: {
  step: SimulationStep;
  index: number;
  /** Fired by the final card once its reveal animation finishes. */
  onSettled?: (e: AnimationEvent<HTMLLIElement>) => void;
}) {
  const style = STEP_STYLES[step.step] ?? FALLBACK;
  const policyStatus = (step.data as { status?: string })?.status;

  return (
    <li
      style={{ "--step-index": index } as CSSProperties}
      onAnimationEnd={onSettled}
      className={`pipeline-step rounded-panel border-l-2 ${style.border} bg-surface-elevated/40 px-4 py-3`}
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
  const [error, setError] = useState<string | null>(null);
  /** Remounts the step list so a re-run replays the reveal from the start. */
  const [runToken, setRunToken] = useState(0);

  const runSimulation = useCallback(async () => {
    setState("loading");
    setSimulation(null);
    setError(null);

    try {
      const result = await demoApi.runSimulation();
      setSimulation(result);
      setRunToken((t) => t + 1);
      /* Stage reveal is owned entirely by CSS (`.pipeline-step`, 400ms apart).
         Completion is signalled by the last card's animationend rather than a
         timer chain, so a reduced-motion reader - whose animations collapse to
         near-zero - reaches the finished state immediately. */
      setState("streaming");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
      setState("error");
    }
  }, []);

  const handleFinalStep = useCallback((e: AnimationEvent<HTMLLIElement>) => {
    // Ignore animations bubbling up from nested payload controls.
    if (e.target !== e.currentTarget) return;
    setState("done");
  }, []);

  const busy = state === "loading" || state === "streaming";

  return (
    <section>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Eyebrow>Live Webhook Simulation</Eyebrow>
          <p className="mt-1.5 max-w-prose text-[13px] text-text-secondary">
            Replays a payment failure through the full pipeline - risk sieve, diagnosis,
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
            <div className="py-4" key={`rail-${runToken}`}>
              <StageRail steps={simulation.steps} />
            </div>

            {/* Stages reveal in sequence - see `.pipeline-step` in globals.css */}
            <ol className="space-y-2" key={`steps-${runToken}`}>
              {simulation.steps.map((step, i) => (
                <StepCard
                  key={step.step}
                  step={step}
                  index={i}
                  onSettled={
                    i === simulation.steps.length - 1 ? handleFinalStep : undefined
                  }
                />
              ))}
            </ol>

            <p
              className={`mono mt-3 flex items-center gap-2 text-[10px] uppercase tracking-eyebrow ${
                state === "done" ? "text-recovery-text" : "text-text-muted"
              }`}
              aria-live="polite"
            >
              <span
                className={`inline-block h-1.5 w-1.5 rounded-full ${
                  state === "done" ? "bg-recovery" : "bg-ai animate-pulse-glow"
                }`}
              />
              {state === "done"
                ? `Pipeline complete · ${simulation.steps.length} stages`
                : "Executing pipeline…"}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
