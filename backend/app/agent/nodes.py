"""
LangGraph node functions — CLAUDE.md §9, §25.

Node ordering (from CLAUDE.md §9):
  classify_context → generate_diagnosis → generate_action_proposal →
  validate_proposal → rank_actions → policy_check →
  execute_action → record_outcome

Phase 2 implements:  classify_context, generate_diagnosis,
                     generate_action_proposal, validate_proposal.
Phase 3 stubs:       rank_actions, policy_check, execute_action, record_outcome.
                     (pass state through unchanged; business logic added in Phase 3)

ISOLATION INVARIANT:
  No node may read or write latent_state, potential_outcomes, p_payment,
  p_churn, payment_intent, cash_flow_health, payment_rail_health,
  churn_sensitivity, or any hidden simulator variable.
"""
from __future__ import annotations

from pydantic import ValidationError

from app.agent.fallback import smart_retry_proposal
from app.agent.reasoning import BaseReasoningModel, ReasoningContext
from app.agent.schemas import RecoveryProposal
from app.agent.state import RecoveryReasoningState
from app.core.logging import get_logger

logger = get_logger(__name__)


# ─── classify_context ─────────────────────────────────────────────────────────

def classify_context(state: RecoveryReasoningState) -> dict:
    """
    Deterministically classify the observable context into a category tag.
    No LLM call. Derived purely from observable event types and payment history.
    """
    event_types = {e.get("event_type", "") for e in state["observable_events"]}
    failures = state["payment_context"]
    failure_codes = {p.get("failure_code") for p in failures if p.get("failure_code")}

    if "payment_method_changed" in event_types or "card_expired" in failure_codes:
        classification = "payment_rail_issue"
    elif "subscription_changed" in event_types:
        classification = "churn_risk"
    elif state["support_context"]:
        classification = "customer_contacted_support"
    elif state["risk_score"] >= 0.70:
        classification = "high_risk_no_signal"
    else:
        classification = "general_payment_risk"

    logger.info(
        "classify_context",
        extra={
            "kp_customer_id": state["customer_id"],
            "kp_classification": classification,
        },
    )
    return {"context_classification": classification}


# ─── generate_diagnosis ───────────────────────────────────────────────────────

def make_generate_diagnosis(model: BaseReasoningModel):
    """Factory: injects the LLM provider into the diagnosis node."""

    def generate_diagnosis(state: RecoveryReasoningState) -> dict:
        """
        Calls the LLM with observable context only (CLAUDE.md §18).
        On any failure, falls back to the smart-retry policy (CLAUDE.md §12).
        """
        context = ReasoningContext(
            customer_id=state["customer_id"],
            risk_score=state["risk_score"],
            risk_level=state["risk_level"],
            risk_signals=state["risk_signals"],
            subscription_info=state["subscription_context"],
            payment_failures=[
                p for p in state["payment_context"]
                if p.get("status") == "failed"
            ],
            observable_events=state["observable_events"],
            support_messages=[
                line.strip()
                for line in state["support_context"].split("\n---\n")
                if line.strip()
            ],
        )

        used_fallback = False
        fallback_reason: str | None = None

        try:
            proposal = model.reason(context)
        except Exception as exc:
            reason = type(exc).__name__ + ": " + str(exc)
            proposal = smart_retry_proposal(context, reason)
            used_fallback = True
            fallback_reason = reason

        logger.info(
            "diagnosis_generated",
            extra={
                "kp_customer_id": state["customer_id"],
                "kp_cause": proposal.cause,
                "kp_action": proposal.proposed_action,
                "kp_used_fallback": used_fallback,
            },
        )

        return {
            "diagnosis": proposal.model_dump(),
            "used_fallback": used_fallback,
            "fallback_reason": fallback_reason,
        }

    return generate_diagnosis


# ─── generate_action_proposal ─────────────────────────────────────────────────

def generate_action_proposal(state: RecoveryReasoningState) -> dict:
    """
    Extracts and confirms the proposed action from the diagnosis result.
    Validates that the action is from the allowed set.
    """
    diagnosis = state.get("diagnosis") or {}
    allowed_actions = {
        "silent_retry", "smart_link", "grace_period", "human_escalation", "suppress"
    }
    proposed_action = diagnosis.get("proposed_action", "silent_retry")
    if proposed_action not in allowed_actions:
        proposed_action = "silent_retry"

    proposal = {
        "proposed_action": proposed_action,
        "cause": diagnosis.get("cause", "temporary_cash_flow"),
        "confidence": diagnosis.get("confidence", 0.60),
        "rationale": diagnosis.get("rationale", ""),
        "risk_level": diagnosis.get("risk_level", state["risk_level"]),
    }
    return {"recovery_proposal": proposal}


# ─── validate_proposal ────────────────────────────────────────────────────────

def validate_proposal(state: RecoveryReasoningState) -> dict:
    """
    Final Pydantic validation of the recovery proposal (CLAUDE.md §20).
    Any validation failure is treated as an LLM failure and triggers fallback.
    The validated proposal is the authoritative output of the reasoning graph.
    """
    raw = state.get("recovery_proposal") or state.get("diagnosis") or {}
    try:
        validated = RecoveryProposal.model_validate(raw)
        return {"validated_proposal": validated.model_dump()}
    except (ValidationError, Exception) as exc:
        # Last-resort fallback: produce a safe default
        logger.error(
            "validate_proposal_failed",
            extra={
                "kp_customer_id": state["customer_id"],
                "kp_error": str(exc),
            },
        )
        safe = RecoveryProposal(
            cause="temporary_cash_flow",
            confidence=0.50,
            proposed_action="silent_retry",
            rationale=f"[validation fallback] {exc}",
            risk_level=state.get("risk_level", "MEDIUM"),
        )
        return {"validated_proposal": safe.model_dump(), "used_fallback": True}


# ─── Phase 3 stubs ────────────────────────────────────────────────────────────
# These nodes are required by CLAUDE.md §9 to be present in the graph.
# Business logic is added in Phase 3. For now they pass state through unchanged.

def rank_actions(state: RecoveryReasoningState) -> dict:
    """Phase 3: Economic Optimizer ranks actions by Expected Net Revenue."""
    return {"ranked_actions": None}


def policy_check(state: RecoveryReasoningState) -> dict:
    """Phase 3: Policy Guard deterministically approves/blocks/escalates."""
    return {"policy_decision": None}


def execute_action(state: RecoveryReasoningState) -> dict:
    """Phase 3: Action Service executes the approved, idempotent action."""
    return {"execution_result": None}


def record_outcome(state: RecoveryReasoningState) -> dict:
    """Phase 3: Outcome Engine records the result and closes the case."""
    return {"recorded_outcome": None}
