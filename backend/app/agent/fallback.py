"""
LLM Fallback Policy - CLAUDE.md §12.

When the LLM fails (timeout, provider error, schema validation failure,
malformed JSON, invalid enum, missing field), the recovery pipeline must
continue with a deterministic smart-retry baseline. It must never crash.

Every fallback is logged as an llm_fallback audit event.
"""
from __future__ import annotations

import logging

from app.agent.reasoning import ReasoningContext
from app.agent.schemas import RecoveryProposal
from app.core.logging import get_logger

logger = get_logger(__name__)


def smart_retry_proposal(
    context: ReasoningContext,
    failure_reason: str,
) -> RecoveryProposal:
    """
    Deterministic fallback based on observable signals only.

    Rule hierarchy (priority order):
      1. payment_method_changed → card_expired → smart_link
      2. risk_score >= 0.70    → temporary_cash_flow → human_escalation
      3. support message exists → temporary_cash_flow → grace_period
      4. default              → temporary_cash_flow → silent_retry

    The fallback does NOT require an external API call.
    """
    # Log required by CLAUDE.md §12
    logger.warning(
        "llm_fallback",
        extra={
            "kp_event": "llm_fallback",
            "kp_reason": failure_reason,
            "kp_fallback_policy": "smart_retry",
            "kp_customer_id": context.customer_id,
        },
    )

    event_types = {e.get("event_type", "") for e in context.observable_events}

    if "payment_method_changed" in event_types:
        cause = "card_expired"
        action = "smart_link"
        rationale = (
            f"[smart_retry fallback - LLM unavailable: {failure_reason}] "
            "Payment method change observed. Sending smart payment link."
        )
    elif context.risk_score >= 0.70:
        cause = "temporary_cash_flow"
        action = "human_escalation"
        rationale = (
            f"[smart_retry fallback - LLM unavailable: {failure_reason}] "
            "High risk score. Escalating to human agent."
        )
    elif "support_message" in event_types:
        cause = "temporary_cash_flow"
        action = "grace_period"
        rationale = (
            f"[smart_retry fallback - LLM unavailable: {failure_reason}] "
            "Support contact detected. Offering grace period."
        )
    else:
        cause = "temporary_cash_flow"
        action = "silent_retry"
        rationale = (
            f"[smart_retry fallback - LLM unavailable: {failure_reason}] "
            "Transient payment difficulty assumed. Initiating silent retry."
        )

    risk_level = (
        context.risk_level
        if context.risk_level in ("LOW", "MEDIUM", "HIGH")
        else "MEDIUM"
    )

    return RecoveryProposal(
        cause=cause,
        confidence=0.60,
        proposed_action=action,
        rationale=rationale,
        risk_level=risk_level,
    )
