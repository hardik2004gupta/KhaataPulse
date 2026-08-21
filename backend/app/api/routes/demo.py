"""
Demo API — deterministic hero case and live simulation for frontend.

These endpoints work WITHOUT a database connection (no-db mode),
using the in-memory evaluation pipeline from Phase 4.

CLAUDE.md §26: Demo mode must work even if LLM/network/DB is unavailable.
All data originates from the real simulator + risk model + optimizer + policy guard.
No hardcoded business metrics.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.logging import get_logger
from app.evaluation.policies import KhaataPulsePolicy
from app.risk.model import TRAINING_REFERENCE_DATE, MODEL_VERSION, get_risk_predictor
from app.simulator.generator import generate_world
from app.simulator.world import WorldInternal

router = APIRouter(prefix="/demo", tags=["demo"])
logger = get_logger(__name__)

# Deterministic demo seed (CLAUDE.md §27: hero case must be reproducible)
_HERO_SEED = 42
_HERO_COHORT = 100


def _run_pipeline_for_customer(obs) -> dict[str, Any]:
    """Run full KhaataPulse pipeline for one observable customer. No DB required."""
    from app.agent.reasoning import StubReasoningModel, ReasoningContext
    from app.optimizer.ranker import rank_eligible_actions
    from app.policy.guard import policy_guard

    settings = get_settings()
    predictor = get_risk_predictor()

    # ── Risk Sieve ─────────────────────────────────────────────────────────────
    prediction = predictor.predict(obs, reference_date=TRAINING_REFERENCE_DATE)

    # ── Stub Diagnosis ─────────────────────────────────────────────────────────
    payment_failures = [
        {"status": p.status, "failure_code": p.failure_code, "payment_method": p.payment_method}
        for p in obs.payments if p.status == "failed"
    ]
    support_msgs = [
        ev.payload.get("message", "")
        for ev in obs.events if ev.event_type == "support_message"
    ]
    context = ReasoningContext(
        customer_id=obs.customer_id,
        risk_score=prediction.risk_score,
        risk_level=prediction.risk_level,
        risk_signals=[{"feature": s.feature, "impact": s.impact} for s in prediction.top_signals],
        subscription_info={
            "plan": obs.subscription.plan,
            "amount": float(obs.subscription.amount),
            "currency": obs.subscription.currency,
        },
        payment_failures=payment_failures,
        observable_events=[{"event_type": ev.event_type, **ev.payload} for ev in obs.events],
        support_messages=[m for m in support_msgs if m],
    )
    stub = StubReasoningModel()
    proposal = stub.reason(context)

    # ── Economic Optimizer ─────────────────────────────────────────────────────
    rankings = rank_eligible_actions(
        cause=proposal.cause,
        amount=obs.subscription.amount,
        ltv=obs.ltv,
    )

    # ── Policy Guard (no DB) ───────────────────────────────────────────────────
    selected_action = rankings[0].action_type if rankings else proposal.proposed_action
    decision = policy_guard(
        customer_id=obs.customer_id,
        action_type=selected_action,
        amount=obs.subscription.amount,
        idempotency_key=f"demo_{obs.customer_id}",
        dispute_hold=False,
        legal_hold=False,
        opt_out=False,
        db=None,
    )

    from app.policy.guard import PolicyStatus
    final_action = selected_action
    if decision.status == PolicyStatus.BLOCKED:
        final_action = "blocked"
    elif decision.status == PolicyStatus.ESCALATED:
        final_action = "human_escalation"

    return {
        "prediction": prediction,
        "proposal": proposal,
        "rankings": rankings,
        "decision": decision,
        "final_action": final_action,
    }


def _build_hero_case() -> dict[str, Any]:
    """
    Build the deterministic hero case.
    Uses seed=42, 100-customer cohort, picks the highest at-risk customer.
    No DB access.
    """
    settings = get_settings()
    from app.evaluation.evaluator import EvaluationWorld

    raw = generate_world(
        seed=_HERO_SEED,
        cohort_size=_HERO_COHORT,
        simulator_version=settings.simulator_version,
        reference_date=TRAINING_REFERENCE_DATE,
    )
    world = WorldInternal.from_raw_records(
        raw=raw,
        seed=_HERO_SEED,
        cohort_size=_HERO_COHORT,
        simulator_version=settings.simulator_version,
        reference_date=TRAINING_REFERENCE_DATE,
    )
    eval_world = EvaluationWorld(world=world)

    predictor = get_risk_predictor()

    # Score every customer, pick the highest-risk one above threshold
    best_rec = None
    best_score = -1.0
    best_obs = None
    for rec in eval_world.customer_records():
        obs = eval_world.extract_observable_for(rec)
        pred = predictor.predict(obs, reference_date=TRAINING_REFERENCE_DATE)
        if pred.risk_score > best_score:
            best_score = pred.risk_score
            best_rec = rec
            best_obs = obs

    if best_obs is None:
        raise RuntimeError("No customers generated in hero cohort")

    pipeline = _run_pipeline_for_customer(best_obs)
    pred = pipeline["prediction"]
    proposal = pipeline["proposal"]
    rankings = pipeline["rankings"]
    decision = pipeline["decision"]
    final_action = pipeline["final_action"]

    now = datetime.now(timezone.utc)

    # ── Build audit trail (in-memory, matches Phase 3 AuditEvent structure) ───
    audit_events = [
        {
            "event_type": "risk_detected",
            "actor": "risk_sieve",
            "timestamp": now.isoformat(),
            "payload": {
                "risk_score": round(pred.risk_score, 4),
                "risk_level": pred.risk_level,
                "model_version": pred.model_version,
                "top_signals": [{"feature": s.feature, "impact": round(s.impact, 4)} for s in pred.top_signals],
            },
        },
        {
            "event_type": "diagnosis_generated",
            "actor": "langgraph_agent",
            "timestamp": now.isoformat(),
            "payload": {
                "cause": proposal.cause,
                "confidence": round(proposal.confidence, 4),
                "proposed_action": proposal.proposed_action,
                "rationale": proposal.rationale,
                "risk_level": proposal.risk_level,
            },
        },
        {
            "event_type": "action_proposed",
            "actor": "optimizer",
            "timestamp": now.isoformat(),
            "payload": {
                "selected_action": rankings[0].action_type if rankings else proposal.proposed_action,
                "rankings": [
                    {
                        "action_type": r.action_type,
                        "enr": str(r.enr),
                        "estimated_p_payment": round(r.estimated_p_payment, 4),
                        "estimated_p_churn": round(r.estimated_p_churn, 4),
                        "action_cost": str(r.action_cost),
                    }
                    for r in rankings
                ],
            },
        },
        {
            "event_type": "policy_check",
            "actor": "policy_guard",
            "timestamp": now.isoformat(),
            "payload": decision.as_dict(),
        },
        {
            "event_type": "action_executed",
            "actor": "action_service",
            "timestamp": now.isoformat(),
            "payload": {
                "action_type": final_action,
                "idempotency_key": f"demo_{best_obs.customer_id}",
                "status": (
                    "blocked" if decision.status == "BLOCKED"
                    else "escalated" if decision.status == "ESCALATED"
                    else "executed"
                ),
            },
        },
    ]

    return {
        "customer": {
            "id": best_obs.customer_id,
            "name": best_obs.name,
            "segment": best_obs.segment,
            "ltv": str(best_obs.ltv),
        },
        "subscription": {
            "plan": best_obs.subscription.plan,
            "amount": str(best_obs.subscription.amount),
            "currency": best_obs.subscription.currency,
            "renewal_at": best_obs.subscription.renewal_at.isoformat(),
            "status": best_obs.subscription.status,
        },
        "payments": [
            {
                "status": p.status,
                "failure_code": p.failure_code,
                "payment_method": p.payment_method,
                "amount": str(p.amount),
                "created_at": p.created_at.isoformat() if hasattr(p.created_at, "isoformat") else str(p.created_at),
            }
            for p in best_obs.payments
        ],
        "observable_events": [
            {
                "event_type": ev.event_type,
                "timestamp": ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp),
                "payload": ev.payload,
            }
            for ev in best_obs.events
        ],
        "risk": {
            "risk_score": round(pred.risk_score, 4),
            "risk_level": pred.risk_level,
            "model_version": pred.model_version,
            "top_signals": [
                {"feature": s.feature, "impact": round(s.impact, 4)}
                for s in pred.top_signals
            ],
        },
        "diagnosis": {
            "cause": proposal.cause,
            "confidence": round(proposal.confidence, 4),
            "rationale": proposal.rationale,
            "proposed_action": proposal.proposed_action,
            "risk_level": proposal.risk_level,
        },
        "action_rankings": [
            {
                "rank": i + 1,
                "action_type": r.action_type,
                "enr": str(r.enr),
                "estimated_p_payment": round(r.estimated_p_payment, 4),
                "estimated_p_churn": round(r.estimated_p_churn, 4),
                "action_cost": str(r.action_cost),
            }
            for i, r in enumerate(rankings)
        ],
        "policy_decision": {
            "status": decision.status,
            "action_type": decision.action_type,
            "checks": decision.checks,
            "block_reason": decision.block_reason,
        },
        "execution": {
            "action_type": final_action,
            "status": (
                "blocked" if decision.status == "BLOCKED"
                else "escalated" if decision.status == "ESCALATED"
                else "executed"
            ),
            "idempotency_key": f"demo_{best_obs.customer_id}",
        },
        "audit_events": audit_events,
    }


@router.get("/hero")
def get_hero_case():
    """
    GET /demo/hero

    Returns the deterministic hero case for demo mode.
    Uses seed=42 world, picks the highest-risk customer.
    No DB access. All data from real simulator + risk model + optimizer.
    """
    logger.info("demo_hero_case_requested")
    return _build_hero_case()


@router.post("/simulate")
def simulate_pipeline():
    """
    POST /demo/simulate

    Runs the full KhaataPulse pipeline for the hero customer and returns
    a sequence of pipeline steps for the live event stream visualization.

    No DB access. Uses real pipeline components.
    """
    logger.info("demo_simulate_requested")
    hero = _build_hero_case()
    now = datetime.now(timezone.utc)

    steps = [
        {
            "step": "payment_failed",
            "label": "Payment Failed",
            "description": f"Renewal payment declined — {hero['payments'][-1]['failure_code'] or 'bank_declined'}",
            "actor": "payment_gateway",
            "data": {
                "amount": hero["subscription"]["amount"],
                "currency": hero["subscription"]["currency"],
                "failure_code": hero["payments"][-1]["failure_code"] if hero["payments"] else "bank_declined",
                "payment_method": hero["payments"][-1]["payment_method"] if hero["payments"] else "card",
            },
        },
        {
            "step": "risk_detected",
            "label": "Risk Detected",
            "description": f"Risk score: {int(hero['risk']['risk_score'] * 100)}% — routed to KhaataPulse",
            "actor": "risk_sieve",
            "data": hero["risk"],
        },
        {
            "step": "diagnosis_generated",
            "label": "AI Diagnosis",
            "description": f"Cause: {hero['diagnosis']['cause'].replace('_', ' ').title()} — {int(hero['diagnosis']['confidence'] * 100)}% confidence",
            "actor": "langgraph_agent",
            "data": hero["diagnosis"],
        },
        {
            "step": "action_ranked",
            "label": "Action Ranked",
            "description": f"Selected: {hero['action_rankings'][0]['action_type'].replace('_', ' ').title() if hero['action_rankings'] else 'suppress'}",
            "actor": "economic_optimizer",
            "data": {"rankings": hero["action_rankings"]},
        },
        {
            "step": "policy_check",
            "label": "Policy Check",
            "description": f"Policy Guard: {hero['policy_decision']['status']}",
            "actor": "policy_guard",
            "data": hero["policy_decision"],
        },
        {
            "step": "action_executed",
            "label": "Action Executed" if hero["execution"]["status"] == "executed" else "Action " + hero["execution"]["status"].title(),
            "description": f"Simulated gateway: {hero['execution']['action_type'].replace('_', ' ').title()} — {hero['execution']['status']}",
            "actor": "action_service",
            "data": hero["execution"],
        },
    ]

    return {
        "customer": hero["customer"],
        "subscription": hero["subscription"],
        "steps": steps,
    }
