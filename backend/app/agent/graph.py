"""
LangGraph recovery reasoning graph - CLAUDE.md §9.

Full node order (all 9 required by the engineering contract):
  START → classify_context → generate_diagnosis → generate_action_proposal →
  validate_proposal → rank_actions → policy_check → execute_action →
  record_outcome → END

Phase 2 implements the first four nodes with business logic.
Phase 3 implements the final four nodes (rank_actions, policy_check,
execute_action, record_outcome) with real business logic.
"""
from __future__ import annotations

from typing import Optional

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agent.nodes import (
    classify_context,
    generate_action_proposal,
    make_generate_diagnosis,
    make_execute_action,
    make_policy_check,
    make_rank_actions,
    make_record_outcome,
    validate_proposal,
)
from app.agent.reasoning import BaseReasoningModel, get_reasoning_model
from app.agent.state import RecoveryReasoningState


def build_recovery_graph(
    reasoning_model: BaseReasoningModel | None = None,
    db: Optional[Session] = None,
) -> "CompiledGraph":
    """
    Compile the single-stage recovery reasoning graph.

    Args:
        reasoning_model: LLM provider to inject. Defaults to get_reasoning_model()
                         which returns Anthropic in production or Stub in demo/CI.
        db:              DB session for Phase 3 nodes (policy_check, execute_action,
                         record_outcome). If None, DB operations are skipped.

    Returns:
        Compiled LangGraph ready for invoke().
    """
    if reasoning_model is None:
        reasoning_model = get_reasoning_model()

    builder = StateGraph(RecoveryReasoningState)

    # ── Nodes (CLAUDE.md §9 order) ────────────────────────────────────────────
    builder.add_node("classify_context", classify_context)
    builder.add_node("generate_diagnosis", make_generate_diagnosis(reasoning_model))
    builder.add_node("generate_action_proposal", generate_action_proposal)
    builder.add_node("validate_proposal", validate_proposal)
    # Phase 3 nodes - fully implemented
    builder.add_node("rank_actions", make_rank_actions())
    builder.add_node("policy_check", make_policy_check(db=db))
    builder.add_node("execute_action", make_execute_action(db=db))
    builder.add_node("record_outcome", make_record_outcome(db=db))

    # ── Edges (single-stage, deterministic) ───────────────────────────────────
    builder.add_edge(START, "classify_context")
    builder.add_edge("classify_context", "generate_diagnosis")
    builder.add_edge("generate_diagnosis", "generate_action_proposal")
    builder.add_edge("generate_action_proposal", "validate_proposal")
    builder.add_edge("validate_proposal", "rank_actions")
    builder.add_edge("rank_actions", "policy_check")
    builder.add_edge("policy_check", "execute_action")
    builder.add_edge("execute_action", "record_outcome")
    builder.add_edge("record_outcome", END)

    return builder.compile()


# ── State factory ─────────────────────────────────────────────────────────────

def make_initial_state(
    customer_id: int,
    risk_score: float,
    risk_level: str,
    risk_signals: list[dict],
    subscription_context: dict,
    payment_context: list[dict],
    observable_events: list[dict],
    support_context: str = "",
    ltv: float = 0.0,
    dispute_hold: bool = False,
    legal_hold: bool = False,
    opt_out: bool = False,
) -> RecoveryReasoningState:
    """
    Build the initial graph state from observable data only.
    All hidden-state fields are absent by design.
    """
    return RecoveryReasoningState(
        customer_id=customer_id,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_signals=risk_signals,
        subscription_context=subscription_context,
        payment_context=payment_context,
        observable_events=observable_events,
        support_context=support_context,
        ltv=ltv,
        dispute_hold=dispute_hold,
        legal_hold=legal_hold,
        opt_out=opt_out,
        context_classification=None,
        diagnosis=None,
        recovery_proposal=None,
        validated_proposal=None,
        used_fallback=False,
        fallback_reason=None,
        eligible_actions=None,
        action_rankings=None,
        selected_action=None,
        ranked_actions=None,
        policy_decision=None,
        execution_result=None,
        recorded_outcome=None,
        case_id=None,
    )
