"""
Expected Net Revenue formula — CLAUDE.md §13.

    ENR = P(payment | action) × Amount
        - P(churn  | action) × LTV
        - ActionCost

The optimizer uses ESTIMATED probabilities derived from observable data
(diagnosis cause + risk score), not the simulator's ground-truth PotentialOutcomes.
The evaluation harness uses ground-truth probabilities to measure policy performance.
This keeps the architectural boundary intact (CLAUDE.md §7).

All monetary calculations use Decimal to preserve precision — CLAUDE.md §19.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


# ── Estimated probability tables ─────────────────────────────────────────────
# These are model-level estimates, not simulator truth.

_BASE_P_PAYMENT: dict[str, float] = {
    "card_expired":        0.35,
    "billing_migration":   0.45,
    "temporary_cash_flow": 0.50,
    "price_friction":      0.38,
    "churn_intent":        0.22,
}

_PAYMENT_MULTIPLIERS: dict[str, dict[str, float]] = {
    "card_expired": {
        "silent_retry":      0.88,
        "smart_link":        1.85,
        "grace_period":      1.12,
        "human_escalation":  1.60,
        "suppress":          0.20,
    },
    "billing_migration": {
        "silent_retry":      1.02,
        "smart_link":        1.58,
        "grace_period":      1.18,
        "human_escalation":  1.45,
        "suppress":          0.25,
    },
    "temporary_cash_flow": {
        "silent_retry":      1.06,
        "smart_link":        1.12,
        "grace_period":      1.68,
        "human_escalation":  1.38,
        "suppress":          0.30,
    },
    "price_friction": {
        "silent_retry":      0.88,
        "smart_link":        1.08,
        "grace_period":      1.28,
        "human_escalation":  1.32,
        "suppress":          0.50,
    },
    "churn_intent": {
        "silent_retry":      0.78,
        "smart_link":        0.88,
        "grace_period":      1.18,
        "human_escalation":  1.22,
        "suppress":          0.60,
    },
}

_BASE_P_CHURN: dict[str, float] = {
    "card_expired":        0.12,
    "billing_migration":   0.18,
    "temporary_cash_flow": 0.22,
    "price_friction":      0.32,
    "churn_intent":        0.55,
}

_CHURN_MULTIPLIERS: dict[str, float] = {
    "silent_retry":      0.97,
    "smart_link":        0.90,
    "grace_period":      0.78,
    "human_escalation":  1.22,
    "suppress":          0.82,
}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def estimate_probabilities(cause: str, action_type: str) -> tuple[float, float]:
    """
    Estimate P(payment|action) and P(churn|action) from diagnosis cause + action type.

    Returns:
        (p_payment, p_churn) — both clamped to [0.04, 0.97] and [0.01, 0.95]
    """
    base_pay = _BASE_P_PAYMENT.get(cause, 0.40)
    mults = _PAYMENT_MULTIPLIERS.get(cause, {})
    pay_mult = mults.get(action_type, 1.10)
    p_payment = _clamp(base_pay * pay_mult, 0.04, 0.97)

    base_churn = _BASE_P_CHURN.get(cause, 0.20)
    churn_mult = _CHURN_MULTIPLIERS.get(action_type, 1.00)
    p_churn = _clamp(base_churn * churn_mult, 0.01, 0.95)

    return p_payment, p_churn


def compute_enr(
    p_payment: float,
    amount: Decimal,
    p_churn: float,
    ltv: Decimal,
    action_cost: Decimal,
) -> Decimal:
    """
    Expected Net Revenue = P(payment|action) × Amount
                         - P(churn|action)  × LTV
                         - ActionCost
    """
    return (
        Decimal(str(round(p_payment, 6))) * amount
        - Decimal(str(round(p_churn, 6))) * ltv
        - action_cost
    )


@dataclass(frozen=True)
class ActionRanking:
    """Result of ranking one action for one customer case."""
    action_type: str
    enr: Decimal
    estimated_p_payment: float
    estimated_p_churn: float
    action_cost: Decimal
