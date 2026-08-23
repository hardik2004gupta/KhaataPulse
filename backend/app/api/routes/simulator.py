"""
Simulator API routes.

POST /simulation/generate - trigger world generation and persistence.
GET  /simulation/runs     - list completed simulation runs.

IMPORTANT: Responses MUST NOT contain latent state or potential outcomes.
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.db.models.simulation_run import SimulationRun
from app.schemas.simulator import (
    SimulationGenerateRequest,
    SimulationGenerateResponse,
    SimulationRunResponse,
)
from app.simulator.generator import generate_world
from app.simulator.world import WorldInternal
from app.simulator.persistence import persist_world

router = APIRouter(prefix="/simulation", tags=["simulation"])
settings = get_settings()


@router.post("/generate", response_model=SimulationGenerateResponse)
def generate_simulation(
    request: SimulationGenerateRequest,
    db: Session = Depends(get_db),
) -> SimulationGenerateResponse:
    """
    Generate and persist a synthetic customer world.

    The response contains only run metadata - no customer data, no hidden outcomes.
    """
    t_start = time.time()

    reference_date = datetime.now(timezone.utc)
    raw_records = generate_world(
        seed=request.seed,
        cohort_size=request.cohort_size,
        simulator_version=settings.simulator_version,
        reference_date=reference_date,
    )

    world = WorldInternal.from_raw_records(
        raw=raw_records,
        seed=request.seed,
        cohort_size=request.cohort_size,
        simulator_version=settings.simulator_version,
        reference_date=reference_date,
    )

    run = persist_world(db, world)

    event_count = sum(len(r["events"]) for r in raw_records)
    payment_count = sum(len(r["payments"]) for r in raw_records)

    return SimulationGenerateResponse(
        simulation_run_id=run.id,
        seed=request.seed,
        cohort_size=request.cohort_size,
        simulator_version=settings.simulator_version,
        status=run.status,
        customer_count=len(raw_records),
        event_count=event_count,
        payment_count=payment_count,
        duration_seconds=round(time.time() - t_start, 2),
    )


@router.get("/runs", response_model=list[SimulationRunResponse])
def list_simulation_runs(
    db: Session = Depends(get_db),
    limit: int = 20,
) -> list[SimulationRun]:
    """List recent simulation runs for reproducibility tracking."""
    return (
        db.query(SimulationRun)
        .order_by(SimulationRun.created_at.desc())
        .limit(limit)
        .all()
    )
