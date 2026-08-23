"""
Observable feature engineering — CLAUDE.md §8, §4 (Risk Sieve).

ARCHITECTURE BOUNDARY:
  Input:  ObservableCustomerData (never latent state, never potential outcomes)
  Output: RiskFeatures (typed feature vector — all values traceable to observable data)

Every feature here must be derivable from observable events, payment history,
and subscription data. No hidden simulator state may enter this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.simulator.world import ObservableCustomerData


# ── Feature names in the exact order used by to_array() ──────────────────────
# Used by the risk model for explainability / top-signal labelling.
FEATURE_NAMES: list[str] = [
    "days_to_renewal",           # 0: days until subscription renews
    "invoice_views",             # 1: count of invoice_viewed events
    "checkout_reopens",          # 2: count of checkout_reopened events
    "payment_method_changes",    # 3: count of payment_method_changed events
    "previous_payment_failures", # 4: count of failed historical payments
    "average_payment_delay",     # 5: payment_delayed events / historical_payments
    "subscription_age",          # 6: days since earliest historical payment
    "payment_success_rate",      # 7: successful / total historical payments [0,1]
    "support_event_count",       # 8: count of support_message events
    "days_since_last_payment",   # 9: days since most recent historical payment
    "renewal_amount",            # 10: subscription amount in INR
    "segment_encoded",           # 11: 0=consumer, 1=smb, 2=enterprise
]

_SEGMENT_ENCODING = {"consumer": 0, "smb": 1, "enterprise": 2}


@dataclass(frozen=True)
class RiskFeatures:
    """
    Typed feature vector — observable data only.

    All fields derive exclusively from ObservableCustomerData.
    This class intentionally has no latent_state, payment_intent,
    cash_flow_health, payment_rail_health, churn_sensitivity, p_payment,
    or p_churn fields. CLAUDE.md §7 isolation is enforced by the type system.
    """
    days_to_renewal: float
    invoice_views: int
    checkout_reopens: int
    payment_method_changes: int
    previous_payment_failures: int
    average_payment_delay: float
    subscription_age: float
    payment_success_rate: float
    support_event_count: int
    days_since_last_payment: float
    renewal_amount: float
    segment_encoded: int

    def to_array(self) -> list[float]:
        """Return features in FEATURE_NAMES order for the sklearn model."""
        return [
            self.days_to_renewal,
            float(self.invoice_views),
            float(self.checkout_reopens),
            float(self.payment_method_changes),
            float(self.previous_payment_failures),
            self.average_payment_delay,
            self.subscription_age,
            self.payment_success_rate,
            float(self.support_event_count),
            self.days_since_last_payment,
            self.renewal_amount,
            float(self.segment_encoded),
        ]

    def to_dict(self) -> dict:
        return {name: val for name, val in zip(FEATURE_NAMES, self.to_array())}


class FeatureBuilder:
    """
    Transforms ObservableCustomerData → RiskFeatures.

    Uses only observable event history, payment records, and subscription info.
    Never touches CustomerLatentState or PotentialOutcomes.
    """

    def __init__(self, reference_date: datetime | None = None) -> None:
        self._reference_date = reference_date or datetime.now(timezone.utc)

    def build(self, obs: ObservableCustomerData) -> RiskFeatures:
        ref = self._reference_date
        sub = obs.subscription
        payments = obs.payments
        events = obs.events

        # ── Historical payments (exclude pending) ─────────────────────────────
        historical = [p for p in payments if p.status != "pending"]
        successful = [p for p in historical if p.status == "successful"]
        failed = [p for p in historical if p.status == "failed"]

        previous_payment_failures = len(failed)
        # No observed failures when no history → success rate = 1.0
        payment_success_rate = len(successful) / len(historical) if historical else 1.0

        # ── Subscription age (proxy: oldest historical payment → ref date) ────
        if historical:
            oldest = min(p.created_at for p in historical)
            subscription_age = max(0.0, (ref - oldest).total_seconds() / 86400)
        else:
            subscription_age = 0.0

        # ── Days since last historical payment ────────────────────────────────
        if historical:
            latest = max(p.created_at for p in historical)
            days_since_last_payment = max(0.0, (ref - latest).total_seconds() / 86400)
        else:
            days_since_last_payment = 0.0

        # ── Days to renewal ───────────────────────────────────────────────────
        renewal_at = sub.renewal_at
        if renewal_at.tzinfo is None:
            renewal_at = renewal_at.replace(tzinfo=timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        days_to_renewal = max(0.0, (renewal_at - ref).total_seconds() / 86400)

        # ── Event counts ──────────────────────────────────────────────────────
        invoice_views = sum(1 for e in events if e.event_type == "invoice_viewed")
        checkout_reopens = sum(1 for e in events if e.event_type == "checkout_reopened")
        payment_method_changes = sum(1 for e in events if e.event_type == "payment_method_changed")
        support_event_count = sum(1 for e in events if e.event_type == "support_message")
        payment_delayed_count = sum(1 for e in events if e.event_type == "payment_delayed")

        # average_payment_delay: delayed events as a ratio of historical payments
        average_payment_delay = payment_delayed_count / max(1, len(historical))

        return RiskFeatures(
            days_to_renewal=days_to_renewal,
            invoice_views=invoice_views,
            checkout_reopens=checkout_reopens,
            payment_method_changes=payment_method_changes,
            previous_payment_failures=previous_payment_failures,
            average_payment_delay=average_payment_delay,
            subscription_age=subscription_age,
            payment_success_rate=payment_success_rate,
            support_event_count=support_event_count,
            days_since_last_payment=days_since_last_payment,
            renewal_amount=float(sub.amount),
            segment_encoded=_SEGMENT_ENCODING.get(obs.segment, 0),
        )
