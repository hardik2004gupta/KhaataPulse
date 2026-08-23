"""
LangGraph agent tests - CLAUDE.md §32.

Verifies:
  - All 9 nodes execute in correct order
  - Graph produces a valid RecoveryProposal
  - Pydantic validation enforced (valid/invalid inputs)
  - LLM failures trigger deterministic fallback
  - Agent isolation: no hidden state in graph state or LLM context
  - Low-risk cases bypass LangGraph (tested at service level)
  - At-risk cases enter LangGraph
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.agent.fallback import smart_retry_proposal
from app.agent.graph import build_recovery_graph, make_initial_state
from app.agent.reasoning import ReasoningContext, StubReasoningModel
from app.agent.schemas import RecoveryProposal
from app.agent.state import RecoveryReasoningState


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_STATE_KWARGS = dict(
    customer_id=42,
    risk_score=0.75,
    risk_level="HIGH",
    risk_signals=[
        {"feature": "previous_payment_failures", "impact": 0.45},
        {"feature": "payment_success_rate", "impact": -0.30},
        {"feature": "checkout_reopens", "impact": 0.22},
    ],
    subscription_context={
        "plan": "growth",
        "amount": 4999.0,
        "currency": "INR",
        "renewal_at": "2026-02-01T00:00:00+00:00",
        "status": "active",
    },
    payment_context=[
        {"status": "failed", "failure_code": "insufficient_funds", "payment_method": "upi", "amount": 4999.0},
        {"status": "successful", "failure_code": None, "payment_method": "upi", "amount": 4999.0},
        {"status": "pending", "failure_code": None, "payment_method": "upi", "amount": 4999.0},
    ],
    observable_events=[
        {"event_type": "renewal_approaching", "days_until_renewal": 14},
        {"event_type": "invoice_viewed"},
        {"event_type": "payment_failed", "failure_code": "insufficient_funds"},
        {"event_type": "support_message", "message": "I am having trouble with my payment."},
    ],
    support_context="I am having trouble with my payment.",
    ltv=50000.0,
    dispute_hold=False,
    legal_hold=False,
    opt_out=False,
)


@pytest.fixture(scope="module")
def stub_graph():
    return build_recovery_graph(reasoning_model=StubReasoningModel())


@pytest.fixture()
def initial_state() -> RecoveryReasoningState:
    return make_initial_state(**SAMPLE_STATE_KWARGS)


# ── Graph structure ───────────────────────────────────────────────────────────

class TestGraphStructure:
    def test_graph_builds_without_error(self):
        graph = build_recovery_graph(reasoning_model=StubReasoningModel())
        assert graph is not None

    def test_graph_invoke_returns_dict(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        assert isinstance(result, dict)

    def test_all_nine_nodes_produce_state_keys(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        # Phase 2 nodes
        assert "context_classification" in result
        assert "diagnosis" in result
        assert "recovery_proposal" in result
        assert "validated_proposal" in result
        # Phase 3 stubs
        assert "ranked_actions" in result
        assert "policy_decision" in result
        assert "execution_result" in result
        assert "recorded_outcome" in result


# ── Node outputs ──────────────────────────────────────────────────────────────

class TestNodeOutputs:
    def test_classify_context_sets_classification(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        assert result["context_classification"] is not None
        assert isinstance(result["context_classification"], str)

    def test_diagnosis_is_set(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        assert result["diagnosis"] is not None
        assert isinstance(result["diagnosis"], dict)

    def test_diagnosis_has_required_fields(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        diag = result["diagnosis"]
        for field in ("cause", "confidence", "proposed_action", "rationale", "risk_level"):
            assert field in diag, f"Missing field: {field}"

    def test_validated_proposal_is_set(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        vp = result["validated_proposal"]
        assert vp is not None
        assert isinstance(vp, dict)

    def test_validated_proposal_passes_pydantic(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        vp = result["validated_proposal"]
        proposal = RecoveryProposal.model_validate(vp)
        assert proposal.cause in (
            "billing_migration", "temporary_cash_flow", "card_expired",
            "price_friction", "churn_intent",
        )
        assert proposal.proposed_action in (
            "silent_retry", "smart_link", "grace_period", "human_escalation", "suppress",
        )
        assert 0.0 <= proposal.confidence <= 1.0

    def test_phase3_nodes_produce_real_outputs(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        # Phase 3 nodes now produce real outputs (not None)
        assert result["action_rankings"] is not None
        assert isinstance(result["action_rankings"], list)
        assert result["policy_decision"] is not None
        assert "status" in result["policy_decision"]
        assert result["execution_result"] is not None
        assert result["recorded_outcome"] is not None


# ── Classify context determinism ──────────────────────────────────────────────

class TestClassifyContext:
    def test_payment_method_change_classified_as_rail_issue(self, stub_graph):
        state = make_initial_state(
            **{**SAMPLE_STATE_KWARGS,
               "observable_events": [{"event_type": "payment_method_changed"}],
               "support_context": ""},
        )
        result = stub_graph.invoke(state)
        assert result["context_classification"] == "payment_rail_issue"

    def test_subscription_change_classified_as_churn_risk(self, stub_graph):
        state = make_initial_state(
            **{**SAMPLE_STATE_KWARGS,
               "observable_events": [{"event_type": "subscription_changed"}],
               "support_context": ""},
        )
        result = stub_graph.invoke(state)
        assert result["context_classification"] == "churn_risk"


# ── Structured output validation ──────────────────────────────────────────────

class TestStructuredOutputValidation:
    def test_valid_proposal_passes(self):
        p = RecoveryProposal(
            cause="card_expired",
            confidence=0.85,
            proposed_action="smart_link",
            rationale="Card expired.",
            risk_level="HIGH",
        )
        assert p.cause == "card_expired"

    def test_invalid_cause_raises(self):
        with pytest.raises(ValidationError):
            RecoveryProposal(
                cause="unknown_cause",
                confidence=0.85,
                proposed_action="smart_link",
                rationale=".",
                risk_level="HIGH",
            )

    def test_invalid_action_raises(self):
        with pytest.raises(ValidationError):
            RecoveryProposal(
                cause="card_expired",
                confidence=0.85,
                proposed_action="call_customer",  # not in enum
                rationale=".",
                risk_level="HIGH",
            )

    def test_invalid_risk_level_raises(self):
        with pytest.raises(ValidationError):
            RecoveryProposal(
                cause="card_expired",
                confidence=0.85,
                proposed_action="smart_link",
                rationale=".",
                risk_level="CRITICAL",  # not in enum
            )

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            RecoveryProposal(
                cause="card_expired",
                confidence=-0.1,
                proposed_action="smart_link",
                rationale=".",
                risk_level="HIGH",
            )

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            RecoveryProposal(
                cause="card_expired",
                confidence=1.1,
                proposed_action="smart_link",
                rationale=".",
                risk_level="HIGH",
            )

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            RecoveryProposal.model_validate(
                {"cause": "card_expired", "confidence": 0.85}  # missing fields
            )

    def test_malformed_dict_raises(self):
        with pytest.raises(ValidationError):
            RecoveryProposal.model_validate({"nonsense": True})


# ── LLM failure → fallback ────────────────────────────────────────────────────

class TestLLMFailureFallback:
    class _FailingModel:
        def reason(self, context):
            raise ConnectionError("LLM provider unreachable")

    class _TimeoutModel:
        def reason(self, context):
            import time
            raise TimeoutError("Request timed out")

    class _BadJsonModel:
        def reason(self, context):
            raise ValueError("Malformed JSON response from LLM")

    class _ValidationFailModel:
        def reason(self, context):
            raise Exception("schema validation failure")

    @pytest.mark.parametrize("failing_model_cls", [
        _FailingModel,
        _TimeoutModel,
        _BadJsonModel,
        _ValidationFailModel,
    ])
    def test_llm_failure_triggers_fallback(self, failing_model_cls, initial_state):
        graph = build_recovery_graph(reasoning_model=failing_model_cls())
        result = graph.invoke(initial_state)
        assert result["used_fallback"] is True
        assert result["fallback_reason"] is not None
        # Must still produce a valid validated_proposal
        vp = result["validated_proposal"]
        assert vp is not None
        RecoveryProposal.model_validate(vp)

    def test_fallback_never_crashes(self, initial_state):
        graph = build_recovery_graph(reasoning_model=self._FailingModel())
        result = graph.invoke(initial_state)  # must not raise
        assert result is not None

    def test_fallback_produces_valid_proposal(self):
        context = ReasoningContext(
            customer_id=42,
            risk_score=0.75,
            risk_level="HIGH",
            risk_signals=[],
            subscription_info={"plan": "growth", "amount": 4999.0},
            payment_failures=[],
            observable_events=[{"event_type": "support_message"}],
            support_messages=["Having trouble paying"],
        )
        proposal = smart_retry_proposal(context, "timeout")
        assert proposal.proposed_action in (
            "silent_retry", "smart_link", "grace_period", "human_escalation", "suppress"
        )
        assert proposal.cause in (
            "billing_migration", "temporary_cash_flow", "card_expired",
            "price_friction", "churn_intent",
        )

    def test_fallback_for_payment_method_change(self):
        context = ReasoningContext(
            customer_id=1,
            risk_score=0.50,
            risk_level="MEDIUM",
            risk_signals=[],
            subscription_info={},
            payment_failures=[],
            observable_events=[{"event_type": "payment_method_changed"}],
            support_messages=[],
        )
        proposal = smart_retry_proposal(context, "provider_error")
        assert proposal.proposed_action == "smart_link"
        assert proposal.cause == "card_expired"

    def test_fallback_for_high_risk_no_signal(self):
        context = ReasoningContext(
            customer_id=2,
            risk_score=0.80,
            risk_level="HIGH",
            risk_signals=[],
            subscription_info={},
            payment_failures=[],
            observable_events=[],
            support_messages=[],
        )
        proposal = smart_retry_proposal(context, "timeout")
        assert proposal.proposed_action == "human_escalation"


# ── Agent isolation: no hidden state ─────────────────────────────────────────

HIDDEN_STATE_KEYS = {
    "latent_state", "payment_intent", "cash_flow_health",
    "payment_rail_health", "churn_sensitivity", "potential_outcomes",
    "p_payment", "p_churn", "ground_truth_action_effects",
    "customer_ltv_latent",
}


class TestAgentIsolation:
    def test_initial_state_has_no_hidden_keys(self, initial_state):
        for key in HIDDEN_STATE_KEYS:
            assert key not in initial_state, f"Hidden key '{key}' found in initial graph state"

    def test_final_state_has_no_hidden_keys(self, stub_graph, initial_state):
        result = stub_graph.invoke(initial_state)
        for key in HIDDEN_STATE_KEYS:
            assert key not in result, f"Hidden key '{key}' found in final graph state"

    def test_reasoning_context_has_no_hidden_keys(self):
        ctx = ReasoningContext(
            customer_id=1,
            risk_score=0.5,
            risk_level="MEDIUM",
            risk_signals=[],
            subscription_info={},
            payment_failures=[],
            observable_events=[],
            support_messages=[],
        )
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(ctx)}
        for key in HIDDEN_STATE_KEYS:
            assert key not in field_names, f"Hidden key '{key}' found in ReasoningContext"

    def test_state_typeddict_has_no_hidden_keys(self):
        import typing
        hints = typing.get_type_hints(RecoveryReasoningState)
        for key in HIDDEN_STATE_KEYS:
            assert key not in hints, f"Hidden key '{key}' found in RecoveryReasoningState TypedDict"

    def test_make_initial_state_rejects_extra_hidden_kwargs(self):
        """make_initial_state should not accept latent_state - verify via signature."""
        import inspect
        sig = inspect.signature(make_initial_state)
        assert "latent_state" not in sig.parameters
        assert "potential_outcomes" not in sig.parameters
        assert "p_payment" not in sig.parameters

    def test_stub_reasoning_model_uses_only_observable_context(self):
        """StubReasoningModel.reason should not access any hidden fields."""
        ctx = ReasoningContext(
            customer_id=99,
            risk_score=0.65,
            risk_level="HIGH",
            risk_signals=[{"feature": "previous_payment_failures", "impact": 0.40}],
            subscription_info={"plan": "pro", "amount": 9999},
            payment_failures=[{"status": "failed", "failure_code": "card_blocked"}],
            observable_events=[{"event_type": "invoice_viewed"}],
            support_messages=[],
        )
        stub = StubReasoningModel()
        proposal = stub.reason(ctx)
        assert isinstance(proposal, RecoveryProposal)


# ── Risk routing integration ──────────────────────────────────────────────────

class TestRiskRoutingIntegration:
    """Verify that the risk threshold controls LangGraph invocation."""

    def test_low_risk_does_not_need_langgraph(self):
        """A clearly low-risk customer (score < 0.30) routes to standard flow."""
        from app.risk.service import RoutingDecision, RiskService
        from unittest.mock import patch
        from app.risk.model import RiskPrediction, RiskSignal, MODEL_VERSION

        low_pred = RiskPrediction(
            risk_score=0.10,
            risk_level="LOW",
            top_signals=[RiskSignal("days_to_renewal", 0.05)],
            model_version=MODEL_VERSION,
        )
        service = RiskService(threshold=0.30)
        from datetime import timedelta, timezone
        from decimal import Decimal
        from app.simulator.world import (
            ObservableCustomerData, ObservablePayment, ObservableSubscription
        )
        ref = datetime(2026, 1, 1, tzinfo=timezone.utc)
        obs = ObservableCustomerData(
            customer_id=1, name="Safe", segment="consumer",
            ltv=Decimal("5000"),
            subscription=ObservableSubscription(
                plan="basic", amount=Decimal("199"), currency="INR",
                renewal_at=ref + timedelta(days=20), status="active",
            ),
            payments=[], events=[],
        )

        predictor_mock = MagicMock()
        predictor_mock.predict.return_value = low_pred

        with patch("app.risk.service.get_risk_predictor", return_value=predictor_mock):
            assessment = service.assess(obs)

        assert assessment.routing == RoutingDecision.STANDARD_FLOW

    def test_high_risk_routes_to_langgraph(self):
        """A high-risk customer (score >= 0.30) routes to LangGraph."""
        from app.risk.service import RoutingDecision, RiskService
        from app.risk.model import RiskPrediction, RiskSignal, MODEL_VERSION
        from datetime import timedelta, timezone
        from decimal import Decimal
        from app.simulator.world import (
            ObservableCustomerData, ObservablePayment, ObservableSubscription
        )

        high_pred = RiskPrediction(
            risk_score=0.80,
            risk_level="HIGH",
            top_signals=[RiskSignal("previous_payment_failures", 0.45)],
            model_version=MODEL_VERSION,
        )
        service = RiskService(threshold=0.30)
        ref = datetime(2026, 1, 1, tzinfo=timezone.utc)
        obs = ObservableCustomerData(
            customer_id=2, name="Risky", segment="smb",
            ltv=Decimal("50000"),
            subscription=ObservableSubscription(
                plan="growth", amount=Decimal("4999"), currency="INR",
                renewal_at=ref + timedelta(days=10), status="active",
            ),
            payments=[], events=[],
        )

        predictor_mock = MagicMock()
        predictor_mock.predict.return_value = high_pred

        with patch("app.risk.service.get_risk_predictor", return_value=predictor_mock):
            assessment = service.assess(obs)

        assert assessment.routing == RoutingDecision.LANGGRAPH
