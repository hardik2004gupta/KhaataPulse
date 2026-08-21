"""
Action Service — CLAUDE.md §15.

Executes typed, idempotent simulated gateway actions.
All actions are simulated (no real payment processing in MVP).

Required fields per action: action_id, case_id, customer_id, action_type,
amount, currency, idempotency_key, timestamp, policy_result.

The service rejects duplicate execution (same idempotency key).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.policy.guard import PolicyDecision, PolicyStatus

logger = get_logger(__name__)


@dataclass
class ActionRequest:
    """Typed action contract — CLAUDE.md §15."""
    case_id: int
    customer_id: int
    action_type: str          # silent_retry | smart_link | grace_period | human_escalation | suppress
    amount: Decimal
    currency: str
    idempotency_key: str
    policy_decision: PolicyDecision


@dataclass
class ActionResult:
    action_id: Optional[int]
    action_type: str
    status: str               # executed | blocked | escalated | skipped | duplicate
    idempotency_key: str
    message: str


def execute_action(request: ActionRequest, db: Optional[Session] = None) -> ActionResult:
    """
    Execute an approved action or record a blocked/escalated outcome.

    Idempotency: if the same idempotency_key was already executed, return the
    existing record without side effects (CLAUDE.md §22).
    """
    if request.policy_decision.status not in (PolicyStatus.APPROVED, PolicyStatus.ESCALATED):
        logger.info(
            "action_blocked",
            extra={
                "kp_action_type": request.action_type,
                "kp_idempotency_key": request.idempotency_key,
                "kp_block_reason": request.policy_decision.block_reason,
            },
        )
        return ActionResult(
            action_id=None,
            action_type=request.action_type,
            status="blocked",
            idempotency_key=request.idempotency_key,
            message=f"blocked:{request.policy_decision.block_reason}",
        )

    if db is not None:
        from app.db.models.action import RecoveryAction
        existing = db.query(RecoveryAction).filter_by(
            idempotency_key=request.idempotency_key
        ).first()
        if existing is not None:
            return ActionResult(
                action_id=existing.id,
                action_type=existing.action_type,
                status="duplicate",
                idempotency_key=request.idempotency_key,
                message="idempotent_replay",
            )

        action = RecoveryAction(
            case_id=request.case_id,
            customer_id=request.customer_id,
            action_type=request.action_type,
            amount=request.amount,
            currency=request.currency,
            idempotency_key=request.idempotency_key,
            policy_result=request.policy_decision.as_dict(),
        )
        db.add(action)
        db.flush()
        action_id = action.id
    else:
        action_id = None

    status = (
        "escalated"
        if request.policy_decision.status == PolicyStatus.ESCALATED
        else "executed"
    )

    logger.info(
        "action_executed",
        extra={
            "kp_action_type": request.action_type,
            "kp_status": status,
            "kp_idempotency_key": request.idempotency_key,
            "kp_amount": str(request.amount),
        },
    )

    return ActionResult(
        action_id=action_id,
        action_type=request.action_type,
        status=status,
        idempotency_key=request.idempotency_key,
        message=f"simulated_{request.action_type}",
    )
