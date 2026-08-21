"""
SIMULATOR INTERNAL — CustomerLatentState

This module is owned exclusively by the simulator.

The agent must NEVER receive a CustomerLatentState object or any value derived
directly from it (except through the observable event interface).

CLAUDE.md §7: "The agent must never receive this object."
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CustomerLatentState:
    """
    Hidden ground-truth state of a customer. Never serialized, never returned
    by any observable API, never passed to the agent or risk model as direct input.

    Fields:
        payment_intent:      Willingness to pay [0, 1]. High = customer wants to pay.
        cash_flow_health:    Liquidity of the customer [0, 1]. Low = cash-flow problems.
        payment_rail_health: Reliability of their payment method [0, 1]. Low = card issues.
        churn_sensitivity:   Propensity to cancel if pressured [0, 1]. High = fragile.
        customer_ltv:        Estimated lifetime value in INR (Decimal for exact arithmetic).
    """
    payment_intent: float
    cash_flow_health: float
    payment_rail_health: float
    churn_sensitivity: float
    customer_ltv: Decimal


def derive_cause(latent: CustomerLatentState, rng) -> str:
    """
    Derive the primary failure cause from latent state.
    Used internally to generate coherent observable events and outcomes.
    The agent must infer the cause independently from observable evidence.
    """
    pi = latent.payment_intent
    cf = latent.cash_flow_health
    pr = latent.payment_rail_health
    cs = latent.churn_sensitivity

    scores = {
        "card_expired":        (1.0 - pr) * 1.5,
        "billing_migration":   (1.0 - pr) * 0.8 * (pi + 0.2),   # rail issue but high intent
        "temporary_cash_flow": (1.0 - cf) * 1.4,
        "price_friction":      (1.0 - pi) * (1.0 - cs) * 1.2,
        "churn_intent":        cs * (1.0 - pi) * 1.5,
    }

    causes = list(scores.keys())
    weights = [max(0.001, scores[c] + rng.uniform(0, 0.05)) for c in causes]
    return rng.choices(causes, weights=weights)[0]
