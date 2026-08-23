"""
Recovery policy implementations - CLAUDE.md §18, §32.

Three policies all implement the same RecoveryPolicy interface so the evaluator
can swap them against the same world without changing evaluation logic.

ISOLATION:
  All three policy.decide() calls receive ObservableCustomerData only.
  No policy may receive latent_state or PotentialOutcomes.
  The evaluator (not the policy) uses PotentialOutcomes to compute outcomes.

Policy versions used for reproducibility tracking.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.simulator.world import ObservableCustomerData

# Version constants for reproducibility
STATIC_DUNNING_VERSION = "static-dunning-v1"
SMART_RETRY_VERSION = "smart-retry-v1"
KHAATAPULSE_VERSION = "khaatapulse-v1"


# ── Base interface ────────────────────────────────────────────────────────────

class RecoveryPolicy(ABC):
    """
    Policy interface - receives observable data, returns action type.
    No policy may receive latent state or potential outcomes.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @abstractmethod
    def decide(self, obs: ObservableCustomerData) -> str:
        """
        Returns one of: no_action, silent_retry, smart_link, grace_period,
                        human_escalation, suppress
        Based exclusively on observable customer data.
        """
        ...

    def reset(self) -> None:
        """Called at the start of each evaluation run to reset any per-run state."""
        pass


# ── Static Dunning - CLAUDE.md §18 ───────────────────────────────────────────

class StaticDunningPolicy(RecoveryPolicy):
    """
    Baseline: payment_failure → 24h retry → reminder → human_escalation.
    No risk model. No LLM. No cause analysis. Pure rule-based dunning.

    Evaluation mapping (based on observable failure history):
      0 failures  → no_action (no dunning triggered)
      1 failure   → silent_retry (24h retry step)
      2+ failures → human_escalation (escalation step)
    """

    @property
    def name(self) -> str:
        return "static_dunning"

    @property
    def version(self) -> str:
        return STATIC_DUNNING_VERSION

    def decide(self, obs: ObservableCustomerData) -> str:
        historical = [p for p in obs.payments if p.status != "pending"]
        failed = [p for p in historical if p.status == "failed"]

        if not failed:
            return "no_action"
        if len(failed) >= 2:
            return "human_escalation"
        return "silent_retry"


# ── Smart Retry - CLAUDE.md §18 ──────────────────────────────────────────────

class SmartRetryPolicy(RecoveryPolicy):
    """
    Second baseline: failure-code rules → deterministic retry timing → payment_link → escalation.
    Deterministic. No LLM. No KhaataPulse risk model. No ENR.

    Failure-code mapping (observable):
      card_expired / invalid_card / card_blocked / wallet_limit_exceeded → smart_link
      insufficient_funds / insufficient_balance                          → grace_period
      upi_timeout / session_expired / bank_declined / other              → silent_retry
      No failures                                                        → no_action
    """

    _SMART_LINK_CODES = frozenset({
        "card_expired", "invalid_card", "card_blocked", "wallet_limit_exceeded"
    })
    _GRACE_CODES = frozenset({
        "insufficient_funds", "insufficient_balance"
    })

    @property
    def name(self) -> str:
        return "smart_retry"

    @property
    def version(self) -> str:
        return SMART_RETRY_VERSION

    def decide(self, obs: ObservableCustomerData) -> str:
        historical = [p for p in obs.payments if p.status != "pending"]
        failed = [p for p in historical if p.status == "failed"]

        if not failed:
            return "no_action"

        # Use most recent failure code
        latest_failure = max(failed, key=lambda p: p.created_at)
        code = latest_failure.failure_code or ""

        if code in self._SMART_LINK_CODES:
            return "smart_link"
        if code in self._GRACE_CODES:
            return "grace_period"
        # Repeated failures with no actionable code → escalate
        if len(failed) >= 3:
            return "human_escalation"
        return "silent_retry"


# ── KhaataPulse - CLAUDE.md §18 ──────────────────────────────────────────────

