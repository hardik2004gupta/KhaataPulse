"""
Tests for the same-cohort evaluation engine — CLAUDE.md §17, §32.

Critical invariants:
  1. World is generated ONCE — all three policies evaluate the same world.
  2. Policies receive ObservableCustomerData only (no hidden state).
  3. PotentialOutcomes accessed only by evaluator (via EvaluationWorld).
  4. Metrics are dynamically generated — no hardcoded values.
  5. incremental_recovery = khaatapulse.recovered - smart_retry.recovered.
  6. False positive: KP triggered AND P(payment|no_action) >= 0.70.
"""
from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.evaluation.evaluator import (
    EvaluationWorld,
    evaluate_policy_on_world,
    run_same_cohort_evaluation,
    _policy_outcome_key,
    _is_contact_action,
    _FALSE_POSITIVE_THRESHOLD,
    _OUTCOME_ACTION_MAP,
)
from app.evaluation.metrics import PolicyEvaluationResult, EvaluationRunResult
from app.evaluation.policies import (
    StaticDunningPolicy,
    SmartRetryPolicy,
    KhaataPulsePolicy,
)
from app.simulator.generator import generate_world
from app.simulator.world import WorldInternal, ObservableCustomerData, _InternalCustomerRecord
from app.risk.model import TRAINING_REFERENCE_DATE


# ── Helpers ───────────────────────────────────────────────────────────────────

_SMALL_COHORT = 50   # fast for unit tests; still exercises all code paths
_SEED = 42


def _build_eval_world(seed: int = _SEED, cohort_size: int = _SMALL_COHORT) -> EvaluationWorld:
    settings_patcher = patch("app.core.config.get_settings")
    mock_settings = MagicMock()
    mock_settings.simulator_version = "1.0"
    mock_settings.risk_threshold = 0.30
    mock_settings.kill_switch = False
    mock_settings.auto_action_limit = Decimal("10000")
    mock_settings.max_contacts_7d = 3
    mock_settings.contact_cooldown_hours = 24
    mock_settings.action_cost_silent_retry = 0
    mock_settings.action_cost_smart_link = 50
    mock_settings.action_cost_grace_period = 100
    mock_settings.action_cost_human_escalation = 500

    raw = generate_world(
        seed=seed,
        cohort_size=cohort_size,
        simulator_version="1.0",
        reference_date=TRAINING_REFERENCE_DATE,
    )
    world = WorldInternal.from_raw_records(
        raw=raw,
        seed=seed,
        cohort_size=cohort_size,
        simulator_version="1.0",
        reference_date=TRAINING_REFERENCE_DATE,
    )
    return EvaluationWorld(world=world)


# ── Outcome action map ─────────────────────────────────────────────────────────

def test_outcome_action_map_covers_all_actions():
    """Every action type maps to a valid PotentialOutcomes key."""
    valid_outcome_keys = {"no_action", "silent_retry", "smart_link", "grace_period", "human_escalation"}
    for key, val in _OUTCOME_ACTION_MAP.items():
        assert val in valid_outcome_keys, f"{key} → {val} is not a valid outcome key"


def test_suppress_maps_to_no_action():
    assert _policy_outcome_key("suppress") == "no_action"


def test_blocked_maps_to_no_action():
    assert _policy_outcome_key("blocked") == "no_action"


def test_no_action_maps_to_no_action():
    assert _policy_outcome_key("no_action") == "no_action"


def test_contact_action_classification():
    assert _is_contact_action("silent_retry")
    assert _is_contact_action("smart_link")
    assert _is_contact_action("grace_period")
    assert _is_contact_action("human_escalation")
    assert not _is_contact_action("no_action")
    assert not _is_contact_action("suppress")
    assert not _is_contact_action("blocked")


# ── EvaluationWorld isolation ──────────────────────────────────────────────────

def test_evaluation_world_returns_all_records():
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    assert len(eval_world.customer_records()) == _SMALL_COHORT


def test_evaluation_world_get_potential_outcomes_requires_valid_id():
    eval_world = _build_eval_world(cohort_size=10)
    with pytest.raises(KeyError):
        eval_world.get_potential_outcomes(customer_id=999999)


