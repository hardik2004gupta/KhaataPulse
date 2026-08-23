"""
Evaluation persistence models — CLAUDE.md §17, §19.

EvaluationRun    — one run = one world generation + all three policy evaluations.
EvaluationResult — per-policy metrics within a run.

Every run stores: run_id, seed, cohort_size, simulator_version, model_version,
policy_version, and all required metrics.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), nullable=False, unique=True, index=True)  # e.g. eval_42_3000
    seed = Column(Integer, nullable=False)
    cohort_size = Column(Integer, nullable=False)
    simulator_version = Column(String(20), nullable=False)
    model_version = Column(String(50), nullable=False)
    policy_version = Column(String(200), nullable=False)  # comma-separated policy versions
    status = Column(String(20), nullable=False, default="queued")  # queued|running|completed|failed
    error_message = Column(String(500), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    results = relationship("EvaluationResult", back_populates="run", order_by="EvaluationResult.policy_name")


class EvaluationResult(Base):
    """Per-policy metrics for one evaluation run."""
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
                   nullable=False, index=True)
    policy_name = Column(String(50), nullable=False)        # static_dunning | smart_retry | khaatapulse

    # Monetary metrics (Numeric for precision)
    recovered_amount = Column(Numeric(14, 4), nullable=False)
    total_at_risk_amount = Column(Numeric(14, 4), nullable=False)
    incremental_recovery = Column(Numeric(14, 4), nullable=True)  # vs smart_retry baseline

    # Rate metrics
    recovery_rate = Column(Numeric(8, 6), nullable=False)   # [0.0, 1.0]

    # Contact metrics
    contacts_sent = Column(Integer, nullable=False)
    contacts_avoided = Column(Integer, nullable=False)      # cohort_size - contacts_sent
    human_escalations = Column(Integer, nullable=False)

    # Quality metrics
    false_positives = Column(Integer, nullable=False)
    policy_blocks = Column(Integer, nullable=False)
    cases_evaluated = Column(Integer, nullable=False)
    llm_fallback_count = Column(Integer, nullable=False, default=0)

    run = relationship("EvaluationRun", back_populates="results")
