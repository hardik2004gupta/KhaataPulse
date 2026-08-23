"""
Risk Service — ties together FeatureBuilder, RiskPredictor, and routing.
CLAUDE.md §8: routing threshold is configuration-driven (never scattered as 0.30).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from app.core.config import get_settings
from app.risk.model import RiskPrediction, get_risk_predictor


class RoutingDecision(str, Enum):
    STANDARD_FLOW = "standard_flow"
    LANGGRAPH = "langgraph"


@dataclass(frozen=True)
class RiskAssessment:
    prediction: RiskPrediction
    routing: RoutingDecision
    threshold_used: float


class RiskService:
    """
    Entry point for risk scoring.

    Takes ObservableCustomerData; returns RiskAssessment containing the
    prediction and the routing decision. Never receives hidden state.
    """

    def __init__(self, threshold: float | None = None) -> None:
        settings = get_settings()
        self._threshold = threshold if threshold is not None else settings.risk_threshold

    def assess(
        self,
        obs,                                    # ObservableCustomerData
        reference_date: datetime | None = None,
    ) -> RiskAssessment:
        predictor = get_risk_predictor()
        prediction = predictor.predict(obs, reference_date=reference_date)
        routing = (
            RoutingDecision.LANGGRAPH
            if prediction.risk_score >= self._threshold
            else RoutingDecision.STANDARD_FLOW
        )
        return RiskAssessment(
            prediction=prediction,
            routing=routing,
            threshold_used=self._threshold,
        )