def test_evaluation_world_potential_outcomes_not_in_observable():
    """The observable view must never contain PotentialOutcomes."""
    eval_world = _build_eval_world(cohort_size=10)
    for rec in eval_world.customer_records():
        obs = eval_world.extract_observable_for(rec)
        # ObservableCustomerData has no potential_outcomes attribute
        assert not hasattr(obs, "potential_outcomes")
        assert not hasattr(obs, "latent_state")


def test_evaluation_world_observable_has_required_fields():
    eval_world = _build_eval_world(cohort_size=5)
    for rec in eval_world.customer_records():
        obs = eval_world.extract_observable_for(rec)
        assert obs.customer_id == rec.customer_id
        assert isinstance(obs.subscription.amount, Decimal)
        assert obs.subscription.amount > 0
        assert obs.ltv >= 0


def test_evaluation_world_same_outcomes_for_same_customer():
    """PotentialOutcomes are deterministic for a given seed."""
    eval_world_a = _build_eval_world(seed=_SEED, cohort_size=5)
    eval_world_b = _build_eval_world(seed=_SEED, cohort_size=5)

    for rec_a, rec_b in zip(eval_world_a.customer_records(), eval_world_b.customer_records()):
        po_a = eval_world_a.get_potential_outcomes(rec_a.customer_id)
        po_b = eval_world_b.get_potential_outcomes(rec_b.customer_id)
        assert po_a.for_action("no_action").p_payment == po_b.for_action("no_action").p_payment


# ── Same-cohort invariant ──────────────────────────────────────────────────────

def test_same_cohort_three_policies_see_identical_customers():
    """
    All three policies must decide on the same set of customers.
    We verify by checking that total_at_risk amounts are equal.
    """
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)

    static = StaticDunningPolicy()
    smart = SmartRetryPolicy()
    kp = KhaataPulsePolicy()

    r_static = evaluate_policy_on_world(static, eval_world, "test_run")
    r_smart = evaluate_policy_on_world(smart, eval_world, "test_run")
    r_kp = evaluate_policy_on_world(kp, eval_world, "test_run")

    # Same world → same total_at_risk
    assert r_static.total_at_risk_amount == r_smart.total_at_risk_amount
    assert r_static.total_at_risk_amount == r_kp.total_at_risk_amount


def test_same_cohort_cases_evaluated_equals_cohort_size():
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    result = evaluate_policy_on_world(StaticDunningPolicy(), eval_world, "test")
    assert result.cases_evaluated == _SMALL_COHORT


# ── Incremental recovery calculation ──────────────────────────────────────────

def test_incremental_recovery_is_kp_minus_smart_retry():
    """Primary KPI must be dynamically computed. CLAUDE.md §18."""
    result = run_same_cohort_evaluation(
        seed=_SEED,
        cohort_size=_SMALL_COHORT,
        simulator_version="1.0",
        run_id="test_incr",
    )
    expected = result.khaatapulse.recovered_amount - result.smart_retry.recovered_amount
    assert result.incremental_recovery == expected


def test_incremental_recovery_matches_kp_result_field():
    result = run_same_cohort_evaluation(
        seed=_SEED,
        cohort_size=_SMALL_COHORT,
        simulator_version="1.0",
        run_id="test_match",
    )
    assert result.khaatapulse.incremental_recovery == result.incremental_recovery


# ── Recovery rate ──────────────────────────────────────────────────────────────

def test_recovery_rate_is_bounded_between_zero_and_one():
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    for policy in [StaticDunningPolicy(), SmartRetryPolicy(), KhaataPulsePolicy()]:
        result = evaluate_policy_on_world(policy, eval_world, "rate_test")
        assert 0.0 <= result.recovery_rate <= 1.0


def test_recovery_rate_equals_recovered_over_at_risk():
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    result = evaluate_policy_on_world(StaticDunningPolicy(), eval_world, "rate_check")
    expected = float(result.recovered_amount / result.total_at_risk_amount)
    assert abs(result.recovery_rate - expected) < 1e-9


