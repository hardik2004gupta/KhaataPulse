"""
Evaluation result models — CLAUDE.md §17, §32.

PolicyEvaluationResult  — metrics for one policy in one evaluation run.
EvaluationRunResult     — all three policies + incremental recovery for one run.

No values may be hardcoded. All fields originate from actual evaluator output.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class PolicyEvaluationResult:
    """Metrics for one policy evaluated against one cohort. CLAUDE.md §17."""
    policy_name: str
    policy_version: str

    # Monetary — using Decimal for precision
    recovered_amount: Decimal          # Σ P(payment|action) × subscription_amount
    total_at_risk_amount: Decimal      # Σ subscription_amount for entire cohort

    # Rate — recovered_amount / total_at_risk_amount
    recovery_rate: float               # in [0.0, 1.0]

    # Contact metrics
    contacts_sent: int                 # customers where action ∉ {no_action, suppress}
    contacts_avoided: int              # cohort_size - contacts_sent
    human_escalations: int

    # Quality metrics
    false_positives: int               # triggered on customers who would have paid anyway
    policy_blocks: int                 # Policy Guard BLOCKED decisions
    cases_evaluated: int               # total customers in cohort
    llm_fallback_count: int = 0        # LLM failures that triggered fallback

    # Computed after comparison (set by EvaluationRunResult)
    incremental_recovery: Optional[Decimal] = None  # vs smart_retry

    def as_dict(self) -> dict:
        return {
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "recovered_amount": str(self.recovered_amount),
            "total_at_risk_amount": str(self.total_at_risk_amount),
            "recovery_rate": float(self.recovery_rate),
            "incremental_recovery": str(self.incremental_recovery) if self.incremental_recovery is not None else None,
            "contacts_sent": self.contacts_sent,
            "contacts_avoided": self.contacts_avoided,
            "human_escalations": self.human_escalations,
            "false_positives": self.false_positives,
            "policy_blocks": self.policy_blocks,
            "cases_evaluated": self.cases_evaluated,
            "llm_fallback_count": self.llm_fallback_count,
        }


@dataclass
class EvaluationRunResult:
    """
    Complete evaluation run result — one world, three policies.
    Primary KPI: incremental_recovery = khaatapulse - smart_retry.
    """
    run_id: str
    seed: int
    cohort_size: int
    simulator_version: str
    model_version: str
    policy_version: str

    static_dunning: PolicyEvaluationResult
    smart_retry: PolicyEvaluationResult
    khaatapulse: PolicyEvaluationResult

    # Primary KPI — CLAUDE.md §18
    incremental_recovery: Decimal      # khaatapulse.recovered - smart_retry.recovered

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "cohort_size": self.cohort_size,
            "simulator_version": self.simulator_version,
            "model_version": self.model_version,
            "policy_version": self.policy_version,
            "incremental_recovery": str(self.incremental_recovery),
            "static_dunning": self.static_dunning.as_dict(),
            "smart_retry": self.smart_retry.as_dict(),
            "khaatapulse": self.khaatapulse.as_dict(),
        }
