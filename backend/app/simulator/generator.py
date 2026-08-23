"""
Deterministic customer world generator.

Accepts a seed + cohort_size and produces a fully reproducible synthetic world.
The same seed + simulator_version always yields the same world.
Hidden state and potential outcomes are generated internally and NEVER leak
through the observable interface.
"""
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.simulator.latent_state import CustomerLatentState
from app.simulator.outcomes import generate_outcomes, PotentialOutcomes, ACTION_TYPES
from app.simulator.events import generate_observable_events


# ── Name vocabulary ───────────────────────────────────────────────────────────
_FIRST_NAMES = [
    "Arjun", "Kavita", "Siddharth", "Priya", "Rohit", "Ananya", "Vikram", "Meera",
    "Rahul", "Divya", "Aditya", "Sneha", "Nikhil", "Pooja", "Karthik", "Sunita",
    "Rajesh", "Neha", "Amit", "Swati", "Deepak", "Ritu", "Manish", "Alka", "Suresh",
    "Usha", "Sandeep", "Lata", "Vijay", "Rekha",
]
_LAST_NAMES = [
    "Mehta", "Reddy", "Nair", "Singh", "Kumar", "Sharma", "Patel", "Gupta",
    "Iyer", "Joshi", "Agarwal", "Pillai", "Verma", "Rao", "Mishra", "Shah",
    "Chaudhary", "Bose", "Das", "Mukherjee", "Choudhury", "Trivedi", "Bhatt",
    "Deshpande", "Jain", "Malhotra", "Kapoor", "Srivastava", "Tiwari", "Pandey",
]

# ── Segment definitions ────────────────────────────────────────────────────────
_SEGMENT_WEIGHTS = [("consumer", 0.30), ("smb", 0.50), ("enterprise", 0.20)]

_SEGMENT_PLANS: dict[str, list[tuple[str, int]]] = {
    "consumer":   [("basic", 199), ("standard", 499), ("premium", 999)],
    "smb":        [("starter", 1999), ("growth", 4999), ("professional", 9999)],
    "enterprise": [("business", 9999), ("enterprise", 24999), ("enterprise_plus", 49999)],
}

# ── Payment methods ────────────────────────────────────────────────────────────
_PAYMENT_METHODS = ["upi", "card", "net_banking", "wallet"]
_PAYMENT_METHOD_WEIGHTS = [0.40, 0.35, 0.15, 0.10]

_FAILURE_CODES: dict[str, list[str]] = {
    "upi":         ["insufficient_funds", "bank_declined", "upi_timeout"],
    "card":        ["card_expired", "card_blocked", "insufficient_funds", "invalid_card"],
    "net_banking": ["bank_declined", "session_expired", "insufficient_funds"],
    "wallet":      ["insufficient_balance", "wallet_limit_exceeded"],
}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _beta(rng: random.Random, alpha: float, beta: float) -> float:
    return rng.betavariate(alpha, beta)


def _generate_latent_state(rng: random.Random, amount: int) -> CustomerLatentState:
    """Generate hidden latent state. Never expose this object outside the simulator."""
    payment_intent = _beta(rng, alpha=4.0, beta=1.5)          # skewed high
    cash_flow_health = _beta(rng, alpha=2.5, beta=2.0)         # roughly uniform
    payment_rail_health = _beta(rng, alpha=5.0, beta=1.5)      # skewed high
    churn_sensitivity = _beta(rng, alpha=1.5, beta=4.0)        # skewed low

    # LTV = subscription amount × expected months of tenure (12–60 months)
    expected_months = 12 + _beta(rng, alpha=1.5, beta=1.0) * 48
    ltv = Decimal(str(round(amount * expected_months, 2)))

    return CustomerLatentState(
        payment_intent=payment_intent,
        cash_flow_health=cash_flow_health,
        payment_rail_health=payment_rail_health,
        churn_sensitivity=churn_sensitivity,
        customer_ltv=ltv,
    )