class KhaataPulsePolicy(RecoveryPolicy):
    """
    Full KhaataPulse pipeline: Risk Sieve → LangGraph → Optimizer → Policy Guard.

    Evaluation mode uses StubReasoningModel (deterministic, no LLM API calls)
    and skips DB writes (Policy Guard runs in no-db mode).

    Decision path:
      risk_score < threshold  → no_action
      risk_score >= threshold → stub diagnosis → optimizer → policy_guard
        BLOCKED    → no_action
        ESCALATED  → human_escalation
        APPROVED   → selected_action
    """

    def __init__(self) -> None:
        from app.risk.model import get_risk_predictor, TRAINING_REFERENCE_DATE
        from app.agent.reasoning import StubReasoningModel
        self._predictor = get_risk_predictor()
        self._reference_date = TRAINING_REFERENCE_DATE
        self._stub_model = StubReasoningModel()
        self._llm_fallback_count = 0

    @property
    def name(self) -> str:
        return "khaatapulse"

    @property
    def version(self) -> str:
        return KHAATAPULSE_VERSION

    @property
    def llm_fallback_count(self) -> int:
        return self._llm_fallback_count

    def reset(self) -> None:
        self._llm_fallback_count = 0

    def decide(self, obs: ObservableCustomerData) -> str:
        from app.core.config import get_settings
        from app.risk.features import FeatureBuilder
        from app.agent.reasoning import ReasoningContext
        from app.optimizer.ranker import rank_eligible_actions
        from app.policy.guard import policy_guard, PolicyStatus

        settings = get_settings()

        # ── Risk Sieve ─────────────────────────────────────────────────────────
        prediction = self._predictor.predict(obs, reference_date=self._reference_date)
        if prediction.risk_score < settings.risk_threshold:
            return "no_action"

        # ── LangGraph stub diagnosis ───────────────────────────────────────────
        payment_failures = [
            {"status": p.status, "failure_code": p.failure_code, "payment_method": p.payment_method}
            for p in obs.payments if p.status == "failed"
        ]
        support_msgs = [
            ev.payload.get("message", "")
            for ev in obs.events if ev.event_type == "support_message"
        ]
        context = ReasoningContext(
            customer_id=obs.customer_id,
            risk_score=prediction.risk_score,
            risk_level=prediction.risk_level,
            risk_signals=[
                {"feature": s.feature, "impact": s.impact} for s in prediction.top_signals
            ],
            subscription_info={
                "plan": obs.subscription.plan,
                "amount": float(obs.subscription.amount),
                "currency": obs.subscription.currency,
            },
            payment_failures=payment_failures,
            observable_events=[
                {"event_type": ev.event_type, **ev.payload} for ev in obs.events
            ],
            support_messages=[m for m in support_msgs if m],
        )

        try:
            proposal = self._stub_model.reason(context)
        except Exception:
            self._llm_fallback_count += 1
            from app.agent.fallback import smart_retry_proposal
            proposal = smart_retry_proposal(context, "evaluation_stub_failure")
            self._llm_fallback_count += 1

        cause = proposal.cause
        proposed_action = proposal.proposed_action

        # ── Economic Optimizer ─────────────────────────────────────────────────
        from decimal import Decimal
        amount = obs.subscription.amount
        ltv = obs.ltv

        rankings = rank_eligible_actions(cause=cause, amount=amount, ltv=ltv)
        selected = rankings[0].action_type if rankings else proposed_action

        # ── Policy Guard (no DB) ───────────────────────────────────────────────
        decision = policy_guard(
            customer_id=obs.customer_id,
            action_type=selected,
            amount=amount,
            idempotency_key=f"eval_{obs.customer_id}",
            dispute_hold=False,
            legal_hold=False,
            opt_out=False,
            db=None,
        )

        if decision.status == PolicyStatus.BLOCKED:
            return "blocked"  # tracked separately
        elif decision.status == PolicyStatus.ESCALATED:
            return "human_escalation"
        else:
            return selected
