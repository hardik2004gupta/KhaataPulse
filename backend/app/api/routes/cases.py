"""
Recovery Cases API — list and detail views for the risk queue.

CLAUDE.md §30: Customer, Risk, Cause, Action, Policy, Status.
Observable data only — no hidden simulator state.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.recovery_case import RecoveryCase
from app.db.models.audit_event import AuditEvent
from app.db.models.customer import Customer
from app.db.models.subscription import Subscription
from app.core.logging import get_logger

router = APIRouter(prefix="/cases", tags=["cases"])
logger = get_logger(__name__)


@router.get("/")
def list_cases(
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    GET /cases/

    List recovery cases for the risk queue.
    Returns observable data only — no hidden simulator state.
    """
    cases = (
        db.query(RecoveryCase)
        .order_by(RecoveryCase.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []
    for case in cases:
        customer = db.query(Customer).filter(Customer.id == case.customer_id).first()
        subscription = db.query(Subscription).filter(
            Subscription.customer_id == case.customer_id
        ).first()

        result.append({
            "id": case.id,
            "customer_id": case.customer_id,
            "customer_name": customer.name if customer else None,
            "customer_segment": customer.segment if customer else None,
            "subscription_plan": subscription.plan if subscription else None,
            "subscription_amount": str(subscription.amount) if subscription else None,
            "currency": subscription.currency if subscription else "INR",
            "risk_score": float(case.risk_score),
            "risk_level": case.risk_level,
            "diagnosis": case.diagnosis,
            "diagnosis_confidence": float(case.diagnosis_confidence) if case.diagnosis_confidence else None,
            "proposed_action": case.proposed_action,
            "selected_action": case.selected_action,
            "policy_status": case.policy_status,
            "outcome_status": case.outcome_status,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        })

    return {"cases": result, "total": len(result), "limit": limit, "offset": offset}


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    """
    GET /cases/{case_id}

    Get full case detail including audit events.
    Observable data only.
    """
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    customer = db.query(Customer).filter(Customer.id == case.customer_id).first()
    subscription = db.query(Subscription).filter(
        Subscription.customer_id == case.customer_id
    ).first()

    audit_events = (
        db.query(AuditEvent)
        .filter(AuditEvent.case_id == case_id)
        .order_by(AuditEvent.timestamp)
        .all()
    )

    return {
        "id": case.id,
        "customer_id": case.customer_id,
        "customer_name": customer.name if customer else None,
        "customer_segment": customer.segment if customer else None,
        "customer_ltv": str(customer.ltv) if customer else None,
        "subscription_plan": subscription.plan if subscription else None,
        "subscription_amount": str(subscription.amount) if subscription else None,
        "currency": subscription.currency if subscription else "INR",
        "risk_score": float(case.risk_score),
        "risk_level": case.risk_level,
        "diagnosis": case.diagnosis,
        "diagnosis_confidence": float(case.diagnosis_confidence) if case.diagnosis_confidence else None,
        "proposed_action": case.proposed_action,
        "selected_action": case.selected_action,
        "policy_status": case.policy_status,
        "outcome_status": case.outcome_status,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        "audit_events": [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "actor": ev.actor,
                "payload": ev.payload,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "idempotency_key": ev.idempotency_key,
            }
            for ev in audit_events
        ],
    }
