"""
Observable event generation from hidden latent state.

ARCHITECTURE BOUNDARY:
  - Input:  CustomerLatentState (hidden)
  - Output: list of observable event dicts — the ONLY simulator data that crosses
            into the observable world.

Event payloads contain ONLY information that would be legitimately observable by
a recovery system (amounts, dates, status codes, message text). They must never
contain payment_intent, cash_flow_health, payment_rail_health, churn_sensitivity,
or any derived probability.
"""
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.simulator.latent_state import CustomerLatentState, derive_cause


# Support message templates per cause category.
# These hint at the root cause without revealing latent state directly.
_SUPPORT_TEMPLATES: dict[str, list[str]] = {
    "billing_migration": [
        "We recently migrated our accounting system and the billing entity has changed. "
        "Can you update the invoice details to reflect our new company name?",
        "Our company went through a restructuring and the GST registration is under a new entity. "
        "The payment is failing because of a mismatch. Please help.",
        "We switched to a centralized billing team and the old card is no longer active for this account. "
        "Working on getting the new payment details set up.",
        "Billing responsibility moved to our finance department last week. "
        "They're setting up the new payment method — should be resolved shortly.",
    ],
    "temporary_cash_flow": [
        "We're experiencing a temporary cash flow crunch this quarter. "
        "Is there any flexibility on the payment date or a short extension?",
        "Our receivables are delayed this month due to a large client payment being held up. "
        "We fully intend to continue — just need a few extra days.",
        "We had some unexpected expenses this month that have squeezed our working capital. "
        "Can we get a brief grace period?",
        "This is a temporary situation — we have invoices due from clients that will clear shortly. "
        "Would appreciate a few days of flexibility.",
    ],
    "card_expired": [
        "My credit card expired last month and I've been trying to update the payment method. "
        "The new card should be active — can you retry?",
        "The card on file has been replaced by my bank. I've added the new details to my profile.",
        "Bank issued a new card and the old one is no longer valid. Updated the payment method just now.",
        "Card was blocked due to a fraud alert and I received a replacement. "
        "New card details have been updated — please retry the payment.",
    ],
    "price_friction": [
        "We've been reviewing our software spend and the current tier is higher than we're utilizing. "
        "Can we discuss the pricing?",
        "The renewal amount seems higher than what we budgeted for. "
        "We'd like to understand what options are available before committing.",
        "We're evaluating our tool stack this quarter. The current pricing is a concern. "
        "Is there a more suitable plan for our current usage?",
        "I noticed the renewal went up from last year. Wanted to understand the pricing change "
        "before authorizing the payment.",
    ],
    "churn_intent": [
        "We're currently evaluating alternative solutions and may not be renewing. "
        "Please don't auto-charge until we've made a final decision.",
        "Our team has been discussing whether this tool still fits our workflow. "
        "Can we put the renewal on hold while we review?",
        "We've had some internal discussions about our software stack. "
        "I'll need to check with the team before approving this renewal.",
        "We're in the middle of a vendor review process. Not sure about the renewal yet.",
    ],
}

_PAYMENT_METHOD_NAMES = {
    "upi": "UPI",
    "card": "credit card",
    "net_banking": "net banking",
    "wallet": "digital wallet",
}


def _days_ago(base_date: datetime, days: float) -> datetime:
    return base_date - timedelta(days=days)


