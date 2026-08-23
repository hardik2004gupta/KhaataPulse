"""
Simulator tests - CLAUDE.md §32 requirements.

Tests the generator, isolation boundary, determinism, and observable data contract.
No database required for these tests.
"""
import dataclasses
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.simulator.generator import generate_world
from app.simulator.latent_state import CustomerLatentState
from app.simulator.outcomes import PotentialOutcomes, ACTION_TYPES
from app.simulator.world import (
    WorldInternal,
    ObservableCustomerData,
    extract_observable,
)
from app.db.models.event import OBSERVABLE_EVENT_TYPES


REFERENCE_DATE = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)


def _build_world(seed: int = 42, cohort_size: int = 100) -> tuple[list[dict], WorldInternal]:
    raw = generate_world(
        seed=seed,
        cohort_size=cohort_size,
        simulator_version="v1",
        reference_date=REFERENCE_DATE,
    )
    world = WorldInternal.from_raw_records(
        raw=raw,
        seed=seed,
        cohort_size=cohort_size,
        simulator_version="v1",
        reference_date=REFERENCE_DATE,
    )
    return raw, world


# ── Determinism ───────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_same_seed_same_customer_count(self):
        raw_a = generate_world(42, 100, "v1", REFERENCE_DATE)
        raw_b = generate_world(42, 100, "v1", REFERENCE_DATE)
        assert len(raw_a) == len(raw_b) == 100

    def test_same_seed_same_names(self):
        raw_a = generate_world(42, 50, "v1", REFERENCE_DATE)
        raw_b = generate_world(42, 50, "v1", REFERENCE_DATE)
        names_a = [r["customer"]["name"] for r in raw_a]
        names_b = [r["customer"]["name"] for r in raw_b]
        assert names_a == names_b

    def test_same_seed_same_amounts(self):
        raw_a = generate_world(42, 50, "v1", REFERENCE_DATE)
        raw_b = generate_world(42, 50, "v1", REFERENCE_DATE)
        amounts_a = [r["subscription"]["amount"] for r in raw_a]
        amounts_b = [r["subscription"]["amount"] for r in raw_b]
        assert amounts_a == amounts_b

    def test_same_seed_same_latent_states(self):
        raw_a = generate_world(42, 20, "v1", REFERENCE_DATE)
        raw_b = generate_world(42, 20, "v1", REFERENCE_DATE)
        for a, b in zip(raw_a, raw_b):
            la: CustomerLatentState = a["_latent"]
            lb: CustomerLatentState = b["_latent"]
            assert la.payment_intent == pytest.approx(lb.payment_intent)
            assert la.cash_flow_health == pytest.approx(lb.cash_flow_health)

    def test_different_seeds_produce_different_worlds(self):
        raw_42 = generate_world(42, 50, "v1", REFERENCE_DATE)
        raw_123 = generate_world(123, 50, "v1", REFERENCE_DATE)
        names_42 = [r["customer"]["name"] for r in raw_42]
        names_123 = [r["customer"]["name"] for r in raw_123]
        # Very unlikely to be identical across 50 customers
        assert names_42 != names_123

    def test_seed_42_123_456_all_reproducible(self):
        for seed in [42, 123, 456]:
            raw_a = generate_world(seed, 30, "v1", REFERENCE_DATE)
            raw_b = generate_world(seed, 30, "v1", REFERENCE_DATE)
            assert [r["customer"]["name"] for r in raw_a] == [r["customer"]["name"] for r in raw_b]


# ── Cohort size ────────────────────────────────────────────────────────────────

class TestCohortSize:
    def test_exact_cohort_size(self):
        for size in [1, 10, 100, 500]:
            raw = generate_world(42, size, "v1", REFERENCE_DATE)
            assert len(raw) == size

    def test_default_cohort_size_3000(self):
        raw = generate_world(42, 3000, "v1", REFERENCE_DATE)
        assert len(raw) == 3000


# ── Latent state isolation ─────────────────────────────────────────────────────

