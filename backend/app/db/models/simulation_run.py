"""
Simulator-internal tables.

SimulationRun  — tracks a world generation run for reproducibility.
SimulatorOutcome — stores P(payment|action) and P(churn|action) per customer.

ARCHITECTURE BOUNDARY: These tables are owned exclusively by the simulator module.
No other module (agent, API, frontend) may read from SimulatorOutcome directly.
The evaluation harness (Phase 4) will access outcomes via the simulator service only.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SimulationRun(Base):
    __tablename__ = "sim_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed = Column(Integer, nullable=False)
    cohort_size = Column(Integer, nullable=False)
    simulator_version = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="generating")  # generating, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    outcomes = relationship("SimulatorOutcome", back_populates="simulation_run")


class SimulatorOutcome(Base):
    """
    Hidden potential outcomes — NEVER exposed to the agent or observable API.
    Used only by the evaluation harness to compute policy performance.

    Stores P(payment | action) and P(churn | action) for each customer × action pair.
    """
    __tablename__ = "sim_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_run_id = Column(Integer, ForeignKey("sim_runs.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)   # no_action, silent_retry, smart_link, grace_period, human_escalation
    p_payment = Column(Numeric(6, 4), nullable=False)  # P(payment | action)
    p_churn = Column(Numeric(6, 4), nullable=False)    # P(churn | action)

    simulation_run = relationship("SimulationRun", back_populates="outcomes")

    __table_args__ = (
        UniqueConstraint("simulation_run_id", "customer_id", "action_type", name="uq_sim_outcome"),
    )
