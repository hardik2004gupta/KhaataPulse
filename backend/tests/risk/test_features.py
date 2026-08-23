"""
Feature engineering tests - CLAUDE.md §32.

Verifies:
  - Correct feature values from observable data
  - Isolation: no hidden simulator field enters the feature vector
  - FEATURE_NAMES matches RiskFeatures.to_array() order
  - All features traceable to observable-only sources
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.risk.features import FEATURE_NAMES, FeatureBuilder, RiskFeatures
from app.simulator.world import (
    ObservableCustomerData,
    ObservableEvent,
    ObservablePayment,
    ObservableSubscription,
)

REFERENCE = datetime(2026, 1, 1, tzinfo=timezone.utc)
RENEWAL = REFERENCE + timedelta(days=14)


def _make_obs(
    segment: str = "smb",
    plan: str = "starter",
    amount: str = "1999.00",
    payments: list[ObservablePayment] | None = None,
    events: list[ObservableEvent] | None = None,
) -> ObservableCustomerData:
    sub = ObservableSubscription(
        plan=plan,
        amount=Decimal(amount),
        currency="INR",
        renewal_at=RENEWAL,
        status="active",
    )
    return ObservableCustomerData(
        customer_id=1,
        name="Test User",
        segment=segment,
        ltv=Decimal("50000.00"),
        subscription=sub,
        payments=payments or [],
        events=events or [],
    )


def _payment(status: str, days_ago: int = 30) -> ObservablePayment:
    return ObservablePayment(
        amount=Decimal("1999.00"),
        status=status,
        failure_code="insufficient_funds" if status == "failed" else None,
        payment_method="upi",
        created_at=REFERENCE - timedelta(days=days_ago),
    )


def _event(event_type: str) -> ObservableEvent:
    return ObservableEvent(
        event_type=event_type,
        timestamp=REFERENCE - timedelta(days=5),
        payload={"test": True},
    )


# ── Feature values ────────────────────────────────────────────────────────────

class TestFeatureValues:
    def test_days_to_renewal(self):
        obs = _make_obs()
        f = FeatureBuilder(REFERENCE).build(obs)
        assert abs(f.days_to_renewal - 14.0) < 0.1

    def test_invoice_views(self):
        obs = _make_obs(events=[_event("invoice_viewed"), _event("invoice_viewed")])
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.invoice_views == 2

    def test_checkout_reopens(self):
        obs = _make_obs(events=[_event("checkout_reopened")])
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.checkout_reopens == 1

    def test_payment_method_changes(self):
        obs = _make_obs(events=[_event("payment_method_changed")])
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.payment_method_changes == 1

    def test_previous_payment_failures(self):
        payments = [_payment("failed", 60), _payment("successful", 30), _payment("pending", 0)]
        obs = _make_obs(payments=payments)
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.previous_payment_failures == 1

    def test_payment_success_rate_all_successful(self):
        payments = [_payment("successful", 60), _payment("successful", 30), _payment("pending", 0)]
        obs = _make_obs(payments=payments)
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.payment_success_rate == pytest.approx(1.0)

    def test_payment_success_rate_mixed(self):
        payments = [_payment("successful", 60), _payment("failed", 30), _payment("pending", 0)]
        obs = _make_obs(payments=payments)
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.payment_success_rate == pytest.approx(0.5)

    def test_support_event_count(self):
        obs = _make_obs(events=[_event("support_message"), _event("support_message")])
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.support_event_count == 2

    def test_subscription_age_from_oldest_payment(self):
        payments = [_payment("successful", 180), _payment("successful", 30), _payment("pending", 0)]
        obs = _make_obs(payments=payments)
        f = FeatureBuilder(REFERENCE).build(obs)
        assert abs(f.subscription_age - 180.0) < 1.0

    def test_days_since_last_payment(self):
        payments = [_payment("successful", 35), _payment("pending", 0)]
        obs = _make_obs(payments=payments)
        f = FeatureBuilder(REFERENCE).build(obs)
        assert abs(f.days_since_last_payment - 35.0) < 1.0

    def test_renewal_amount(self):
        obs = _make_obs(amount="4999.00")
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.renewal_amount == pytest.approx(4999.0)

    def test_segment_encoded_consumer(self):
        obs = _make_obs(segment="consumer")
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.segment_encoded == 0

    def test_segment_encoded_smb(self):
        obs = _make_obs(segment="smb")
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.segment_encoded == 1

    def test_segment_encoded_enterprise(self):
        obs = _make_obs(segment="enterprise")
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.segment_encoded == 2

    def test_no_payments_does_not_crash(self):
        obs = _make_obs(payments=[])
        f = FeatureBuilder(REFERENCE).build(obs)
        assert f.payment_success_rate == pytest.approx(1.0)
        assert f.previous_payment_failures == 0
        assert f.subscription_age == pytest.approx(0.0)


# ── Feature array contract ────────────────────────────────────────────────────

class TestFeatureArrayContract:
    def test_to_array_length_matches_feature_names(self):
        obs = _make_obs()
        f = FeatureBuilder(REFERENCE).build(obs)
        assert len(f.to_array()) == len(FEATURE_NAMES)

    def test_to_array_order_matches_feature_names(self):
        """Each index in to_array() must correspond to the same-index FEATURE_NAME."""
        obs = _make_obs(events=[_event("invoice_viewed"), _event("support_message")])
        f = FeatureBuilder(REFERENCE).build(obs)
        arr = f.to_array()
        d = f.to_dict()
        for i, name in enumerate(FEATURE_NAMES):
            assert arr[i] == pytest.approx(d[name])

    def test_to_dict_has_all_feature_names(self):
        obs = _make_obs()
        f = FeatureBuilder(REFERENCE).build(obs)
        d = f.to_dict()
        for name in FEATURE_NAMES:
            assert name in d


# ── Isolation: no hidden fields ───────────────────────────────────────────────

class TestFeatureIsolation:
    HIDDEN_FIELD_NAMES = {
        "latent_state", "payment_intent", "cash_flow_health",
        "payment_rail_health", "churn_sensitivity", "customer_ltv",
        "potential_outcomes", "p_payment", "p_churn",
        "_latent", "_outcomes",
    }

    def test_risk_features_dataclass_has_no_hidden_fields(self):
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(RiskFeatures)}
        overlap = self.HIDDEN_FIELD_NAMES & field_names
        assert not overlap, f"Hidden fields found in RiskFeatures: {overlap}"

    def test_to_dict_has_no_hidden_keys(self):
        obs = _make_obs()
        f = FeatureBuilder(REFERENCE).build(obs)
        d = f.to_dict()
        overlap = self.HIDDEN_FIELD_NAMES & set(d.keys())
        assert not overlap

    def test_to_array_values_are_all_finite(self):
        import math
        obs = _make_obs(
            payments=[_payment("failed", 60), _payment("successful", 30), _payment("pending", 0)],
            events=[_event("invoice_viewed"), _event("payment_delayed"), _event("support_message")],
        )
        f = FeatureBuilder(REFERENCE).build(obs)
        for v in f.to_array():
            assert math.isfinite(v), f"Non-finite value in feature array: {v}"

    def test_feature_builder_only_uses_observable_customer_data(self):
        """FeatureBuilder.build accepts ObservableCustomerData only - no latent state."""
        import inspect
        sig = inspect.signature(FeatureBuilder.build)
        param_names = list(sig.parameters.keys())
        # Should have self, obs (ObservableCustomerData), nothing else
        assert "obs" in param_names
        # Must not have latent_state or potential_outcomes as params
        assert "latent_state" not in param_names
        assert "potential_outcomes" not in param_names


# ── Full simulator pipeline isolation ────────────────────────────────────────

class TestSimulatorPipelineIsolation:
    """
    End-to-end: generate world → extract observable → build features.
    Verify no hidden state reaches the feature vector.
    """

    def test_features_from_simulator_contain_no_hidden_state(self):
        from datetime import datetime, timezone
        from app.simulator.generator import generate_world
        from app.simulator.world import WorldInternal, extract_observable

        ref = datetime(2026, 1, 1, tzinfo=timezone.utc)
        raw = generate_world(42, 10, "v1", ref)
        world = WorldInternal.from_raw_records(raw=raw, seed=42, cohort_size=10, simulator_version="v1", reference_date=ref)
        obs_world = extract_observable(world)

        builder = FeatureBuilder(ref)
        hidden_keys = {
            "payment_intent", "cash_flow_health", "payment_rail_health",
            "churn_sensitivity", "p_payment", "p_churn",
        }
        for obs in obs_world.customers:
            feat = builder.build(obs)
            for key in hidden_keys:
                assert not hasattr(feat, key), f"Hidden key '{key}' found in RiskFeatures"
            for v in feat.to_array():
                assert isinstance(v, (int, float))
