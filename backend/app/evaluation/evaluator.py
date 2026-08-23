"""
Same-cohort evaluation engine - CLAUDE.md §17, §32 (§58 final invariant).

ARCHITECTURE:
  1. World is generated ONCE per evaluation run.
  2. All three policies evaluate against the SAME world.
  3. The evaluator (not policies) accesses PotentialOutcomes.
  4. Policies receive ObservableCustomerData only.
  5. Outcome calculation uses ground-truth P(payment|action) × amount (expected value).

OUTCOME SEMANTICS:
  PotentialOutcomes stores P(payment|action) and P(churn|action).
  recovered_amount = Σ P(payment|action) × subscription_amount (expected value, deterministic).
  This is equivalent to sampling with the world seed - but deterministic and without noise.

FALSE POSITIVE DEFINITION:
  A KhaataPulse intervention is a false positive if:
  - KhaataPulse triggered on this customer (risk_score >= threshold), AND
  - The simulator's P(payment | no_action) >= 0.70 (customer would have paid anyway).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.evaluation.metrics import EvaluationRunResult, PolicyEvaluationResult
from app.evaluation.policies import (
    KhaataPulsePolicy,
    RecoveryPolicy,
    STATIC_DUNNING_VERSION,
    SMART_RETRY_VERSION,
    KHAATAPULSE_VERSION,
)
from app.risk.model import MODEL_VERSION, TRAINING_REFERENCE_DATE
from app.simulator.world import (
    ObservableCustomerData,
    ObservableEvent,
    ObservablePayment,
    ObservableSubscription,
    WorldInternal,
    _InternalCustomerRecord,
)
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Threshold above which no_action p_payment flags as false positive
_FALSE_POSITIVE_THRESHOLD = 0.70

# action types that map to "no_action" outcomes in PotentialOutcomes
# (PotentialOutcomes has no "suppress" or "blocked" entry)
_OUTCOME_ACTION_MAP: dict[str, str] = {
    "no_action":        "no_action",
    "suppress":         "no_action",   # suppress = don't contact = same outcome as no_action
    "blocked":          "no_action",   # policy guard blocked = no action taken
    "silent_retry":     "silent_retry",
    "smart_link":       "smart_link",
    "grace_period":     "grace_period",
    "human_escalation": "human_escalation",
}


@dataclass
class EvaluationWorld:
    """
    Wrapper around WorldInternal that provides evaluator-authorized access to
    PotentialOutcomes while keeping the boundary clear.

    Only the evaluator may call get_potential_outcomes().
    Policies receive extract_observable() output only.
    """
    world: WorldInternal

    def customer_records(self) -> list[_InternalCustomerRecord]:
        return self.world.records

    def get_potential_outcomes(self, customer_id: int):
        """Evaluator-authorized access to PotentialOutcomes. NEVER pass to policies."""
        for rec in self.world.records:
            if rec.customer_id == customer_id:
                return rec.potential_outcomes
        raise KeyError(f"Customer {customer_id} not found in evaluation world")

    def extract_observable_for(self, rec: _InternalCustomerRecord) -> ObservableCustomerData:
        """Extract observable view for a single customer (safe to pass to policies)."""
        from datetime import timezone
        sub_data = rec.subscription
        renewal_at = sub_data["renewal_at"]
        if hasattr(renewal_at, "tzinfo") and renewal_at.tzinfo is None:
            renewal_at = renewal_at.replace(tzinfo=timezone.utc)

        obs_sub = ObservableSubscription(
            plan=sub_data["plan"],
            amount=sub_data["amount"],
            currency=sub_data["currency"],
            renewal_at=renewal_at,
            status=sub_data["status"],
        )
        obs_payments = [
            ObservablePayment(
                amount=p["amount"],
                status=p["status"],
                failure_code=p["failure_code"],
                payment_method=p["payment_method"],
                created_at=p["created_at"],
            )
            for p in rec.payments
        ]
        obs_events = [
            ObservableEvent(
                event_type=e["event_type"],
                timestamp=e["timestamp"],
                payload=e["payload"],
            )
            for e in rec.events
        ]
        return ObservableCustomerData(
            customer_id=rec.customer_id,
            name=rec.name,
            segment=rec.segment,
            ltv=rec.ltv,
            subscription=obs_sub,
            payments=obs_payments,
            events=obs_events,
        )


def _policy_outcome_key(action: str) -> str:
    """Map a policy action to its PotentialOutcomes key."""
    return _OUTCOME_ACTION_MAP.get(action, "no_action")


def _is_contact_action(action: str) -> bool:
    """Return True if the action involves customer contact."""
    return action not in ("no_action", "suppress", "blocked")


def evaluate_policy_on_world(
    policy: RecoveryPolicy,
    eval_world: EvaluationWorld,
    run_id: str,
) -> PolicyEvaluationResult:
    """
    Evaluate one policy against the full evaluation world.

    Each customer's outcome is calculated using PotentialOutcomes ground-truth
    (evaluator-authorized), NOT the policy's own probability estimates.

    Uses expected-value semantics:
      recovered_amount = Σ P(payment|action) × subscription_amount
    """
    settings = get_settings()

    recovered_amount = Decimal("0")
    total_at_risk = Decimal("0")
    contacts_sent = 0
    human_escalations = 0
    false_positives = 0
    policy_blocks = 0
    llm_fallbacks = getattr(policy, "llm_fallback_count", 0)

    is_kp = policy.name == "khaatapulse"
    policy.reset()

    for rec in eval_world.customer_records():
        obs = eval_world.extract_observable_for(rec)
        amount = obs.subscription.amount
        total_at_risk += amount

        # Policy decision - receives observable data only
        try:
            action = policy.decide(obs)
        except Exception as e:
            logger.warning(
                "policy_decide_error",
                extra={
                    "kp_policy": policy.name,
                    "kp_customer_id": obs.customer_id,
                    "kp_error": str(e),
                },
            )
            action = "no_action"

        # Track contacts and escalations
        if _is_contact_action(action):
            contacts_sent += 1
        if action == "human_escalation":
            human_escalations += 1
        if action == "blocked":
            policy_blocks += 1

        # Get ground-truth outcome for the chosen action (evaluator boundary)
        outcomes = eval_world.get_potential_outcomes(obs.customer_id)
        outcome_key = _policy_outcome_key(action)
        action_outcome = outcomes.for_action(outcome_key)

        # Expected-value contribution
        recovered_amount += Decimal(str(round(action_outcome.p_payment, 8))) * amount

        # False positives: KhaataPulse triggered but customer would have paid anyway
        if is_kp and action != "no_action":
            no_action_outcome = outcomes.for_action("no_action")
            if no_action_outcome.p_payment >= _FALSE_POSITIVE_THRESHOLD:
                false_positives += 1

    cohort_size = len(eval_world.customer_records())
    contacts_avoided = cohort_size - contacts_sent

    # Recovery rate: recovered_amount / total_at_risk
    recovery_rate = float(recovered_amount / total_at_risk) if total_at_risk > 0 else 0.0

    # LLM fallback count for KhaataPulse
    if is_kp:
        llm_fallbacks = getattr(policy, "llm_fallback_count", 0)

    logger.info(
        "policy_evaluated",
        extra={
            "kp_run_id": run_id,
            "kp_policy": policy.name,
            "kp_cohort_size": cohort_size,
            "kp_contacts_sent": contacts_sent,
            "kp_recovered_amount": str(recovered_amount),
        },
    )

    return PolicyEvaluationResult(
        policy_name=policy.name,
        policy_version=policy.version,
        recovered_amount=recovered_amount,
        total_at_risk_amount=total_at_risk,
        recovery_rate=recovery_rate,
        contacts_sent=contacts_sent,
        contacts_avoided=contacts_avoided,
        human_escalations=human_escalations,
        false_positives=false_positives,
        policy_blocks=policy_blocks,
        cases_evaluated=cohort_size,
        llm_fallback_count=llm_fallbacks,
    )


def run_same_cohort_evaluation(
    seed: int,
    cohort_size: int,
    simulator_version: str,
    run_id: str,
) -> EvaluationRunResult:
    """
    Generate the world ONCE, evaluate all three policies against the SAME world.

    This enforces the CLAUDE.md §17 same-cohort invariant:
      - same seed → same world
      - same world → same customer population
      - same world → same event history
      - same world → same potential outcomes
      - only the policy changes

    Returns EvaluationRunResult with all three policies and incremental recovery.
    """
    from datetime import datetime, timezone
    from app.simulator.generator import generate_world
    from app.simulator.world import WorldInternal
    from app.evaluation.policies import StaticDunningPolicy, SmartRetryPolicy

    reference_date = TRAINING_REFERENCE_DATE  # fixed reference for reproducibility

    logger.info(
        "evaluation_start",
        extra={
            "kp_run_id": run_id,
            "kp_seed": seed,
            "kp_cohort_size": cohort_size,
        },
    )

    # ── Step 1: Generate world ONCE ───────────────────────────────────────────
    raw = generate_world(
        seed=seed,
        cohort_size=cohort_size,
        simulator_version=simulator_version,
        reference_date=reference_date,
    )
    world = WorldInternal.from_raw_records(
        raw=raw,
        seed=seed,
        cohort_size=cohort_size,
        simulator_version=simulator_version,
        reference_date=reference_date,
    )
    eval_world = EvaluationWorld(world=world)

    # ── Step 2: Evaluate each policy against the SAME world ───────────────────
    static_result = evaluate_policy_on_world(StaticDunningPolicy(), eval_world, run_id)
    smart_result = evaluate_policy_on_world(SmartRetryPolicy(), eval_world, run_id)
    kp_policy = KhaataPulsePolicy()
    kp_result = evaluate_policy_on_world(kp_policy, eval_world, run_id)

    # ── Step 3: Compute incremental recovery (primary KPI) ────────────────────
    incremental_recovery = kp_result.recovered_amount - smart_result.recovered_amount

    # Attach to results
    kp_result.incremental_recovery = incremental_recovery

    policy_version = (
        f"{STATIC_DUNNING_VERSION},{SMART_RETRY_VERSION},{KHAATAPULSE_VERSION}"
    )

    logger.info(
        "evaluation_complete",
        extra={
            "kp_run_id": run_id,
            "kp_seed": seed,
            "kp_incremental_recovery": str(incremental_recovery),
        },
    )

    return EvaluationRunResult(
        run_id=run_id,
        seed=seed,
        cohort_size=cohort_size,
        simulator_version=simulator_version,
        model_version=MODEL_VERSION,
        policy_version=policy_version,
        static_dunning=static_result,
        smart_retry=smart_result,
        khaatapulse=kp_result,
        incremental_recovery=incremental_recovery,
    )
