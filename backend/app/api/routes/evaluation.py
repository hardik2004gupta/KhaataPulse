"""
Evaluation API — CLAUDE.md §20, §30.

POST /evaluation/run   → trigger evaluation run (sync for MVP)
GET  /evaluation/{run_id} → retrieve results

Evaluation runs synchronously for MVP simplicity.
The route returns run_id + status immediately; results are in the same response
since we run synchronously. The contract supports future async migration.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.evaluation.runner import get_run_from_db, run_evaluation, run_multi_seed_evaluation, REQUIRED_SEEDS
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluationRunRequest(BaseModel):
    cohort_size: int = Field(default=3000, gt=0, le=10000)
    seed: int = Field(default=42)


class MultiSeedRequest(BaseModel):
    cohort_size: int = Field(default=3000, gt=0, le=10000)
    seeds: list[int] = Field(default=REQUIRED_SEEDS)


@router.post("/run")
def trigger_evaluation_run(
    request: EvaluationRunRequest,
    db: Session = Depends(get_db),
):
    """
    POST /evaluation/run

    Triggers a synchronous evaluation run for one seed.
    Returns run_id, status, and full results.

    CLAUDE.md §30: returns evaluation_run_id and status.
    For MVP, runs synchronously and returns completed results in one response.
    """
    try:
        result = run_evaluation(
            seed=request.seed,
            cohort_size=request.cohort_size,
            db=db,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(
            "evaluation_api_error",
            extra={"kp_seed": request.seed, "kp_error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {exc}",
        )

    return {
        "run_id": result.run_id,
        "status": "completed",
        "results": result.as_dict(),
    }


@router.post("/run/multi-seed")
def trigger_multi_seed_evaluation(
    request: MultiSeedRequest,
    db: Session = Depends(get_db),
):
    """
    POST /evaluation/run/multi-seed

    Runs evaluation for multiple seeds independently.
    Each seed produces an independently persisted result.
    Required seeds per CLAUDE.md §17: 42, 123, 456.
    """
    if not request.seeds:
        raise HTTPException(status_code=400, detail="seeds must be non-empty")

    try:
        results = run_multi_seed_evaluation(
            cohort_size=request.cohort_size,
            seeds=request.seeds,
            db=db,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-seed evaluation failed: {exc}",
        )

    from app.evaluation.runner import get_multi_seed_summary
    summary = get_multi_seed_summary(results)

    return {
        "runs": [r.as_dict() for r in results],
        "summary": summary,
    }


@router.get("/run/{run_id}")
def get_evaluation_run(
    run_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /evaluation/run/{run_id}

    Retrieve a completed evaluation run from persistence.
    Results originate from stored evaluation data — no hardcoded metrics.
    """
    run_data = get_run_from_db(run_id=run_id, db=db)
    if run_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found",
        )
    return run_data


@router.get("/runs")
def list_evaluation_runs(
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """List recent evaluation runs."""
    from app.db.models.evaluation import EvaluationRun
    runs = (
        db.query(EvaluationRun)
        .order_by(EvaluationRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "run_id": r.run_id,
            "seed": r.seed,
            "cohort_size": r.cohort_size,
            "status": r.status,
            "simulator_version": r.simulator_version,
            "model_version": r.model_version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in runs
    ]
