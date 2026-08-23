"""
Deterministic action ranker — CLAUDE.md §13.

Given the LLM diagnosis cause, subscription amount, and customer LTV,
ranks all eligible actions by Expected Net Revenue.

The optimizer is NOT the LLM. It is a deterministic financial function.
The LLM narrows the eligible set; the optimizer picks the best option.
"""
from __future__ import annotations

from decimal import Decimal

from app.optimizer.eligibility import get_eligible_actions
from app.optimizer.enr import ActionRanking, compute_enr, estimate_probabilities
from app.core.config import get_settings


def _action_cost(action_type: str) -> Decimal:
    """Return the cost of executing an action (INR). Config-driven per CLAUDE.md §25."""
    settings = get_settings()
    costs: dict[str, int] = {
        "silent_retry":      settings.action_cost_silent_retry,
        "smart_link":        settings.action_cost_smart_link,
        "grace_period":      settings.action_cost_grace_period,
        "human_escalation":  settings.action_cost_human_escalation,
        "suppress":          0,
    }
    return Decimal(str(costs.get(action_type, 0)))


def rank_eligible_actions(
    cause: str,
    amount: Decimal,
    ltv: Decimal,
) -> list[ActionRanking]:
    """
    Rank all eligible actions for a given cause by Expected Net Revenue.

    Returns:
        List of ActionRanking sorted descending by ENR (best first).
    """
    eligible = get_eligible_actions(cause)
    rankings: list[ActionRanking] = []

    for action_type in eligible:
        p_payment, p_churn = estimate_probabilities(cause, action_type)
        cost = _action_cost(action_type)
        enr = compute_enr(p_payment, amount, p_churn, ltv, cost)
        rankings.append(ActionRanking(
            action_type=action_type,
            enr=enr,
            estimated_p_payment=p_payment,
            estimated_p_churn=p_churn,
            action_cost=cost,
        ))

    return sorted(rankings, key=lambda r: r.enr, reverse=True)
