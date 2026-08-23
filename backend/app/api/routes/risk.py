"""
Risk API - CLAUDE.md §30, §8.

POST /risk/predict   - score one customer (risk sieve only)
POST /risk/reason    - risk sieve + LangGraph reasoning (at-risk cases only)

Observable data only is returned. Hidden simulator state never crosses the API.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.db.models.customer import Customer
from app.db.models.event import Event
from app.db.models.payment import Payment
from app.db.models.subscription import Subscription
from app.risk.model import get_risk_predictor
from app.risk.service import RoutingDecision, RiskService
from app.simulator.world import (
    ObservableCustomerData,
    ObservableEvent,
    ObservablePayment,
    ObservableSubscription,
)

router = APIRouter(prefix="/risk", tags=["risk"])
logger = get_logger(__name__)


# ── Request / response schemas ────────────────────────────────────────────────

class PredictRequest(BaseModel):
    customer_id: int


class SignalOut(BaseModel):
    feature: str
    impact: float


class PredictResponse(BaseModel):
    customer_id: int
    risk_score: float
    risk_level: str
    top_signals: list[SignalOut]
    model_version: str
    routing_decision: str


class ReasonResponse(BaseModel):
    customer_id: int
    risk_score: float
    risk_level: str
    top_signals: list[SignalOut]
    model_version: str
    routing_decision: str
    # LangGraph output
    context_classification: str | None
    cause: str | None
    confidence: float | None
    proposed_action: str | None
    rationale: str | None
    used_fallback: bool


# ── DB → observable conversion (no hidden state) ─────────────────────────────

def _load_observable(customer_id: int, db: Session) -> ObservableCustomerData:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    subscription = (
        db.query(Subscription).filter(Subscription.customer_id == customer_id).first()
    )
    if subscription is None:
        raise HTTPException(status_code=404, detail=f"No subscription for customer {customer_id}")

    payments_orm = (
        db.query(Payment).filter(Payment.customer_id == customer_id).all()
    )
    events_orm = (
        db.query(Event)
        .filter(Event.customer_id == customer_id)
        .order_by(Event.timestamp)
        .all()
    )

    obs_sub = ObservableSubscription(
        plan=subscription.plan,
        amount=subscription.amount,
        currency=subscription.currency,
        renewal_at=subscription.renewal_at,
        status=subscription.status,
    )
    obs_payments = [
        ObservablePayment(
            amount=p.amount,
            status=p.status,
            failure_code=p.failure_code,
            payment_method=p.payment_method,
            created_at=p.created_at,
        )
        for p in payments_orm
    ]
    obs_events = [
        ObservableEvent(
            event_type=e.event_type,
            timestamp=e.timestamp,
            payload=e.payload,
        )
        for e in events_orm
    ]

    return ObservableCustomerData(
        customer_id=customer.id,
        name=customer.name,
        segment=customer.segment,
        ltv=customer.ltv,
        subscription=obs_sub,
        payments=obs_payments,
        events=obs_events,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/predict", response_model=PredictResponse)
def predict_risk(req: PredictRequest, db: Session = Depends(get_db)) -> PredictResponse:
    """
    Score a customer's payment failure risk.
    Returns the risk prediction and routing decision.
    """
    obs = _load_observable(req.customer_id, db)
    service = RiskService()
    assessment = service.assess(obs, reference_date=datetime.now(timezone.utc))
    pred = assessment.prediction

    logger.info(
        "risk_detected",
        extra={
            "kp_customer_id": req.customer_id,
            "kp_risk_score": pred.risk_score,
            "kp_risk_level": pred.risk_level,
            "kp_routing": assessment.routing.value,
        },
    )

    return PredictResponse(
        customer_id=req.customer_id,
        risk_score=round(pred.risk_score, 4),
        risk_level=pred.risk_level,
        top_signals=[SignalOut(feature=s.feature, impact=round(s.impact, 4)) for s in pred.top_signals],
        model_version=pred.model_version,
        routing_decision=assessment.routing.value,
    )


@router.post("/reason", response_model=ReasonResponse)
def reason(req: PredictRequest, db: Session = Depends(get_db)) -> ReasonResponse:
    """
    Risk sieve + LangGraph reasoning for at-risk cases.
    Low-risk customers are returned without invoking LangGraph.
    """
    from app.agent.graph import build_recovery_graph, make_initial_state
    from app.agent.reasoning import get_reasoning_model

    obs = _load_observable(req.customer_id, db)
    service = RiskService()
    assessment = service.assess(obs, reference_date=datetime.now(timezone.utc))
    pred = assessment.prediction

    base = ReasonResponse(
        customer_id=req.customer_id,
        risk_score=round(pred.risk_score, 4),
        risk_level=pred.risk_level,
        top_signals=[SignalOut(feature=s.feature, impact=round(s.impact, 4)) for s in pred.top_signals],
        model_version=pred.model_version,
        routing_decision=assessment.routing.value,
        context_classification=None,
        cause=None,
        confidence=None,
        proposed_action=None,
        rationale=None,
        used_fallback=False,
    )

    # Only invoke LangGraph for at-risk cases (CLAUDE.md §8)
    if assessment.routing != RoutingDecision.LANGGRAPH:
        return base

    # Build observable state - no hidden fields
    support_lines = [
        e.payload.get("message", "")
        for e in obs.events
        if e.event_type == "support_message" and e.payload.get("message")
    ]

    initial_state = make_initial_state(
        customer_id=obs.customer_id,
        risk_score=pred.risk_score,
        risk_level=pred.risk_level,
        risk_signals=[{"feature": s.feature, "impact": s.impact} for s in pred.top_signals],
        subscription_context={
            "plan": obs.subscription.plan,
            "amount": float(obs.subscription.amount),
            "currency": obs.subscription.currency,
            "renewal_at": obs.subscription.renewal_at.isoformat(),
            "status": obs.subscription.status,
        },
        payment_context=[
            {
                "status": p.status,
                "failure_code": p.failure_code,
                "payment_method": p.payment_method,
                "amount": float(p.amount),
            }
            for p in obs.payments
        ],
        observable_events=[
            {"event_type": e.event_type, **e.payload}
            for e in obs.events
        ],
        support_context="\n---\n".join(support_lines),
    )

    graph = build_recovery_graph(reasoning_model=get_reasoning_model())
    final_state = graph.invoke(initial_state)

    vp = final_state.get("validated_proposal") or {}
    return ReasonResponse(
        **{k: v for k, v in base.model_dump().items() if k not in ("context_classification", "cause", "confidence", "proposed_action", "rationale", "used_fallback")},
        context_classification=final_state.get("context_classification"),
        cause=vp.get("cause"),
        confidence=vp.get("confidence"),
        proposed_action=vp.get("proposed_action"),
        rationale=vp.get("rationale"),
        used_fallback=final_state.get("used_fallback", False),
    )
