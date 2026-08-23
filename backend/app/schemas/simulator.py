"""
API schemas for the simulator endpoint.

These schemas contain ONLY observable information.
Hidden state (CustomerLatentState) and potential outcomes (PotentialOutcomes)
must NEVER appear in these models.
"""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SimulationGenerateRequest(BaseModel):
    cohort_size: int = Field(default=3000, ge=1, le=10000)
    seed: int = Field(default=42)


class SimulationGenerateResponse(BaseModel):
    """
    Response from POST /simulation/generate.

    Contains only run metadata — no customer data, no hidden outcomes.
    Customer data is available via future observable-customer API endpoints.
    """
    simulation_run_id: int
    seed: int
    cohort_size: int
    simulator_version: str
    status: str
    customer_count: int
    event_count: int
    payment_count: int
    duration_seconds: float


class SimulationRunResponse(BaseModel):
    """Summary of a completed simulation run."""
    id: int
    seed: int
    cohort_size: int
    simulator_version: str
    status: str
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
