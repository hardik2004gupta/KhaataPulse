"""
Tests for the evaluation API endpoints — CLAUDE.md §20, §30.

POST /evaluation/run         → trigger single-seed evaluation
POST /evaluation/run/multi-seed → trigger multi-seed
GET  /evaluation/run/{run_id} → retrieve stored result
GET  /evaluation/runs         → list recent runs
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.main import app
from app.evaluation.metrics import PolicyEvaluationResult, EvaluationRunResult
from app.evaluation.policies import STATIC_DUNNING_VERSION, SMART_RETRY_VERSION, KHAATAPULSE_VERSION


# ── Minimal result fixture ─────────────────────────────────────────────────────

def _make_policy_result(name: str, version: str) -> PolicyEvaluationResult:
    return PolicyEvaluationResult(
        policy_name=name,
        policy_version=version,
        recovered_amount=Decimal("100000.00"),
        total_at_risk_amount=Decimal("500000.00"),
        recovery_rate=0.20,
        contacts_sent=50,
        contacts_avoided=200,
        human_escalations=5,
        false_positives=3,
        policy_blocks=2,
        cases_evaluated=250,
        llm_fallback_count=0,
    )


def _make_run_result(seed: int = 42, cohort_size: int = 3000) -> EvaluationRunResult:
    static = _make_policy_result("static_dunning", STATIC_DUNNING_VERSION)
    smart = _make_policy_result("smart_retry", SMART_RETRY_VERSION)
    kp = _make_policy_result("khaatapulse", KHAATAPULSE_VERSION)
    kp.incremental_recovery = Decimal("20000.00")
    return EvaluationRunResult(
        run_id=f"eval_{seed}_{cohort_size}",
        seed=seed,
        cohort_size=cohort_size,
        simulator_version="1.0",
        model_version="logistic-v1",
        policy_version=f"{STATIC_DUNNING_VERSION},{SMART_RETRY_VERSION},{KHAATAPULSE_VERSION}",
        static_dunning=static,
        smart_retry=smart,
        khaatapulse=kp,
        incremental_recovery=Decimal("20000.00"),
    )


# ── Client fixture ─────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """
    TestClient with mocked DB and run_evaluation for fast API tests.
    The evaluator integration is tested in test_evaluator.py.
    """
    with TestClient(app) as c:
        yield c


# ── POST /evaluation/run ───────────────────────────────────────────────────────

def test_post_evaluation_run_returns_200(client):
    mock_result = _make_run_result()
    with patch("app.api.routes.evaluation.run_evaluation", return_value=mock_result):
        resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 100})
    assert resp.status_code == 200


def test_post_evaluation_run_response_has_run_id(client):
    mock_result = _make_run_result()
    with patch("app.api.routes.evaluation.run_evaluation", return_value=mock_result):
        resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 100})
    body = resp.json()
    assert "run_id" in body
    assert body["run_id"] == "eval_42_3000"


def test_post_evaluation_run_response_status_completed(client):
    mock_result = _make_run_result()
    with patch("app.api.routes.evaluation.run_evaluation", return_value=mock_result):
        resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 100})
    body = resp.json()
    assert body["status"] == "completed"


def test_post_evaluation_run_response_has_results(client):
    mock_result = _make_run_result()
    with patch("app.api.routes.evaluation.run_evaluation", return_value=mock_result):
        resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 100})
    body = resp.json()
    assert "results" in body
    results = body["results"]
    assert "static_dunning" in results
    assert "smart_retry" in results
    assert "khaatapulse" in results


def test_post_evaluation_run_no_hardcoded_metrics(client):
    """API must return dynamically-generated metrics, not hardcoded values."""
    mock_result = _make_run_result()
    with patch("app.api.routes.evaluation.run_evaluation", return_value=mock_result):
        resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 100})
    body = resp.json()
    # Verify that the incremental_recovery in the response originates from the result
    incr = body["results"]["incremental_recovery"]
    assert incr == str(mock_result.incremental_recovery)


def test_post_evaluation_run_invalid_cohort_size(client):
    resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 0})
    assert resp.status_code == 422


def test_post_evaluation_run_cohort_too_large(client):
    resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 99999})
    assert resp.status_code == 422


def test_post_evaluation_run_error_returns_500(client):
    with patch("app.api.routes.evaluation.run_evaluation", side_effect=RuntimeError("boom")):
        resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 100})
    assert resp.status_code == 500
    assert "boom" in resp.json()["detail"]


# ── POST /evaluation/run/multi-seed ───────────────────────────────────────────

def test_post_multi_seed_returns_200(client):
    mock_results = [_make_run_result(seed=s) for s in [42, 123, 456]]
    with patch("app.api.routes.evaluation.run_multi_seed_evaluation", return_value=mock_results):
        resp = client.post("/evaluation/run/multi-seed", json={"cohort_size": 100, "seeds": [42, 123, 456]})
    assert resp.status_code == 200


def test_post_multi_seed_returns_runs_and_summary(client):
    mock_results = [_make_run_result(seed=s) for s in [42, 123, 456]]
    with patch("app.api.routes.evaluation.run_multi_seed_evaluation", return_value=mock_results):
        resp = client.post("/evaluation/run/multi-seed", json={"cohort_size": 100, "seeds": [42, 123, 456]})
    body = resp.json()
    assert "runs" in body
    assert "summary" in body
    assert len(body["runs"]) == 3


def test_post_multi_seed_empty_seeds_returns_400(client):
    resp = client.post("/evaluation/run/multi-seed", json={"cohort_size": 100, "seeds": []})
    assert resp.status_code == 400


# ── GET /evaluation/run/{run_id} ───────────────────────────────────────────────

def test_get_evaluation_run_found(client):
    stored = {
        "run_id": "eval_42_3000",
        "seed": 42,
        "cohort_size": 3000,
        "status": "completed",
        "results": {},
    }
    with patch("app.api.routes.evaluation.get_run_from_db", return_value=stored):
        resp = client.get("/evaluation/run/eval_42_3000")
    assert resp.status_code == 200
    assert resp.json()["run_id"] == "eval_42_3000"


def test_get_evaluation_run_not_found(client):
    with patch("app.api.routes.evaluation.get_run_from_db", return_value=None):
        resp = client.get("/evaluation/run/nonexistent")
    assert resp.status_code == 404


# ── GET /evaluation/runs ───────────────────────────────────────────────────────

def test_get_evaluation_runs_returns_list():
    """
    /evaluation/runs requires a DB session.
    Override FastAPI dependency for isolation.
    """
    from app.main import app as fastapi_app
    from app.db.session import get_db

    mock_db = MagicMock()
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with TestClient(fastapi_app) as c:
            resp = c.get("/evaluation/runs")
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        fastapi_app.dependency_overrides.clear()


# ── Metric field contracts ─────────────────────────────────────────────────────

def test_policy_result_fields_in_response(client):
    mock_result = _make_run_result()
    with patch("app.api.routes.evaluation.run_evaluation", return_value=mock_result):
        resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 100})
    kp = resp.json()["results"]["khaatapulse"]
    required_fields = [
        "policy_name", "recovered_amount", "total_at_risk_amount",
        "recovery_rate", "contacts_sent", "contacts_avoided",
        "human_escalations", "false_positives", "policy_blocks",
        "cases_evaluated", "llm_fallback_count",
    ]
    for field in required_fields:
        assert field in kp, f"Missing field: {field}"


def test_recovered_amount_is_string_in_response(client):
    """Decimal amounts must be serialized as strings to avoid floating-point loss."""
    mock_result = _make_run_result()
    with patch("app.api.routes.evaluation.run_evaluation", return_value=mock_result):
        resp = client.post("/evaluation/run", json={"seed": 42, "cohort_size": 100})
    kp = resp.json()["results"]["khaatapulse"]
    assert isinstance(kp["recovered_amount"], str)
