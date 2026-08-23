"""
LangGraph state definition - CLAUDE.md §9, §17.

RecoveryReasoningState contains ONLY information the agent is permitted to see.
Hidden simulator state (CustomerLatentState, PotentialOutcomes, p_payment,
p_churn, payment_intent, cash_flow_health, etc.) must NEVER appear here.
"""
from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict


class RecoveryReasoningState(TypedDict):
    # ── Agent-visible input (observable data only) ────────────────────────────
    customer_id: int
    risk_score: float
    risk_level: str                 # LOW | MEDIUM | HIGH from the risk model
    risk_signals: list[dict]        # [{"feature": ..., "impact": ...}]

    # Observable subscription context
    subscription_context: dict      # plan, amount, currency, renewal_at, status

    # Observable payment history (no probabilities, no hidden state)
    payment_context: list[dict]     # status, failure_code, payment_method, amount

    # Observable events
    observable_events: list[dict]   # event_type + observable payload

    # Support message text
    support_context: str

    # Customer LTV (observable business metric - known to the agent)
    ltv: float

    # Customer hold flags (observable from CRM)
    dispute_hold: bool
    legal_hold: bool
    opt_out: bool

    # ── Node outputs ──────────────────────────────────────────────────────────
    context_classification: Optional[str]   # set by classify_context
    diagnosis: Optional[dict]               # set by generate_diagnosis
    recovery_proposal: Optional[dict]       # set by generate_action_proposal
    validated_proposal: Optional[dict]      # set by validate_proposal (final)

    # Fallback tracking
    used_fallback: bool
    fallback_reason: Optional[str]

    # ── Phase 3 outputs ───────────────────────────────────────────────────────
    eligible_actions: Optional[list]        # list of eligible action type strings
    action_rankings: Optional[list]         # list of ActionRanking dicts (sorted by ENR)
    selected_action: Optional[str]          # best action by ENR

    ranked_actions: Optional[list]          # deprecated alias kept for test compatibility
    policy_decision: Optional[dict]         # PolicyDecision as dict
    execution_result: Optional[dict]        # ActionResult as dict
    recorded_outcome: Optional[dict]        # recovery case summary
    case_id: Optional[int]                  # recovery_cases.id (set during execution)
