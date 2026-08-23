"""
Evaluation runner - multi-seed orchestration and persistence - CLAUDE.md §17.

EvaluationRunner:
  - Accepts seed + cohort_size
  - Creates EvaluationRun record (queued)
  - Runs same-cohort evaluation
  - Persists EvaluationResult per policy
  - Returns EvaluationRunResult

Multi-seed validation:
  - Required seeds: 42, 123, 456 (CLAUDE.md §17)
  - Recommended: 789, 1337
  - Each seed produces an independent run with independently persisted results

Performance: evaluation_duration is recorded in run metadata.
Errors: single customer failures do not terminate the batch.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models.evaluation import EvaluationRun, EvaluationResult
from app.evaluation.evaluator import run_same_cohort_evaluation
from app.evaluation.metrics import EvaluationRunResult, PolicyEvaluationResult
from app.evaluation.policies import (
    STATIC_DUNNING_VERSION,
    SMART_RETRY_VERSION,
    KHAATAPULSE_VERSION,
)
from app.risk.model import MODEL_VERSION

logger = get_logger(__name__)

# Seeds required by CLAUDE.md §17
REQUIRED_SEEDS = [42, 123, 456]
# Recommended additional seeds
RECOMMENDED_SEEDS = [789, 1337]


def _make_run_id(seed: int, cohort_size: int) -> str:
    return f"eval_{seed}_{cohort_size}"


def run_evaluation(
    seed: int,
    cohort_size: int,
    db: Optional[Session] = None,
) -> EvaluationRunResult:
    """
    Execute a complete evaluation run for one seed.

    Creates/updates an EvaluationRun record and persists per-policy EvaluationResult
    records. If db is None, runs without persistence (test/demo mode).

    Returns EvaluationRunResult with all three policies and incremental recovery.
    """
    settings = get_settings()
    run_id = _make_run_id(seed, cohort_size)

    # ── Create run record (status: running) ───────────────────────────────────
    policy_version = f"{STATIC_DUNNING_VERSION},{SMART_RETRY_VERSION},{KHAATAPULSE_VERSION}"

    if db is not None:
        existing = db.query(EvaluationRun).filter_by(run_id=run_id).first()
        if existing is not None:
            run_record = existing
            run_record.status = "running"
            run_record.started_at = datetime.now(timezone.utc)
        else:
            run_record = EvaluationRun(
                run_id=run_id,
                seed=seed,
                cohort_size=cohort_size,
                simulator_version=settings.simulator_version,
                model_version=MODEL_VERSION,
                policy_version=policy_version,
                status="running",
                started_at=datetime.now(timezone.utc),
            )
            db.add(run_record)
        db.flush()

    start_time = time.monotonic()

    try:
        result = run_same_cohort_evaluation(
            seed=seed,
            cohort_size=cohort_size,
            simulator_version=settings.simulator_version,
            run_id=run_id,
        )
    except Exception as exc:
        if db is not None:
            run_record.status = "failed"
            run_record.error_message = str(exc)[:500]
            run_record.completed_at = datetime.now(timezone.utc)
            db.flush()
        logger.error(
            "evaluation_failed",
            extra={"kp_run_id": run_id, "kp_error": str(exc)},
        )
        raise

    duration_seconds = time.monotonic() - start_time

    # ── Persist results ───────────────────────────────────────────────────────
    if db is not None:
        # Remove any existing results for this run (re-run case)
        db.query(EvaluationResult).filter_by(run_id=run_id).delete()
        db.flush()

        for policy_result in [result.static_dunning, result.smart_retry, result.khaatapulse]:
            eval_result = EvaluationResult(
                run_id=run_id,
                policy_name=policy_result.policy_name,
                recovered_amount=policy_result.recovered_amount,
                total_at_risk_amount=policy_result.total_at_risk_amount,
                incremental_recovery=policy_result.incremental_recovery,
                recovery_rate=Decimal(str(round(policy_result.recovery_rate, 8))),
                contacts_sent=policy_result.contacts_sent,
                contacts_avoided=policy_result.contacts_avoided,
                human_escalations=policy_result.human_escalations,
                false_positives=policy_result.false_positives,
                policy_blocks=policy_result.policy_blocks,
                cases_evaluated=policy_result.cases_evaluated,
                llm_fallback_count=policy_result.llm_fallback_count,
            )
            db.add(eval_result)

        run_record.status = "completed"
        run_record.completed_at = datetime.now(timezone.utc)
        db.flush()

    logger.info(
        "evaluation_persisted",
        extra={
            "kp_run_id": run_id,
            "kp_seed": seed,
            "kp_cohort_size": cohort_size,
            "kp_duration_seconds": round(duration_seconds, 2),
            "kp_incremental_recovery": str(result.incremental_recovery),
        },
    )

    return result


def run_multi_seed_evaluation(
    cohort_size: int,
    seeds: Optional[list[int]] = None,
    db: Optional[Session] = None,
) -> list[EvaluationRunResult]:
    """
    Run evaluation for multiple seeds independently.
    Each seed produces an independently persisted result.

    Default seeds: 42, 123, 456 (required by CLAUDE.md §17).
    """
    if seeds is None:
        seeds = REQUIRED_SEEDS

    results = []
    for seed in seeds:
        result = run_evaluation(seed=seed, cohort_size=cohort_size, db=db)
        results.append(result)

    return results


def get_multi_seed_summary(results: list[EvaluationRunResult]) -> dict:
    """
    Produce a structured summary of multi-seed results for the frontend.
    All values are dynamically calculated - no hardcoded numbers.
    """
    positive_runs = sum(1 for r in results if r.incremental_recovery > 0)
    total_runs = len(results)

    return {
        "total_runs": total_runs,
        "positive_runs": positive_runs,
        "negative_runs": total_runs - positive_runs,
        "seeds": [
            {
                "seed": r.seed,
                "run_id": r.run_id,
                "incremental_recovery": str(r.incremental_recovery),
                "khaatapulse_recovered": str(r.khaatapulse.recovered_amount),
                "smart_retry_recovered": str(r.smart_retry.recovered_amount),
                "is_positive": r.incremental_recovery > 0,
            }
            for r in results
        ],
    }


def get_run_from_db(run_id: str, db: Session) -> Optional[dict]:
    """
    Retrieve a completed evaluation run from DB.

    Returns the same shape as EvaluationRunResult.as_dict() wrapped in an outer
    envelope {run_id, status, results} - matching the POST /evaluation/run response
    so the frontend can use the same type for both GET and POST.
    """
    run = db.query(EvaluationRun).filter_by(run_id=run_id).first()
    if run is None:
        return None

    db_results = {r.policy_name: r for r in run.results}

    def _policy_dict(r) -> dict:
        return {
            "policy_name": r.policy_name,
            "policy_version": r.policy_version if hasattr(r, "policy_version") else "",
            "recovered_amount": str(r.recovered_amount),
            "total_at_risk_amount": str(r.total_at_risk_amount),
            "recovery_rate": float(r.recovery_rate),
            "incremental_recovery": str(r.incremental_recovery) if r.incremental_recovery is not None else None,
            "contacts_sent": r.contacts_sent,
            "contacts_avoided": r.contacts_avoided,
            "human_escalations": r.human_escalations,
            "false_positives": r.false_positives,
            "policy_blocks": r.policy_blocks,
            "cases_evaluated": r.cases_evaluated,
            "llm_fallback_count": r.llm_fallback_count,
        }

    incremental_recovery = (
        str(db_results["khaatapulse"].incremental_recovery)
        if "khaatapulse" in db_results and db_results["khaatapulse"].incremental_recovery is not None
        else "0"
    )

    # Build results dict matching EvaluationRunResult.as_dict() - same shape as POST response
    results_dict = {
        "run_id": run.run_id,
        "seed": run.seed,
        "cohort_size": run.cohort_size,
        "simulator_version": run.simulator_version,
        "model_version": run.model_version,
        "policy_version": run.policy_version,
        "incremental_recovery": incremental_recovery,
        "static_dunning": _policy_dict(db_results["static_dunning"]) if "static_dunning" in db_results else {},
        "smart_retry": _policy_dict(db_results["smart_retry"]) if "smart_retry" in db_results else {},
        "khaatapulse": _policy_dict(db_results["khaatapulse"]) if "khaatapulse" in db_results else {},
    }

    return {
        "run_id": run.run_id,
        "status": run.status,
        "results": results_dict,
    }
