"""
Audit Service — CLAUDE.md §16.

Produces immutable AuditEvent records. Append-only.
The audit drawer must show events in chronological order with expandable payloads.

Required event types: risk_detected | diagnosis_generated | action_proposed |
                      policy_check | action_executed | payment_received |
                      case_closed | llm_fallback
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


def log_audit_event(
    *,
    event_type: str,
    case_id: int,
    actor: str,
    payload: dict,
    idempotency_key: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[int]:
    """
    Append an immutable audit event. Returns the event id (or None in no-db mode).

    Args:
        event_type:      One of the required event types (CLAUDE.md §16).
        case_id:         recovery_cases.id this event belongs to.
        actor:           Module that produced the event (e.g. "risk_model", "policy_guard").
        payload:         Structured JSON payload for reconstruction.
        idempotency_key: Optional — action idempotency key if event is tied to an action.
        db:              DB session. If None, event is logged only (no DB persistence).
    """
    logger.info(
        "audit_event",
        extra={
            "kp_event_type": event_type,
            "kp_case_id": case_id,
            "kp_actor": actor,
            "kp_idempotency_key": idempotency_key,
        },
    )

    if db is None:
        return None

    from app.db.models.audit_event import AuditEvent
    event = AuditEvent(
        case_id=case_id,
        event_type=event_type,
        actor=actor,
        payload=payload,
        idempotency_key=idempotency_key,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    return event.id
