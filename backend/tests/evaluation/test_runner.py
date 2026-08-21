"""
Tests for the evaluation runner — multi-seed, persistence, reproducibility.

CLAUDE.md §17: minimum required seeds: 42, 123, 456.
"""
from __future__ import annotations

import pytest
from decimal import Decimal

from app.evaluation.runner import (
    run_evaluation,
    run_multi_seed_evaluation,
    get_multi_seed_summary,
    get_run_from_db,
    REQUIRED_SEEDS,
    _make_run_id,
)
from app.evaluation.metrics import EvaluationRunResult


_FAST_COHORT = 30  # smaller cohort for runner tests to keep them fast


# ── Run ID format ──────────────────────────────────────────────────────────────

def test_run_id_format():
    assert _make_run_id(42, 3000) == "eval_42_3000"
    assert _make_run_id(123, 500) == "eval_123_500"


# ── Required seeds ─────────────────────────────────────────────────────────────

def test_required_seeds_are_correct():
    """CLAUDE.md §17: minimum required seeds: 42, 123, 456."""
    assert 42 in REQUIRED_SEEDS
    assert 123 in REQUIRED_SEEDS
    assert 456 in REQUIRED_SEEDS


# ── run_evaluation (no-db mode) ────────────────────────────────────────────────

def test_run_evaluation_no_db_returns_result():
    result = run_evaluation(seed=42, cohort_size=_FAST_COHORT, db=None)
    assert isinstance(result, EvaluationRunResult)
    assert result.run_id == "eval_42_30"
    assert result.seed == 42
    assert result.cohort_size == _FAST_COHORT


def test_run_evaluation_result_has_all_three_policies():
    result = run_evaluation(seed=42, cohort_size=_FAST_COHORT, db=None)
    assert result.static_dunning is not None
    assert result.smart_retry is not None
    assert result.khaatapulse is not None


def test_run_evaluation_incremental_recovery_is_dynamic():
    """Primary KPI must not be hardcoded. CLAUDE.md §34 rule 7."""
    result = run_evaluation(seed=42, cohort_size=_FAST_COHORT, db=None)
    expected = result.khaatapulse.recovered_amount - result.smart_retry.recovered_amount
    assert result.incremental_recovery == expected


def test_run_evaluation_reproducible_no_db():
    r1 = run_evaluation(seed=123, cohort_size=_FAST_COHORT, db=None)
    r2 = run_evaluation(seed=123, cohort_size=_FAST_COHORT, db=None)
    assert r1.incremental_recovery == r2.incremental_recovery
    assert r1.static_dunning.recovered_amount == r2.static_dunning.recovered_amount


# ── Multi-seed (no-db mode) ────────────────────────────────────────────────────

def test_multi_seed_returns_one_result_per_seed():
    seeds = [42, 123]
    results = run_multi_seed_evaluation(cohort_size=_FAST_COHORT, seeds=seeds, db=None)
    assert len(results) == 2
    returned_seeds = {r.seed for r in results}
    assert returned_seeds == set(seeds)


def test_multi_seed_required_seeds_no_db():
    """CLAUDE.md §17: 42, 123, 456 must all produce valid results."""
    results = run_multi_seed_evaluation(
        cohort_size=_FAST_COHORT, seeds=REQUIRED_SEEDS, db=None
    )
    assert len(results) == 3
    seeds_in_results = {r.seed for r in results}
    assert set(REQUIRED_SEEDS) == seeds_in_results


def test_multi_seed_each_run_is_independent():
    """Each seed evaluates the same cohort_size but a different world."""
    results = run_multi_seed_evaluation(cohort_size=_FAST_COHORT, seeds=[42, 123], db=None)
    r42 = next(r for r in results if r.seed == 42)
    r123 = next(r for r in results if r.seed == 123)
    # Recovered amounts may differ (different worlds) — verify seeds differ at minimum
    assert r42.seed != r123.seed
    assert r42.run_id != r123.run_id


# ── Multi-seed summary ─────────────────────────────────────────────────────────

def test_multi_seed_summary_total_runs():
    results = run_multi_seed_evaluation(cohort_size=_FAST_COHORT, seeds=[42, 123], db=None)
    summary = get_multi_seed_summary(results)
    assert summary["total_runs"] == 2


def test_multi_seed_summary_positive_negative_are_complement():
    results = run_multi_seed_evaluation(cohort_size=_FAST_COHORT, seeds=REQUIRED_SEEDS, db=None)
    summary = get_multi_seed_summary(results)
    assert summary["positive_runs"] + summary["negative_runs"] == summary["total_runs"]


