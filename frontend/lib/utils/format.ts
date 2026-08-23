// Financial formatting utilities - INR-aware

/** Format a Decimal string (from backend) as ₹ with lakh/crore suffix */
export function formatINR(value: string | number): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(n)) return "-";

  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";

  if (abs >= 10_000_000) {
    return `${sign}₹${(abs / 10_000_000).toFixed(2)} Cr`;
  }
  if (abs >= 100_000) {
    return `${sign}₹${(abs / 100_000).toFixed(2)} L`;
  }
  if (abs >= 1_000) {
    return `${sign}₹${abs.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  }
  return `${sign}₹${abs.toFixed(0)}`;
}

/** Format as percentage with 1 decimal, e.g. 0.6641 → "66.4%" */
export function formatPct(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/** Format basis points delta, e.g. 0.028 → "+2.8pp" */
export function formatPP(delta: number): string {
  const pp = delta * 100;
  const sign = pp >= 0 ? "+" : "";
  return `${sign}${pp.toFixed(1)}pp`;
}

/** Short number display for counts */
export function formatCount(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return String(n);
}

/** Format cause enum to readable label */
export function formatCause(cause: string): string {
  const map: Record<string, string> = {
    billing_migration: "Billing Migration",
    temporary_cash_flow: "Temporary Cash Flow",
    card_expired: "Card Expired",
    price_friction: "Price Friction",
    churn_intent: "Churn Intent",
  };
  return map[cause] ?? cause;
}

/** Format action enum to readable label */
export function formatAction(action: string): string {
  const map: Record<string, string> = {
    silent_retry: "Silent Retry",
    smart_link: "Smart Link",
    grace_period: "Grace Period",
    human_escalation: "Human Escalation",
    suppress: "Suppress",
    blocked: "Blocked",
    no_action: "No Action",
  };
  return map[action] ?? action;
}

/** Format risk level */
export function formatRiskLevel(level: string): string {
  return level.charAt(0) + level.slice(1).toLowerCase();
}

/* ── Risk colour ────────────────────────────────────────────────────────────
   Colour tracks the score itself, not the label attached to it, so the same
   number always reads the same way wherever it is rendered. Thresholds mirror
   the risk sieve's routing boundary (0.30) and its critical band (0.70).      */

export type RiskTone = "recovery" | "warning" | "critical";

export function riskTone(score: number): RiskTone {
  if (score >= 0.7) return "critical";
  if (score >= 0.3) return "warning";
  return "recovery";
}

const RISK_TEXT_CLASS: Record<RiskTone, string> = {
  recovery: "text-recovery-text",
  warning: "text-warning-text",
  critical: "text-critical-text",
};

const RISK_BAR_CLASS: Record<RiskTone, string> = {
  recovery: "bg-recovery",
  warning: "bg-warning",
  critical: "bg-critical",
};

/** Semantic text colour for a risk score. */
export function riskTextClass(score: number): string {
  return RISK_TEXT_CLASS[riskTone(score)];
}

/** Semantic fill colour for a risk score. */
export function riskBarClass(score: number): string {
  return RISK_BAR_CLASS[riskTone(score)];
}

/** Format ISO timestamp to HH:MM:SS */
export function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}

/** Format ISO timestamp to readable date+time */
export function formatDateTime(iso: string | null): string {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}