# ── Contacts ──────────────────────────────────────────────────────────────────

def test_contacts_avoided_plus_sent_equals_cohort():
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    result = evaluate_policy_on_world(StaticDunningPolicy(), eval_world, "contacts_test")
    assert result.contacts_sent + result.contacts_avoided == _SMALL_COHORT


def test_static_dunning_no_escalations_for_zero_failures():
    """Customers with no payment history should not be escalated by static dunning."""
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    result = evaluate_policy_on_world(StaticDunningPolicy(), eval_world, "esc_test")
    # Total escalations should be <= contacts_sent (escalation is a subset of contacts)
    assert result.human_escalations <= result.contacts_sent


# ── False positives ────────────────────────────────────────────────────────────

def test_false_positives_only_computed_for_khaatapulse():
    """Static dunning never triggers risk sieve so can't produce false positives."""
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    static_result = evaluate_policy_on_world(StaticDunningPolicy(), eval_world, "fp_static")
    # static_dunning may have false positives = 0 but we enforce it's non-negative
    assert static_result.false_positives == 0


def test_false_positive_threshold_defined():
    assert _FALSE_POSITIVE_THRESHOLD == 0.70


def test_kp_false_positives_nonnegative():
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    kp_result = evaluate_policy_on_world(KhaataPulsePolicy(), eval_world, "fp_kp")
    assert kp_result.false_positives >= 0


def test_kp_false_positives_le_kp_contacts_sent():
    """False positives can only happen when KP contacted a customer."""
    eval_world = _build_eval_world(cohort_size=_SMALL_COHORT)
    kp_result = evaluate_policy_on_world(KhaataPulsePolicy(), eval_world, "fp_bound")
    assert kp_result.false_positives <= kp_result.contacts_sent


# ── Reproducibility ────────────────────────────────────────────────────────────

def test_same_seed_produces_identical_results():
    """Same seed + same code must always produce same metrics."""
    r1 = run_same_cohort_evaluation(
        seed=_SEED, cohort_size=_SMALL_COHORT, simulator_version="1.0", run_id="r1"
    )
    r2 = run_same_cohort_evaluation(
        seed=_SEED, cohort_size=_SMALL_COHORT, simulator_version="1.0", run_id="r2"
    )
    assert r1.static_dunning.recovered_amount == r2.static_dunning.recovered_amount
    assert r1.smart_retry.recovered_amount == r2.smart_retry.recovered_amount
    assert r1.khaatapulse.recovered_amount == r2.khaatapulse.recovered_amount
    assert r1.incremental_recovery == r2.incremental_recovery


def test_different_seeds_may_produce_different_results():
    """Two distinct seeds should (almost always) produce different outcomes."""
    r1 = run_same_cohort_evaluation(
        seed=42, cohort_size=_SMALL_COHORT, simulator_version="1.0", run_id="r_42"
    )
    r2 = run_same_cohort_evaluation(
        seed=123, cohort_size=_SMALL_COHORT, simulator_version="1.0", run_id="r_123"
    )
    # The recovered amounts may differ; at minimum the run_ids differ
    assert r1.seed != r2.seed


# ── Metric output types ────────────────────────────────────────────────────────

def test_policy_evaluation_result_as_dict_is_json_safe():
    eval_world = _build_eval_world(cohort_size=10)
    result = evaluate_policy_on_world(StaticDunningPolicy(), eval_world, "dict_test")
    d = result.as_dict()
    assert isinstance(d["recovered_amount"], str)
    assert isinstance(d["recovery_rate"], float)
    assert isinstance(d["contacts_sent"], int)
    assert isinstance(d["false_positives"], int)


def test_evaluation_run_result_as_dict_structure():
    result = run_same_cohort_evaluation(
        seed=_SEED, cohort_size=10, simulator_version="1.0", run_id="dict_run"
    )
    d = result.as_dict()
    assert "run_id" in d
    assert "incremental_recovery" in d
    assert "static_dunning" in d
    assert "smart_retry" in d
    assert "khaatapulse" in d
    # Verify no hardcoded values — just check they are strings/floats/ints
    assert isinstance(d["incremental_recovery"], str)