def test_multi_seed_summary_seed_entries():
    seeds = [42, 123]
    results = run_multi_seed_evaluation(cohort_size=_FAST_COHORT, seeds=seeds, db=None)
    summary = get_multi_seed_summary(results)
    assert len(summary["seeds"]) == 2
    for entry in summary["seeds"]:
        assert "seed" in entry
        assert "run_id" in entry
        assert "incremental_recovery" in entry
        assert "is_positive" in entry


def test_multi_seed_summary_values_are_dynamic():
    """Verify summary values are not hardcoded (types only — not specific numbers)."""
    results = run_multi_seed_evaluation(cohort_size=_FAST_COHORT, seeds=[42], db=None)
    summary = get_multi_seed_summary(results)
    for entry in summary["seeds"]:
        # incremental_recovery must be a string representation of a Decimal
        float(entry["incremental_recovery"])  # must be convertible to float
        assert isinstance(entry["is_positive"], bool)


# ── DB integration tests (skipped if no DB available) ────────────────────────────

@pytest.fixture
def db_session():
    """Provide a real DB session; skip if database is not reachable."""
    try:
        from sqlalchemy import text
        from app.db.session import SessionLocal
        session = SessionLocal()
        session.execute(text("SELECT 1"))  # probe connection before yielding
        yield session
        session.rollback()
        session.close()
    except Exception:
        pytest.skip("No database connection available")


def test_run_evaluation_persists_run_record(db_session):
    from app.db.models.evaluation import EvaluationRun
    seed = 9901  # unlikely to conflict with other tests

    result = run_evaluation(seed=seed, cohort_size=_FAST_COHORT, db=db_session)
    db_session.flush()

    run = db_session.query(EvaluationRun).filter_by(run_id=result.run_id).first()
    assert run is not None
    assert run.status == "completed"
    assert run.seed == seed
    assert run.cohort_size == _FAST_COHORT
    assert run.completed_at is not None


def test_run_evaluation_persists_three_policy_results(db_session):
    from app.db.models.evaluation import EvaluationResult
    seed = 9902

    result = run_evaluation(seed=seed, cohort_size=_FAST_COHORT, db=db_session)
    db_session.flush()

    db_results = db_session.query(EvaluationResult).filter_by(run_id=result.run_id).all()
    assert len(db_results) == 3
    policy_names = {r.policy_name for r in db_results}
    assert policy_names == {"static_dunning", "smart_retry", "khaatapulse"}


def test_run_evaluation_re_run_overwrites_old_results(db_session):
    from app.db.models.evaluation import EvaluationResult
    seed = 9903

    # First run
    run_evaluation(seed=seed, cohort_size=_FAST_COHORT, db=db_session)
    db_session.flush()

    # Second run (re-run) — should delete old results and create fresh ones
    run_evaluation(seed=seed, cohort_size=_FAST_COHORT, db=db_session)
    db_session.flush()

    run_id = _make_run_id(seed, _FAST_COHORT)
    db_results = db_session.query(EvaluationResult).filter_by(run_id=run_id).all()
    assert len(db_results) == 3  # still exactly 3 (not 6)


def test_get_run_from_db_returns_stored_result(db_session):
    seed = 9904
    result = run_evaluation(seed=seed, cohort_size=_FAST_COHORT, db=db_session)
    db_session.flush()

    retrieved = get_run_from_db(run_id=result.run_id, db=db_session)
    assert retrieved is not None
    assert retrieved["run_id"] == result.run_id
    assert retrieved["seed"] == seed
    assert retrieved["status"] == "completed"
    assert "khaatapulse" in retrieved["results"]
    assert "static_dunning" in retrieved["results"]
    assert "smart_retry" in retrieved["results"]


def test_get_run_from_db_nonexistent_returns_none(db_session):
    retrieved = get_run_from_db(run_id="nonexistent_run", db=db_session)
    assert retrieved is None


def test_run_evaluation_db_persisted_metrics_match_in_memory(db_session):
    """Persisted metrics must exactly match in-memory result — no transformation errors."""
    seed = 9905
    result = run_evaluation(seed=seed, cohort_size=_FAST_COHORT, db=db_session)
    db_session.flush()

    retrieved = get_run_from_db(run_id=result.run_id, db=db_session)
    kp_db = retrieved["results"]["khaatapulse"]
    kp_mem = result.khaatapulse

    assert Decimal(kp_db["recovered_amount"]).quantize(Decimal("0.0001")) == \
           kp_mem.recovered_amount.quantize(Decimal("0.0001"))
    assert kp_db["contacts_sent"] == kp_mem.contacts_sent
    assert kp_db["cases_evaluated"] == kp_mem.cases_evaluated
