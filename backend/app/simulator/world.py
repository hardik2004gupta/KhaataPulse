"""
World boundary - separates simulator internals from observable data.

WorldInternal    - full world including hidden state and potential outcomes.
                   Lives entirely inside the simulator module.

ObservableWorld  - contains only what downstream systems may see.
                   This is the ONLY representation that crosses the simulator boundary.

CLAUDE.md §6: "observable events only" is the data that crosses from
Simulation World → Core Agent.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.simulator.latent_state import CustomerLatentState
from app.simulator.outcomes import PotentialOutcomes


# ─── Internal representation (simulator-owned) ────────────────────────────────

@dataclass
class _InternalCustomerRecord:
    customer_id: int
    name: str
    segment: str
    ltv: Decimal
    subscription: dict
    payments: list[dict]
    events: list[dict]
    latent_state: CustomerLatentState    # HIDDEN
    potential_outcomes: PotentialOutcomes  # HIDDEN


@dataclass
class WorldInternal:
    """
    Full simulation world. Contains hidden state and outcome probabilities.
    Must never be serialized or returned by any observable API.
    """
    seed: int
    cohort_size: int
    simulator_version: str
    reference_date: datetime
    records: list[_InternalCustomerRecord] = field(default_factory=list)

    @classmethod
    def from_raw_records(
        cls,
        raw: list[dict],
        seed: int,
        cohort_size: int,
        simulator_version: str,
        reference_date: datetime,
    ) -> "WorldInternal":
        records = [
            _InternalCustomerRecord(
                customer_id=r["customer"]["id"],
                name=r["customer"]["name"],
                segment=r["customer"]["segment"],
                ltv=r["customer"]["ltv"],
                subscription=r["subscription"],
                payments=r["payments"],
                events=r["events"],
                latent_state=r["_latent"],
                potential_outcomes=r["_outcomes"],
            )
            for r in raw
        ]
        return cls(
            seed=seed,
            cohort_size=cohort_size,
            simulator_version=simulator_version,
            reference_date=reference_date,
            records=records,
        )


# ─── Observable representation (safe to cross the boundary) ──────────────────

@dataclass(frozen=True)
class ObservableSubscription:
    plan: str
    amount: Decimal
    currency: str
    renewal_at: datetime
    status: str


@dataclass(frozen=True)
class ObservablePayment:
    amount: Decimal
    status: str
    failure_code: str | None
    payment_method: str
    created_at: datetime


@dataclass(frozen=True)
class ObservableEvent:
    event_type: str
    timestamp: datetime
    payload: dict   # contains ONLY observable fields


@dataclass(frozen=True)
class ObservableCustomerData:
    """
    The ONLY customer representation that may be passed to downstream systems
    (risk model, LangGraph agent, API responses).

    Guaranteed to contain NO:
      - latent_state (payment_intent, cash_flow_health, etc.)
      - potential_outcomes (P(payment|action), P(churn|action))
    """
    customer_id: int
    name: str
    segment: str
    ltv: Decimal
    subscription: ObservableSubscription
    payments: list[ObservablePayment]
    events: list[ObservableEvent]


@dataclass
class ObservableWorld:
    """Observable slice of the world - safe for agent consumption."""
    customers: list[ObservableCustomerData]


def extract_observable(world: WorldInternal) -> ObservableWorld:
    """
    Extract the observable view from the full internal world.
    This is the ONLY sanctioned way to cross the simulator boundary.
    """
    observable_customers: list[ObservableCustomerData] = []

    for rec in world.records:
        obs_sub = ObservableSubscription(
            plan=rec.subscription["plan"],
            amount=rec.subscription["amount"],
            currency=rec.subscription["currency"],
            renewal_at=rec.subscription["renewal_at"],
            status=rec.subscription["status"],
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
        observable_customers.append(
            ObservableCustomerData(
                customer_id=rec.customer_id,
                name=rec.name,
                segment=rec.segment,
                ltv=rec.ltv,
                subscription=obs_sub,
                payments=obs_payments,
                events=obs_events,
            )
        )

    return ObservableWorld(customers=observable_customers)
