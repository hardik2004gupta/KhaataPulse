"""
LangGraph node functions - CLAUDE.md §9, §25.

Node ordering (from CLAUDE.md §9):
  classify_context → generate_diagnosis → generate_action_proposal →
  validate_proposal → rank_actions → policy_check →
  execute_action → record_outcome

ISOLATION INVARIANT:
  No node may read or write latent_state, potential_outcomes, p_payment,
  p_churn, payment_intent, cash_flow_health, payment_rail_health,
  churn_sensitivity, or any hidden simulator variable.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

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


# ─── rank_actions ─────────────────────────────────────────────────────────────

def make_rank_actions():
    """Factory that returns the rank_actions node (no external injection needed)."""

    def rank_actions(state: RecoveryReasoningState) -> dict:
        """
        Economic Optimizer - CLAUDE.md §13.

        Ranks eligible actions by Expected Net Revenue using observable inputs only.
        The optimizer uses estimated probabilities (not simulator truth).
        """
        from app.optimizer.ranker import rank_eligible_actions

        proposal = state.get("validated_proposal") or {}
        cause = proposal.get("cause", "temporary_cash_flow")

        amount_raw = state["subscription_context"].get("amount", 0)
        amount = Decimal(str(amount_raw))
        ltv = Decimal(str(state.get("ltv", 0)))

        rankings = rank_eligible_actions(cause=cause, amount=amount, ltv=ltv)
        eligible = [r.action_type for r in rankings]
        selected = rankings[0].action_type if rankings else proposal.get("proposed_action", "silent_retry")

        rankings_dicts = [
            {
                "action_type": r.action_type,
                "enr": str(r.enr),
                "estimated_p_payment": r.estimated_p_payment,
                "estimated_p_churn": r.estimated_p_churn,
                "action_cost": str(r.action_cost),
            }
            for r in rankings
        ]

        logger.info(
            "actions_ranked",
            extra={
                "kp_customer_id": state["customer_id"],
                "kp_cause": cause,
                "kp_selected_action": selected,
                "kp_rankings_count": len(rankings),
            },
        )

        return {
            "eligible_actions": eligible,
            "action_rankings": rankings_dicts,
            "selected_action": selected,
            "ranked_actions": rankings_dicts,  # backward-compat alias
        }

    return rank_actions


# ─── policy_check ─────────────────────────────────────────────────────────────

def make_policy_check(db: Optional[Session] = None):
    """Factory: injects the DB session into the policy_check node."""

    def policy_check(state: RecoveryReasoningState) -> dict:
        """
        Policy Guard - CLAUDE.md §14.

        Pure deterministic. All rules checked. Returns APPROVED / BLOCKED / ESCALATED.
        No code path may skip this node.
        """
        from app.policy.guard import policy_guard

        action_type = state.get("selected_action") or "silent_retry"
        amount_raw = state["subscription_context"].get("amount", 0)
        amount = Decimal(str(amount_raw))

        customer_id = state["customer_id"]
        case_id = state.get("case_id", 0)
        idempotency_key = f"rec_CASE_{case_id}"

        decision = policy_guard(
            customer_id=customer_id,
            action_type=action_type,
            amount=amount,
            idempotency_key=idempotency_key,
            dispute_hold=state.get("dispute_hold", False),
            legal_hold=state.get("legal_hold", False),
            opt_out=state.get("opt_out", False),
            db=db,
        )

        logger.info(
            "policy_check",
            extra={
                "kp_customer_id": customer_id,
                "kp_action_type": action_type,
                "kp_policy_status": decision.status,
                "kp_block_reason": decision.block_reason,
            },
        )

        return {"policy_decision": decision.as_dict()}

    return policy_check


# ─── execute_action ───────────────────────────────────────────────────────────

def make_execute_action(db: Optional[Session] = None):
    """Factory: injects the DB session into the execute_action node."""

    def execute_action(state: RecoveryReasoningState) -> dict:
        """
        Action Service - CLAUDE.md §15.

        Executes the approved idempotent action. Creates recovery case + action record.
        """
        from app.actions.service import ActionRequest, execute_action as _exec
        from app.policy.guard import PolicyDecision, PolicyStatus

        policy_dict = state.get("policy_decision") or {}
        action_type = policy_dict.get("action_type") or state.get("selected_action") or "silent_retry"
        amount_raw = policy_dict.get("amount") or state["subscription_context"].get("amount", 0)
        amount = Decimal(str(amount_raw))

        # Create or retrieve recovery case
        case_id = state.get("case_id")
        if case_id is None and db is not None:
            from app.db.models.recovery_case import RecoveryCase
            from datetime import datetime, timezone
            proposal = state.get("validated_proposal") or {}
            case = RecoveryCase(
                customer_id=state["customer_id"],
                risk_score=state["risk_score"],
                risk_level=state["risk_level"],
                diagnosis=proposal.get("cause"),
                diagnosis_confidence=proposal.get("confidence"),
                proposed_action=proposal.get("proposed_action"),
                selected_action=action_type,
                policy_status=policy_dict.get("status"),
                outcome_status="open",
            )
            db.add(case)
            db.flush()
            case_id = case.id
        elif case_id is None:
            case_id = 0  # no-db mode

        idempotency_key = f"rec_CASE_{case_id}"

        policy_decision = PolicyDecision(
            status=policy_dict.get("status", PolicyStatus.BLOCKED),
            checks=policy_dict.get("checks", {}),
            block_reason=policy_dict.get("block_reason"),
            action_type=action_type,
            customer_id=state["customer_id"],
            amount=amount,
            idempotency_key=idempotency_key,
        )

        request = ActionRequest(
            case_id=case_id,
            customer_id=state["customer_id"],
            action_type=action_type,
            amount=amount,
            currency=state["subscription_context"].get("currency", "INR"),
            idempotency_key=idempotency_key,
            policy_decision=policy_decision,
        )

        result = _exec(request, db=db)

        return {
            "case_id": case_id,
            "execution_result": {
                "action_id": result.action_id,
                "action_type": result.action_type,
                "status": result.status,
                "idempotency_key": result.idempotency_key,
                "message": result.message,
            },
        }

    return execute_action


# ─── record_outcome ───────────────────────────────────────────────────────────

def make_record_outcome(db: Optional[Session] = None):
    """Factory: injects the DB session into the record_outcome node."""

    def record_outcome(state: RecoveryReasoningState) -> dict:
        """
        Outcome Engine - records result, emits audit events, closes case.
        """
        from app.audit.service import log_audit_event
        from datetime import datetime, timezone

        case_id = state.get("case_id", 0)
        execution = state.get("execution_result") or {}
        policy = state.get("policy_decision") or {}
        proposal = state.get("validated_proposal") or {}
        action_type = execution.get("action_type", "unknown")
        idempotency_key = execution.get("idempotency_key", f"rec_CASE_{case_id}")

        # Audit: diagnosis_generated
        log_audit_event(
            event_type="diagnosis_generated",
            case_id=case_id,
            actor="langgraph:generate_diagnosis",
            payload={
                "cause": proposal.get("cause"),
                "confidence": proposal.get("confidence"),
                "proposed_action": proposal.get("proposed_action"),
                "rationale": proposal.get("rationale"),
                "used_fallback": state.get("used_fallback", False),
            },
            db=db,
        )

        # Audit: policy_check
        log_audit_event(
            event_type="policy_check",
            case_id=case_id,
            actor="langgraph:policy_check",
            payload={
                "status": policy.get("status"),
                "checks": policy.get("checks"),
                "block_reason": policy.get("block_reason"),
                "action_type": policy.get("action_type"),
            },
            idempotency_key=idempotency_key,
            db=db,
        )

        # Audit: action_executed (or blocked)
        exec_status = execution.get("status", "unknown")
        log_audit_event(
            event_type="action_executed",
            case_id=case_id,
            actor="langgraph:execute_action",
            payload=execution,
            idempotency_key=idempotency_key,
            db=db,
        )

        # Update recovery case status in DB
        if db is not None and case_id:
            from app.db.models.recovery_case import RecoveryCase
            case = db.get(RecoveryCase, case_id)
            if case is not None:
                case.outcome_status = "recovered" if exec_status == "executed" else exec_status
                case.closed_at = datetime.now(timezone.utc)

        # Audit: case_closed
        log_audit_event(
            event_type="case_closed",
            case_id=case_id,
            actor="langgraph:record_outcome",
            payload={
                "final_status": exec_status,
                "action_type": action_type,
                "risk_score": state["risk_score"],
            },
            db=db,
        )

        logger.info(
            "outcome_recorded",
            extra={
                "kp_customer_id": state["customer_id"],
                "kp_case_id": case_id,
                "kp_action_type": action_type,
                "kp_exec_status": exec_status,
            },
        )

        return {
            "recorded_outcome": {
                "case_id": case_id,
                "action_type": action_type,
                "status": exec_status,
                "policy_status": policy.get("status"),
                "cause": proposal.get("cause"),
            }
        }

    return record_outcome
