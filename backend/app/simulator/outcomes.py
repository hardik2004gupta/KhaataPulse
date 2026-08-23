"""
SIMULATOR INTERNAL — PotentialOutcomes

Stores P(payment | action) and P(churn | action) for each customer × action pair.
These values are generated independently of any policy or agent decision.

CLAUDE.md §7: "The agent does not see them.
              Only the evaluation harness uses them to calculate policy performance."

Action types match the RecoveryProposal.proposed_action contract in CLAUDE.md §11.
"""
import random
from dataclasses import dataclass
from decimal import Decimal

from app.simulator.latent_state import CustomerLatentState, derive_cause


ACTION_TYPES = ("no_action", "silent_retry", "smart_link", "grace_period", "human_escalation")


@dataclass(frozen=True)
class ActionOutcome:
    p_payment: float   # probability of successful payment given this action
    p_churn: float     # probability of churn given this action


@dataclass(frozen=True)
class PotentialOutcomes:
    """
    HIDDEN from the agent. Only the evaluation harness may read these.
    """
    no_action: ActionOutcome
    silent_retry: ActionOutcome
    smart_link: ActionOutcome
    grace_period: ActionOutcome
    human_escalation: ActionOutcome

    def for_action(self, action_type: str) -> ActionOutcome:
        return getattr(self, action_type)

    def as_dict(self) -> dict[str, ActionOutcome]:
        return {a: self.for_action(a) for a in ACTION_TYPES}


# Cause-specific payment-probability multipliers per action.
# These encode the domain logic: which interventions work for which root causes.
_CAUSE_PAYMENT_MULTIPLIERS: dict[str, dict[str, float]] = {
    "card_expired": {
        "silent_retry": 0.85,   # retry won't fix an expired card
        "smart_link":   1.75,   # payment link lets them update card — very effective
        "grace_period": 1.10,
        "human_escalation": 1.55,
    },
    "billing_migration": {
        "silent_retry": 1.00,
        "smart_link":   1.55,   # link resolves entity mismatch
        "grace_period": 1.15,
        "human_escalation": 1.45,
    },
    "temporary_cash_flow": {
        "silent_retry": 1.05,
        "smart_link":   1.10,
        "grace_period": 1.65,   # grace period directly addresses cash-flow timing
        "human_escalation": 1.35,
    },
    "price_friction": {
        "silent_retry": 0.90,
        "smart_link":   1.05,
        "grace_period": 1.25,
        "human_escalation": 1.30,
    },
    "churn_intent": {
        "silent_retry": 0.80,
        "smart_link":   0.90,
        "grace_period": 1.15,
        "human_escalation": 1.20,
    },
}

# Churn-probability multipliers: how each action affects churn risk.
_ACTION_CHURN_MULTIPLIERS: dict[str, float] = {
    "no_action":         1.00,
    "silent_retry":      0.97,   # minimal impact
    "smart_link":        0.90,
    "grace_period":      0.78,   # reduced pressure → lower churn
    "human_escalation":  1.22,   # high pressure → higher churn risk
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def generate_outcomes(
    rng: random.Random,
    latent: CustomerLatentState,
) -> PotentialOutcomes:
    """Generate hidden potential outcomes from latent state using a deterministic RNG."""
    cause = derive_cause(latent, rng)
    mults = _CAUSE_PAYMENT_MULTIPLIERS.get(cause, {
        "silent_retry": 1.10,
        "smart_link":   1.20,
        "grace_period": 1.20,
        "human_escalation": 1.40,
    })

    noise_pay = 0.05
    noise_churn = 0.03

    base_pay = latent.payment_intent * latent.payment_rail_health * latent.cash_flow_health
    base_churn = latent.churn_sensitivity * (1.0 - latent.payment_intent) * 0.85

    def p_pay(mult: float) -> float:
        return _clamp(base_pay * mult + rng.gauss(0, noise_pay), 0.04, 0.97)

    def p_churn(churn_mult: float) -> float:
        return _clamp(base_churn * churn_mult + rng.gauss(0, noise_churn), 0.01, 0.95)

    return PotentialOutcomes(
        no_action=ActionOutcome(
            p_payment=_clamp(base_pay + rng.gauss(0, noise_pay), 0.04, 0.97),
            p_churn=p_churn(_ACTION_CHURN_MULTIPLIERS["no_action"]),
        ),
        silent_retry=ActionOutcome(
            p_payment=p_pay(mults["silent_retry"]),
            p_churn=p_churn(_ACTION_CHURN_MULTIPLIERS["silent_retry"]),
        ),
        smart_link=ActionOutcome(
            p_payment=p_pay(mults["smart_link"]),
            p_churn=p_churn(_ACTION_CHURN_MULTIPLIERS["smart_link"]),
        ),
        grace_period=ActionOutcome(
            p_payment=p_pay(mults["grace_period"]),
            p_churn=p_churn(_ACTION_CHURN_MULTIPLIERS["grace_period"]),
        ),
        human_escalation=ActionOutcome(
            p_payment=p_pay(mults["human_escalation"]),
            p_churn=p_churn(_ACTION_CHURN_MULTIPLIERS["human_escalation"]),
        ),
    )
