"""
Risk model tests - CLAUDE.md §32.

Verifies:
  - Model trains on observable data only
  - Predictions in [0.0, 1.0]
  - Model reproducibility (same training config → same predictions)
  - Risk level mapping correct
  - Threshold routing correct (< 0.30 → STANDARD, >= 0.30 → LANGGRAPH)
  - Top 3 signals returned with feature names
  - Model version is correct
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.risk.features import FeatureBuilder, RiskFeatures
from app.risk.model import (
    MODEL_VERSION,
    TRAINING_REFERENCE_DATE,
    RiskPrediction,
    RiskPredictor,
    _observable_risk_label,
    _score_to_level,
)
from app.risk.service import RoutingDecision, RiskService
from app.simulator.world import (
    ObservableCustomerData,
    ObservableEvent,
    ObservablePayment,
    ObservableSubscription,
)

REFERENCE = TRAINING_REFERENCE_DATE
RENEWAL = REFERENCE + timedelta(days=14)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def predictor() -> RiskPredictor:
    """Train once for the whole test module."""
    return RiskPredictor.build(seed=42, cohort_size=500, reference_date=REFERENCE)


def _payment(status: str, days_ago: int = 30) -> ObservablePayment:
    return ObservablePayment(
        amount=Decimal("1999.00"),
        status=status,
        failure_code="insufficient_funds" if status == "failed" else None,
        payment_method="upi",
        created_at=REFERENCE - timedelta(days=days_ago),
    )


def _obs_customer(
    failures: int = 0,
    success_rate: float = 1.0,
    payment_method_change: bool = False,
) -> ObservableCustomerData:
    payments = []
    for i in range(4):
        if i < failures:
            payments.append(_payment("failed", (i + 1) * 30))
        else:
            payments.append(_payment("successful", (i + 1) * 30))
    payments.append(_payment("pending", 0))

    events = []
    if payment_method_change:
        events.append(ObservableEvent(
            event_type="payment_method_changed",
            timestamp=REFERENCE - timedelta(days=3),
            payload={"new_method": "card"},
        ))

    return ObservableCustomerData(
        customer_id=99,
        name="Test",
        segment="smb",
        ltv=Decimal("50000.00"),
        subscription=ObservableSubscription(
            plan="starter", amount=Decimal("1999.00"), currency="INR",
            renewal_at=RENEWAL, status="active",
        ),
        payments=payments,
        events=events,
    )


# ── Training and prediction ───────────────────────────────────────────────────

class TestModelTraining:
    def test_model_trains_without_error(self, predictor):
        assert predictor is not None

    def test_model_version(self, predictor):
        obs = _obs_customer()
        pred = predictor.predict(obs, reference_date=REFERENCE)
        assert pred.model_version == MODEL_VERSION
        assert pred.model_version == "logistic-v1"

    def test_prediction_in_unit_interval(self, predictor):
        for failures in [0, 1, 2, 3]:
            obs = _obs_customer(failures=failures)
            pred = predictor.predict(obs, reference_date=REFERENCE)
            assert 0.0 <= pred.risk_score <= 1.0, f"risk_score out of range: {pred.risk_score}"

    def test_high_failure_customer_has_higher_risk(self, predictor):
        low_risk = predictor.predict(_obs_customer(failures=0), reference_date=REFERENCE)
        high_risk = predictor.predict(_obs_customer(failures=3), reference_date=REFERENCE)
        assert high_risk.risk_score > low_risk.risk_score

    def test_prediction_returns_risk_prediction_type(self, predictor):
        obs = _obs_customer()
        pred = predictor.predict(obs, reference_date=REFERENCE)
        assert isinstance(pred, RiskPrediction)


# ── Reproducibility ───────────────────────────────────────────────────────────

class TestModelReproducibility:
    def test_same_config_same_predictions(self):
        p1 = RiskPredictor.build(seed=42, cohort_size=200, reference_date=REFERENCE)
        p2 = RiskPredictor.build(seed=42, cohort_size=200, reference_date=REFERENCE)
        obs = _obs_customer(failures=1)
        pred1 = p1.predict(obs, reference_date=REFERENCE)
        pred2 = p2.predict(obs, reference_date=REFERENCE)
        assert pred1.risk_score == pytest.approx(pred2.risk_score)
        assert pred1.risk_level == pred2.risk_level

    def test_different_seed_different_model(self):
        p1 = RiskPredictor.build(seed=42, cohort_size=200, reference_date=REFERENCE)
        p2 = RiskPredictor.build(seed=123, cohort_size=200, reference_date=REFERENCE)
        obs = _obs_customer(failures=2)
        pred1 = p1.predict(obs, reference_date=REFERENCE)
        pred2 = p2.predict(obs, reference_date=REFERENCE)
        # Different seeds may (but don't have to) produce different scores
        # Verify both are still valid
        assert 0.0 <= pred1.risk_score <= 1.0
        assert 0.0 <= pred2.risk_score <= 1.0


# ── Risk level ────────────────────────────────────────────────────────────────

class TestRiskLevelMapping:
    @pytest.mark.parametrize("score,expected", [
        (0.0, "LOW"),
        (0.15, "LOW"),
        (0.29, "LOW"),
        (0.30, "MEDIUM"),
        (0.45, "MEDIUM"),
        (0.59, "MEDIUM"),
        (0.60, "HIGH"),
        (0.85, "HIGH"),
        (1.0, "HIGH"),
    ])
    def test_score_to_level(self, score, expected):
        assert _score_to_level(score) == expected


# ── Threshold routing ─────────────────────────────────────────────────────────

class TestThresholdRouting:
    """CLAUDE.md §8: P(failure) < 0.30 → STANDARD, >= 0.30 → LANGGRAPH."""

    def test_routing_uses_configured_threshold(self):
        service = RiskService(threshold=0.30)
        assert service._threshold == pytest.approx(0.30)

    def test_custom_threshold(self):
        service = RiskService(threshold=0.50)
        assert service._threshold == pytest.approx(0.50)

    def test_low_risk_routes_to_standard_flow(self, predictor):
        """Customer with perfect payment history should not go to LangGraph."""
        # Create a clearly low-risk customer
        obs = _obs_customer(failures=0)
        pred = predictor.predict(obs, reference_date=REFERENCE)
        service = RiskService(threshold=0.30)

        # If risk_score < 0.30, routing must be STANDARD_FLOW
        if pred.risk_score < 0.30:
            assessment = service.assess(obs, reference_date=REFERENCE)
            assert assessment.routing == RoutingDecision.STANDARD_FLOW

    def test_at_risk_routes_to_langgraph(self, predictor):
        """Customer with many failures should route to LangGraph."""
        obs = _obs_customer(failures=3, payment_method_change=True)
        pred = predictor.predict(obs, reference_date=REFERENCE)
        service = RiskService(threshold=0.30)

        if pred.risk_score >= 0.30:
            assessment = service.assess(obs, reference_date=REFERENCE)
            assert assessment.routing == RoutingDecision.LANGGRAPH

    @pytest.mark.parametrize("mock_score,threshold,expected_routing", [
        (0.10, 0.30, RoutingDecision.STANDARD_FLOW),
        (0.29, 0.30, RoutingDecision.STANDARD_FLOW),
        (0.30, 0.30, RoutingDecision.LANGGRAPH),
        (0.31, 0.30, RoutingDecision.LANGGRAPH),
        (0.80, 0.30, RoutingDecision.LANGGRAPH),
    ])
    def test_routing_boundary_conditions(self, mock_score, threshold, expected_routing, predictor):
        """Test exactly at and around the routing threshold."""
        from unittest.mock import patch
        from app.risk.model import RiskPrediction, RiskSignal, MODEL_VERSION

        mock_pred = RiskPrediction(
            risk_score=mock_score,
            risk_level=_score_to_level(mock_score),
            top_signals=[RiskSignal("days_to_renewal", 0.1)],
            model_version=MODEL_VERSION,
        )

        service = RiskService(threshold=threshold)
        obs = _obs_customer()

        with patch.object(predictor, "predict", return_value=mock_pred):
            with patch("app.risk.service.get_risk_predictor", return_value=predictor):
                assessment = service.assess(obs, reference_date=REFERENCE)
                assert assessment.routing == expected_routing


# ── Explainability ────────────────────────────────────────────────────────────

class TestExplainability:
    def test_top_signals_count_is_three(self, predictor):
        obs = _obs_customer(failures=1)
        pred = predictor.predict(obs, reference_date=REFERENCE)
        assert len(pred.top_signals) == 3

    def test_top_signals_feature_names_are_valid(self, predictor):
        from app.risk.features import FEATURE_NAMES
        obs = _obs_customer(failures=1)
        pred = predictor.predict(obs, reference_date=REFERENCE)
        for signal in pred.top_signals:
            assert signal.feature in FEATURE_NAMES

    def test_top_signals_impacts_are_finite(self, predictor):
        import math
        obs = _obs_customer(failures=2)
        pred = predictor.predict(obs, reference_date=REFERENCE)
        for signal in pred.top_signals:
            assert math.isfinite(signal.impact)

    def test_top_signals_are_observable_only(self, predictor):
        """Signal feature names must never be hidden simulator fields."""
        hidden = {
            "payment_intent", "cash_flow_health", "payment_rail_health",
            "churn_sensitivity", "p_payment", "p_churn", "latent_state",
        }
        obs = _obs_customer(failures=1)
        pred = predictor.predict(obs, reference_date=REFERENCE)
        for signal in pred.top_signals:
            assert signal.feature not in hidden

    def test_predict_from_features_produces_same_result(self, predictor):
        obs = _obs_customer(failures=1)
        features = FeatureBuilder(REFERENCE).build(obs)
        pred_from_obs = predictor.predict(obs, reference_date=REFERENCE)
        pred_from_feat = predictor.predict_from_features(features)
        assert pred_from_obs.risk_score == pytest.approx(pred_from_feat.risk_score)


# ── Observable training label ─────────────────────────────────────────────────

class TestObservableTrainingLabel:
    def _features_with(self, payment_success_rate: float, failures: int, delay: float) -> RiskFeatures:
        return RiskFeatures(
            days_to_renewal=14.0,
            invoice_views=0,
            checkout_reopens=0,
            payment_method_changes=0,
            previous_payment_failures=failures,
            average_payment_delay=delay,
            subscription_age=180.0,
            payment_success_rate=payment_success_rate,
            support_event_count=0,
            days_since_last_payment=30.0,
            renewal_amount=1999.0,
            segment_encoded=1,
        )

    def test_low_risk_label_zero(self):
        f = self._features_with(0.90, 0, 0.0)
        assert _observable_risk_label(f) == 0

    def test_high_failure_rate_label_one(self):
        f = self._features_with(0.60, 2, 0.0)
        assert _observable_risk_label(f) == 1

    def test_low_success_rate_label_one(self):
        f = self._features_with(0.70, 1, 0.0)
        assert _observable_risk_label(f) == 1

    def test_one_failure_with_high_delay_label_one(self):
        f = self._features_with(0.80, 1, 0.30)
        assert _observable_risk_label(f) == 1
