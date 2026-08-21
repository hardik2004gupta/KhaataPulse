"use client";
import { useState, useCallback } from "react";
import { demoApi } from "@/lib/api/demo";
import type { SimulationStep, SimulationResponse } from "@/lib/types";
import { formatAction } from "@/lib/utils/format";
import { PolicyBadge } from "@/components/ui/PolicyBadge";

const STEP_STYLES: Record<string, { dot: string; label: string }> = {
  payment_failed:      { dot: "bg-critical",  label: "text-critical-text" },
  risk_detected:       { dot: "bg-warning",   label: "text-warning-text"  },
  diagnosis_generated: { dot: "bg-ai",        label: "text-ai-text"       },
  action_ranked:       { dot: "bg-ai",        label: "text-ai-text"       },
  policy_check:        { dot: "bg-recovery",  label: "text-recovery-text" },
  action_executed:     { dot: "bg-recovery",  label: "text-recovery-text" },
};

function StepItem({
  step,
  visible,
  index,
}: {
  step: SimulationStep;
  visible: boolean;
  index: number;
}) {
  const style = STEP_STYLES[step.step] ?? { dot: "bg-text-muted", label: "text-text-secondary" };
  const [expanded, setExpanded] = useState(false);

  if (!visible) return null;

  return (
    <div
      className="relative flex gap-3 animate-fade-in pb-4"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Connector line */}
      <div className="flex flex-col items-center">
        <div className={`w-2.5 h-2.5 rounded-full shrink-0 mt-1 ${style.dot} ${index === 0 ? "" : ""}`} />
        <div className="w-px flex-1 bg-border mt-1.5" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-2">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className={`mono text-xs font-semibold ${style.label}`}>{step.step}</span>
          <span className="text-xs text-text-muted">{step.actor}</span>
        </div>
        <p className="text-sm text-text-secondary mt-0.5">{step.description}</p>

        {/* Policy check badge */}
        {step.step === "policy_check" && (step.data as { status?: string }).status && (
          <div className="mt-2">
            <PolicyBadge status={(step.data as { status: string }).status as "APPROVED" | "BLOCKED" | "ESCALATED"} />
          </div>
        )}

        {/* Expand payload */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-1 text-xs text-text-faint hover:text-text-muted transition-colors mono"
        >
          {expanded ? "▾ hide payload" : "▸ show payload"}
        </button>
        {expanded && (
          <pre className="mt-2 text-xs mono text-text-secondary bg-bg-secondary border border-border rounded p-3 overflow-x-auto">
            {JSON.stringify(step.data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

export function LiveEventStream() {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [visibleCount, setVisibleCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = useCallback(async () => {
    setState("loading");
    setSimulation(null);
    setVisibleCount(0);
    setError(null);

    try {
      const result = await demoApi.runSimulation();
      setSimulation(result);
      setState("done");

      // Reveal steps one by one
      for (let i = 1; i <= result.steps.length; i++) {
        await new Promise<void>((res) => setTimeout(res, 600));
        setVisibleCount(i);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
      setState("error");
    }
  }, []);

  return (
    <section>
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <p className="text-xs font-semibold tracking-widest uppercase text-text-muted mb-0.5">
            Live Pipeline Simulation
          </p>
          <p className="text-xs text-text-faint">
            Runs the full KhaataPulse pipeline on the hero customer in real-time
          </p>
        </div>

        <button
          onClick={runSimulation}
          disabled={state === "loading"}
          className={`
            px-4 py-2 text-sm font-semibold rounded border transition-all
            ${state === "loading"
              ? "bg-surface border-border text-text-muted cursor-wait"
              : "bg-ai-dim border-ai/40 text-ai-text hover:bg-ai/20 cursor-pointer"
            }
          `}
        >
          {state === "loading" ? "Running…" : "⚡ Simulate Payment Webhook"}
        </button>
      </div>

      <div className="bg-surface border border-border rounded-lg p-5 min-h-[200px]">
        {state === "idle" && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <p className="text-text-muted text-sm">
              Click <span className="text-ai-text font-semibold">Simulate Payment Webhook</span> to see the full KhaataPulse pipeline execute step by step.
            </p>
          </div>
        )}

        {state === "error" && (
          <div className="py-8 text-center">
            <p className="text-critical-text text-sm">{error ?? "Simulation failed. Is the backend running?"}</p>
          </div>
        )}

        {simulation && (
          <div>
            <div className="flex items-center gap-3 mb-5 pb-4 border-b border-border">
              <div>
                <p className="text-text-primary font-semibold">{simulation.customer.name}</p>
                <p className="text-xs text-text-muted mono">
                  {simulation.customer.segment} · ₹{parseFloat(simulation.subscription.amount).toLocaleString("en-IN")} / renewal
                </p>
              </div>
            </div>

            <div>
              {simulation.steps.map((step, i) => (
                <StepItem
                  key={step.step}
                  step={step}
                  visible={i < visibleCount}
                  index={i}
                />
              ))}
            </div>

            {visibleCount < simulation.steps.length && state === "done" && (
              <div className="flex items-center gap-2 text-text-muted text-xs mt-2">
                <span className="animate-pulse-glow w-1.5 h-1.5 rounded-full bg-ai" />
                Processing…
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