def generate_observable_events(
    rng: random.Random,
    customer_id: int,
    subscription_amount: Decimal,
    payment_method: str,
    renewal_at: datetime,
    latent: CustomerLatentState,
    payment_history: list[dict],
) -> list[dict]:
    """
    Generate observable events from hidden latent state.
    Returns list of event dicts with keys: event_type, timestamp, payload.
    Payload contains ONLY observable information — never latent variables.
    """
    now = renewal_at - timedelta(days=3)   # simulate current moment = 3 days before renewal
    cause = derive_cause(latent, rng)
    events: list[dict] = []

    amount_int = int(subscription_amount)

    # ── renewal_approaching — universal ──────────────────────────────────────
    days_until = (renewal_at - now).days
    events.append({
        "event_type": "renewal_approaching",
        "timestamp": _days_ago(now, rng.uniform(0.5, 2.0)),
        "payload": {
            "days_until_renewal": days_until,
            "amount": amount_int,
            "currency": "INR",
            "plan_name": None,   # filled by generator
        },
    })

    # ── invoice_viewed — most customers with any payment intent ───────────────
    if latent.payment_intent > 0.25 or rng.random() < 0.3:
        view_days_ago = rng.uniform(3, 20)
        events.append({
            "event_type": "invoice_viewed",
            "timestamp": _days_ago(now, view_days_ago),
            "payload": {
                "invoice_ref": f"INV-{customer_id:05d}",
                "amount": amount_int,
                "currency": "INR",
            },
        })

    # ── checkout_reopened — high intent + decent cash flow ────────────────────
    if latent.payment_intent > 0.55 and latent.cash_flow_health > 0.35:
        reopen_count = rng.randint(1, 3) if latent.payment_intent > 0.7 else 1
        events.append({
            "event_type": "checkout_reopened",
            "timestamp": _days_ago(now, rng.uniform(2, 12)),
            "payload": {
                "reopen_count": reopen_count,
                "payment_method_attempted": payment_method,
            },
        })

    # ── payment_method_changed — low rail health (card issues) ───────────────
    if latent.payment_rail_health < 0.50:
        old_method = rng.choice(["card", "net_banking"])
        events.append({
            "event_type": "payment_method_changed",
            "timestamp": _days_ago(now, rng.uniform(5, 18)),
            "payload": {
                "old_method": old_method,
                "new_method": payment_method,
            },
        })

    # ── payment_failed — low rail or cash flow ────────────────────────────────
    failed_payments = [p for p in payment_history if p["status"] == "failed"]
    for fp in failed_payments[:2]:    # show at most last 2 failures as events
        events.append({
            "event_type": "payment_failed",
            "timestamp": fp["created_at"],
            "payload": {
                "amount": amount_int,
                "failure_code": fp["failure_code"],
                "payment_method": fp["payment_method"],
            },
        })

    # ── payment_delayed — cash flow issue but rail is OK ─────────────────────
    if latent.cash_flow_health < 0.55 and latent.payment_rail_health > 0.40:
        delay_days = rng.randint(2, 7)
        events.append({
            "event_type": "payment_delayed",
            "timestamp": _days_ago(now, rng.uniform(8, 20)),
            "payload": {
                "days_delayed": delay_days,
                "reason_category": "cash_flow",  # observable category — NOT the latent cause
            },
        })

    # ── subscription_changed — churn signal ──────────────────────────────────
    if latent.churn_sensitivity > 0.60 and latent.payment_intent < 0.55:
        events.append({
            "event_type": "subscription_changed",
            "timestamp": _days_ago(now, rng.uniform(10, 25)),
            "payload": {
                "change_type": rng.choice(["downgrade_requested", "plan_inquiry"]),
                "current_plan_tier": "standard",
            },
        })

    # ── support_message — cash flow issues or churn signals ──────────────────
    if latent.cash_flow_health < 0.50 or latent.churn_sensitivity > 0.55:
        templates = _SUPPORT_TEMPLATES.get(cause, _SUPPORT_TEMPLATES["temporary_cash_flow"])
        message = rng.choice(templates)
        events.append({
            "event_type": "support_message",
            "timestamp": _days_ago(now, rng.uniform(4, 15)),
            "payload": {
                "message": message,
                "channel": rng.choice(["email", "chat"]),
            },
        })

    # Sort by timestamp ascending to produce a coherent timeline
    events.sort(key=lambda e: e["timestamp"])
    return events
