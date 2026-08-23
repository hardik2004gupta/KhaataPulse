"""
Structured output contract - CLAUDE.md §11.

RecoveryProposal is the ONLY representation of an LLM-generated recovery
recommendation. Every LLM response must validate against this schema before
it may proceed downstream.
"""
from typing import Literal

from pydantic import BaseModel, Field


class RecoveryProposal(BaseModel):
    cause: Literal[
        "billing_migration",
        "temporary_cash_flow",
        "card_expired",
        "price_friction",
        "churn_intent",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    proposed_action: Literal[
        "silent_retry",
        "smart_link",
        "grace_period",
        "human_escalation",
        "suppress",
    ]
    rationale: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
