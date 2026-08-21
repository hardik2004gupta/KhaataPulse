"""
LLM provider abstraction — CLAUDE.md §22, §18, §19.

BaseReasoningModel is the interface the LangGraph graph depends on.
Two implementations:
  - AnthropicReasoningModel  — real Anthropic API (production)
  - StubReasoningModel       — deterministic fake (tests, demo, CI)

The graph never depends on provider-specific code.
The LLM input (ReasoningContext) contains ONLY observable fields —
no latent state, no potential outcomes, no hidden probabilities.
"""
from __future__ import annotations

import json
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from app.agent.schemas import RecoveryProposal


# ── Observable-only context passed to the LLM ────────────────────────────────

@dataclass(frozen=True)
class ReasoningContext:
    """
    The ONLY data the LLM may receive.

    All fields derive from observable customer data.
    No field here corresponds to CustomerLatentState,
    PotentialOutcomes, or any hidden simulator variable.
    """
    customer_id: int
    risk_score: float
    risk_level: str                    # LOW | MEDIUM | HIGH
    risk_signals: list[dict]           # [{"feature": ..., "impact": ...}]
    subscription_info: dict            # plan, amount, currency, renewal_at
    payment_failures: list[dict]       # observable failed payments (no probabilities)
    observable_events: list[dict]      # event_type + observable payload
    support_messages: list[str]        # extracted support message text


# ── Abstract interface ────────────────────────────────────────────────────────

class BaseReasoningModel(ABC):
    @abstractmethod
    def reason(self, context: ReasoningContext) -> RecoveryProposal:
        """
        Accepts observable context; returns a validated RecoveryProposal.
        Must raise an exception on any failure (provider error, validation error, etc.).
        The caller (graph node) is responsible for fallback.
        """


# ── Deterministic stub (tests / demo / CI) ────────────────────────────────────

class StubReasoningModel(BaseReasoningModel):
    """
    Returns deterministic proposals without calling any external API.
    Used in tests and demo mode to avoid network dependency.

    Proposal logic is rule-based on observable signals only.
    """

    def reason(self, context: ReasoningContext) -> RecoveryProposal:
        # Derive cause from observable event types
        event_types = {e.get("event_type") for e in context.observable_events}

        if "payment_method_changed" in event_types:
            cause = "card_expired"
            action = "smart_link"
            rationale = (
                "Payment method change detected. Providing a smart payment link "
                "to complete the renewal with the updated payment details."
            )
        elif "subscription_changed" in event_types:
            cause = "churn_intent"
            action = "grace_period"
            rationale = (
                "Subscription change event indicates potential churn intent. "
                "Offering a grace period to retain the customer."
            )
        elif context.risk_score >= 0.70:
            cause = "temporary_cash_flow"
            action = "human_escalation"
            rationale = (
                "High risk score with support contact history. "
                "Escalating to a human agent for personalised resolution."
            )
        elif any("support" in e.get("event_type", "") for e in context.observable_events):
            cause = "temporary_cash_flow"
            action = "grace_period"
            rationale = (
                "Customer has raised a support query. "
                "Extending a grace period while the issue is resolved."
            )
        else:
            cause = "temporary_cash_flow"
            action = "silent_retry"
            rationale = (
                "Observable risk signals suggest a transient payment difficulty. "
                "Initiating a silent retry."
            )

        risk_level = context.risk_level if context.risk_level in ("LOW", "MEDIUM", "HIGH") else "MEDIUM"
        confidence = min(0.95, max(0.55, context.risk_score + 0.15))

        return RecoveryProposal(
            cause=cause,
            confidence=round(confidence, 2),
            proposed_action=action,
            rationale=rationale,
            risk_level=risk_level,
        )


# ── Anthropic implementation (production) ────────────────────────────────────

class AnthropicReasoningModel(BaseReasoningModel):
    """
    Uses the Anthropic Messages API for structured LLM reasoning.

    Sends only observable context to the LLM (CLAUDE.md §18).
    Uses tool_use to enforce structured output (CLAUDE.md §19).
    Raises on any failure — the graph node handles fallback.
    """

    def __init__(self, api_key: str, model: str) -> None:
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def reason(self, context: ReasoningContext) -> RecoveryProposal:
        import anthropic

        prompt = self._build_prompt(context)
        tool_definition = self._recovery_tool()

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            tools=[tool_definition],
            tool_choice={"type": "any"},
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract tool use block
        tool_use_block = next(
            (b for b in response.content if b.type == "tool_use"),
            None,
        )
        if tool_use_block is None:
            raise ValueError("LLM did not return a tool_use block")

        raw: dict = tool_use_block.input
        return RecoveryProposal.model_validate(raw)

    def _build_prompt(self, ctx: ReasoningContext) -> str:
        events_summary = "\n".join(
            f"  - {e.get('event_type', 'unknown')}: {json.dumps({k: v for k, v in e.items() if k != 'event_type'})}"
            for e in ctx.observable_events
        )
        signals_summary = "\n".join(
            f"  - {s['feature']}: impact={s['impact']:.3f}"
            for s in ctx.risk_signals
        )
        failures_summary = (
            "\n".join(
                f"  - {p.get('status', '?')} via {p.get('payment_method', '?')}: code={p.get('failure_code', 'N/A')}"
                for p in ctx.payment_failures
            ) or "  (none)"
        )
        support_text = "\n".join(f"  \"{m}\"" for m in ctx.support_messages) or "  (none)"

        return textwrap.dedent(f"""
            You are a payment recovery analyst for KhaataPulse.
            Analyse the following observable subscription renewal risk case and
            propose a contextually appropriate recovery action.

            Customer ID: {ctx.customer_id}
            Risk Score: {ctx.risk_score:.2f}  ({ctx.risk_level})

            Top risk signals (from logistic regression model):
            {signals_summary}

            Subscription: {json.dumps(ctx.subscription_info)}

            Payment failure history:
            {failures_summary}

            Observable events (chronological):
            {events_summary}

            Support messages:
            {support_text}

            Based on this observable data only, provide your diagnosis and
            recovery proposal using the recovery_proposal tool.
        """).strip()

    @staticmethod
    def _recovery_tool() -> dict:
        return {
            "name": "recovery_proposal",
            "description": (
                "Submit a structured payment recovery proposal based on observable "
                "customer signals. All fields are required."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "cause": {
                        "type": "string",
                        "enum": [
                            "billing_migration",
                            "temporary_cash_flow",
                            "card_expired",
                            "price_friction",
                            "churn_intent",
                        ],
                        "description": "Root cause of the payment friction.",
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence in the diagnosis (0–1).",
                    },
                    "proposed_action": {
                        "type": "string",
                        "enum": [
                            "silent_retry",
                            "smart_link",
                            "grace_period",
                            "human_escalation",
                            "suppress",
                        ],
                        "description": "Recommended recovery intervention.",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Brief explanation of the diagnosis and action choice.",
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH"],
                        "description": "Contextual risk assessment.",
                    },
                },
                "required": ["cause", "confidence", "proposed_action", "rationale", "risk_level"],
            },
        }


# ── Factory ───────────────────────────────────────────────────────────────────

def get_reasoning_model() -> BaseReasoningModel:
    """
    Returns AnthropicReasoningModel if LLM_API_KEY is configured,
    StubReasoningModel otherwise (demo / CI mode).
    """
    from app.core.config import get_settings
    settings = get_settings()
    if settings.llm_api_key:
        return AnthropicReasoningModel(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    return StubReasoningModel()