def _generate_payment_history(
    rng: random.Random,
    customer_id: int,
    subscription_id_placeholder: int,
    amount: int,
    payment_method: str,
    latent: CustomerLatentState,
    renewal_at: datetime,
) -> list[dict]:
    """Generate observable payment history. Status and failure codes are observable."""
    payments: list[dict] = []
    now = renewal_at - timedelta(days=3)

    # Generate 3–6 historical payments over the past 6 months
    num_historical = rng.randint(3, 6)
    for i in range(num_historical):
        months_ago = (i + 1)
        payment_date = now - timedelta(days=months_ago * 30 + rng.randint(-3, 3))

        # Probability of success based on latent state
        p_success = latent.payment_rail_health * latent.cash_flow_health
        success = rng.random() < p_success

        payments.append({
            "customer_id": customer_id,
            "subscription_id": subscription_id_placeholder,
            "amount": Decimal(str(amount)),
            "status": "successful" if success else "failed",
            "failure_code": None if success else rng.choice(_FAILURE_CODES.get(payment_method, ["bank_declined"])),
            "payment_method": payment_method,
            "created_at": payment_date,
        })

    # Current renewal attempt (pending)
    payments.append({
        "customer_id": customer_id,
        "subscription_id": subscription_id_placeholder,
        "amount": Decimal(str(amount)),
        "status": "pending",
        "failure_code": None,
        "payment_method": payment_method,
        "created_at": now,
    })

    payments.sort(key=lambda p: p["created_at"])
    return payments


# ── Public interface ───────────────────────────────────────────────────────────

def generate_customer_record(
    rng: random.Random,
    customer_id: int,
    reference_date: datetime,
) -> dict:
    """
    Generate one complete customer record (internal representation).
    Returns a dict with:
      - observable: data safe to expose outside the simulator
      - _latent: CustomerLatentState - NEVER expose
      - _outcomes: PotentialOutcomes - NEVER expose
    """
    # Segment and plan
    segments = [s for s, _ in _SEGMENT_WEIGHTS]
    seg_weights = [w for _, w in _SEGMENT_WEIGHTS]
    segment = rng.choices(segments, weights=seg_weights)[0]

    plans = _SEGMENT_PLANS[segment]
    plan_name, amount = rng.choice(plans)

    # Payment method
    payment_method = rng.choices(_PAYMENT_METHODS, weights=_PAYMENT_METHOD_WEIGHTS)[0]

    # Subscription renewal (7–30 days in future)
    days_to_renewal = rng.randint(5, 28)
    renewal_at = reference_date + timedelta(days=days_to_renewal)

    # Customer name
    name = f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"

    # Hidden latent state
    latent = _generate_latent_state(rng, amount)

    # LTV stored in customer table = same as latent.customer_ltv (LTV is observable)
    ltv = latent.customer_ltv

    # Subscription data
    subscription = {
        "customer_id": customer_id,
        "plan": plan_name,
        "amount": Decimal(str(amount)),
        "currency": "INR",
        "renewal_at": renewal_at,
        "status": "active",
    }

    # Payment history
    # Use customer_id as placeholder for subscription_id (resolved after DB insert)
    payments = _generate_payment_history(
        rng, customer_id, customer_id, amount, payment_method, latent, renewal_at
    )

    # Observable events
    events = generate_observable_events(
        rng, customer_id, Decimal(str(amount)), payment_method, renewal_at, latent, payments
    )
    # Patch plan name into renewal_approaching payload
    for ev in events:
        if ev["event_type"] == "renewal_approaching" and ev["payload"].get("plan_name") is None:
            ev["payload"]["plan_name"] = plan_name

    # Hidden potential outcomes
    outcomes = generate_outcomes(rng, latent)

    return {
        # ── Observable ────────────────────────────────────────────────────────
        "customer": {
            "id": customer_id,
            "name": name,
            "segment": segment,
            "ltv": ltv,
        },
        "subscription": subscription,
        "payments": payments,
        "events": events,
        # ── HIDDEN - never cross the observable boundary ───────────────────────
        "_latent": latent,
        "_outcomes": outcomes,
    }


def generate_world(
    seed: int,
    cohort_size: int,
    simulator_version: str,
    reference_date: datetime | None = None,
) -> list[dict]:
    """
    Generate a deterministic synthetic world.

    Args:
        seed:             RNG seed - same seed + version always produces same world.
        cohort_size:      Number of customers to generate.
        simulator_version: Version string for reproducibility tracking.
        reference_date:   "today" anchor for renewal dates. Defaults to UTC now.

    Returns:
        List of customer records (internal representation with hidden fields).
        Callers must NOT expose _latent or _outcomes fields outside the simulator.
    """
    rng = random.Random(seed)
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    records = []
    for i in range(cohort_size):
        record = generate_customer_record(rng, customer_id=i + 1, reference_date=reference_date)
        records.append(record)

    return records