class TestLatentStateIsolation:
    """
    CLAUDE.md §7: The agent must never receive CustomerLatentState.
    These tests verify the isolation boundary.
    """

    def test_observable_customer_data_has_no_latent_state(self):
        raw, world = _build_world()
        obs_world = extract_observable(world)
        for obs_customer in obs_world.customers:
            assert isinstance(obs_customer, ObservableCustomerData)
            # Must not have latent_state attribute
            assert not hasattr(obs_customer, "latent_state")
            assert not hasattr(obs_customer, "payment_intent")
            assert not hasattr(obs_customer, "cash_flow_health")
            assert not hasattr(obs_customer, "payment_rail_health")
            assert not hasattr(obs_customer, "churn_sensitivity")

    def test_observable_customer_data_has_no_potential_outcomes(self):
        raw, world = _build_world()
        obs_world = extract_observable(world)
        for obs_customer in obs_world.customers:
            assert not hasattr(obs_customer, "potential_outcomes")
            assert not hasattr(obs_customer, "p_payment")
            assert not hasattr(obs_customer, "p_churn")

    def test_observable_customer_fields_are_correct(self):
        raw, world = _build_world(cohort_size=5)
        obs_world = extract_observable(world)
        for obs in obs_world.customers:
            assert isinstance(obs.customer_id, int)
            assert isinstance(obs.name, str)
            assert obs.segment in ("consumer", "smb", "enterprise")
            assert isinstance(obs.ltv, Decimal)
            assert obs.ltv > 0
            assert obs.subscription.amount > 0
            assert obs.subscription.currency == "INR"

    def test_raw_record_keys_include_hidden_fields(self):
        """Raw records have hidden fields - verify they exist for internal use."""
        raw, _ = _build_world(cohort_size=3)
        for r in raw:
            assert "_latent" in r
            assert "_outcomes" in r
            assert isinstance(r["_latent"], CustomerLatentState)
            assert isinstance(r["_outcomes"], PotentialOutcomes)

    def test_latent_state_values_in_bounds(self):
        raw, _ = _build_world(cohort_size=100)
        for r in raw:
            lat = r["_latent"]
            assert 0.0 <= lat.payment_intent <= 1.0
            assert 0.0 <= lat.cash_flow_health <= 1.0
            assert 0.0 <= lat.payment_rail_health <= 1.0
            assert 0.0 <= lat.churn_sensitivity <= 1.0
            assert lat.customer_ltv > 0


# ── Potential outcome isolation ────────────────────────────────────────────────

class TestPotentialOutcomeIsolation:
    """
    CLAUDE.md §7: P(payment|action) and P(churn|action) must never reach the agent.
    """

    def test_outcomes_cover_all_action_types(self):
        raw, _ = _build_world(cohort_size=10)
        for r in raw:
            outcomes: PotentialOutcomes = r["_outcomes"]
            for action in ACTION_TYPES:
                ao = outcomes.for_action(action)
                assert 0.0 <= ao.p_payment <= 1.0
                assert 0.0 <= ao.p_churn <= 1.0

    def test_outcomes_not_in_observable_events(self):
        raw, world = _build_world(cohort_size=20)
        obs_world = extract_observable(world)
        for obs in obs_world.customers:
            for event in obs.events:
                payload = event.payload
                assert "p_payment" not in payload
                assert "p_churn" not in payload
                assert "payment_intent" not in payload
                assert "cash_flow_health" not in payload
                assert "payment_rail_health" not in payload
                assert "churn_sensitivity" not in payload


# ── Event generation ──────────────────────────────────────────────────────────

class TestEventGeneration:
    def test_all_customers_have_events(self):
        raw, world = _build_world(cohort_size=50)
        obs_world = extract_observable(world)
        for obs in obs_world.customers:
            assert len(obs.events) >= 1

    def test_all_customers_have_renewal_approaching_event(self):
        raw, world = _build_world(cohort_size=50)
        obs_world = extract_observable(world)
        for obs in obs_world.customers:
            event_types = {e.event_type for e in obs.events}
            assert "renewal_approaching" in event_types

    def test_all_event_types_are_observable(self):
        raw, world = _build_world(cohort_size=100)
        obs_world = extract_observable(world)
        for obs in obs_world.customers:
            for event in obs.events:
                assert event.event_type in OBSERVABLE_EVENT_TYPES, (
                    f"Non-observable event type found: {event.event_type}"
                )

    def test_events_have_timestamps(self):
        raw, world = _build_world(cohort_size=20)
        obs_world = extract_observable(world)
        for obs in obs_world.customers:
            for event in obs.events:
                assert isinstance(event.timestamp, datetime)

    def test_event_payloads_have_no_hidden_keys(self):
        HIDDEN_KEYS = {
            "payment_intent", "cash_flow_health", "payment_rail_health",
            "churn_sensitivity", "p_payment", "p_churn",
        }
        raw, world = _build_world(cohort_size=50)
        obs_world = extract_observable(world)
        for obs in obs_world.customers:
            for event in obs.events:
                for key in event.payload:
                    assert key not in HIDDEN_KEYS, (
                        f"Hidden key '{key}' found in event payload for {event.event_type}"
                    )

    def test_events_ordered_by_timestamp(self):
        raw, world = _build_world(cohort_size=30)
        obs_world = extract_observable(world)
        for obs in obs_world.customers:
            timestamps = [e.timestamp for e in obs.events]
            assert timestamps == sorted(timestamps)


# ── Referential integrity ──────────────────────────────────────────────────────

class TestReferentialIntegrity:
    def test_every_customer_has_subscription(self):
        raw = generate_world(42, 50, "v1", REFERENCE_DATE)
        for r in raw:
            assert r["subscription"] is not None
            assert r["subscription"]["customer_id"] == r["customer"]["id"]

    def test_every_customer_has_payments(self):
        raw = generate_world(42, 50, "v1", REFERENCE_DATE)
        for r in raw:
            assert len(r["payments"]) >= 1

    def test_payment_customer_ids_match(self):
        raw = generate_world(42, 20, "v1", REFERENCE_DATE)
        for r in raw:
            for p in r["payments"]:
                assert p["customer_id"] == r["customer"]["id"]

    def test_subscription_amounts_are_positive(self):
        raw = generate_world(42, 100, "v1", REFERENCE_DATE)
        for r in raw:
            assert r["subscription"]["amount"] > 0

    def test_segments_are_valid(self):
        raw = generate_world(42, 100, "v1", REFERENCE_DATE)
        valid_segments = {"consumer", "smb", "enterprise"}
        for r in raw:
            assert r["customer"]["segment"] in valid_segments

    def test_payment_statuses_are_valid(self):
        raw = generate_world(42, 50, "v1", REFERENCE_DATE)
        valid_statuses = {"successful", "failed", "pending"}
        for r in raw:
            for p in r["payments"]:
                assert p["status"] in valid_statuses

    def test_renewal_dates_are_in_future(self):
        raw = generate_world(42, 50, "v1", REFERENCE_DATE)
        for r in raw:
            assert r["subscription"]["renewal_at"] > REFERENCE_DATE

    def test_pending_payment_exists_for_each_customer(self):
        raw = generate_world(42, 30, "v1", REFERENCE_DATE)
        for r in raw:
            statuses = [p["status"] for p in r["payments"]]
            assert "pending" in statuses


# ── WorldInternal boundary ─────────────────────────────────────────────────────

class TestWorldBoundary:
    def test_world_internal_has_correct_cohort_size(self):
        raw, world = _build_world(seed=42, cohort_size=75)
        assert len(world.records) == 75

    def test_observable_world_count_matches_internal(self):
        raw, world = _build_world(cohort_size=40)
        obs_world = extract_observable(world)
        assert len(obs_world.customers) == len(world.records)

    def test_world_metadata(self):
        raw, world = _build_world(seed=123, cohort_size=10)
        assert world.seed == 123
        assert world.cohort_size == 10
        assert world.simulator_version == "v1"
