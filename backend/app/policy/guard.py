"""
Policy Guard — CLAUDE.md §14.

Pure, deterministic, independently testable. No side effects.
All thresholds from environment config. Non-bypassable.

Rules (evaluated in this order):
  1. kill_switch        → BLOCKED if automation is globally paused
  2. dispute_hold       → BLOCKED if customer has active dispute
  3. legal_hold         → BLOCKED if customer has legal hold
  4. opt_out            → BLOCKED if customer opted out of contacts
  5. idempotency        → BLOCKED if action already executed (same key)
  6. contact_limit      → BLOCKED if >= max_contacts_7d in last 7 days
  7. cooldown           → BLOCKED if last contact < contact_cooldown_hours ago
  8. amount_threshold   → ESCALATED if amount >= auto_action_limit (requires human)

Only an action that passes ALL rules gets APPROVED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings


# ── Result types ─────────────────────────────────────────────────────────────

class PolicyStatus:
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    ESCALATED = "ESCALATED"


@dataclass
class PolicyDecision:
    """
    Immutable policy decision. Status is APPROVED, BLOCKED, or ESCALATED.
    `checks` contains a dict of {rule_name: passed_bool} for every rule evaluated.
    `block_reason` is set when status is BLOCKED or ESCALATED.
    """
    status: str                           # APPROVED | BLOCKED | ESCALATED
    checks: dict[str, bool] = field(default_factory=dict)
    block_reason: Optional[str] = None
    action_type: str = ""
    customer_id: int = 0
    amount: Decimal = Decimal("0")
    idempotency_key: str = ""

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "checks": self.checks,
            "block_reason": self.block_reason,
            "action_type": self.action_type,
            "customer_id": self.customer_id,
            "amount": str(self.amount),
            "idempotency_key": self.idempotency_key,
        }


# ── Policy Guard ──────────────────────────────────────────────────────────────

def policy_guard(
    *,
    customer_id: int,
    action_type: str,
    amount: Decimal,
    idempotency_key: str,
    dispute_hold: bool = False,
    legal_hold: bool = False,
    opt_out: bool = False,
    db: Optional[Session] = None,
) -> PolicyDecision:
    """
    Pure deterministic policy check — CLAUDE.md §14.

    Args:
        customer_id:    Target customer.
        action_type:    Proposed action (silent_retry, smart_link, etc.).
        amount:         Subscription amount in INR.
        idempotency_key: Unique key for this action (rec_CASE_{id}).
        dispute_hold:   Customer has an active dispute.
        legal_hold:     Customer has an active legal hold.
        opt_out:        Customer opted out of recovery contacts.
        db:             DB session for contact history lookups. If None, history
                        checks are skipped (test / demo mode).

    Returns:
        PolicyDecision with APPROVED, BLOCKED, or ESCALATED status.
    """
    settings = get_settings()
    checks: dict[str, bool] = {}

    def _block(reason: str) -> PolicyDecision:
        return PolicyDecision(
            status=PolicyStatus.BLOCKED,
            checks=checks,
            block_reason=reason,
            action_type=action_type,
            customer_id=customer_id,
            amount=amount,
            idempotency_key=idempotency_key,
        )

    # 1. Kill switch — CLAUDE.md §23
    checks["kill_switch"] = not settings.kill_switch
    if settings.kill_switch:
        return _block("kill_switch_active")

    # 2. Dispute hold
    checks["dispute_hold"] = not dispute_hold
    if dispute_hold:
        return _block("dispute_hold")

    # 3. Legal hold
    checks["legal_hold"] = not legal_hold
    if legal_hold:
        return _block("legal_hold")

    # 4. Opt-out
    checks["opt_out"] = not opt_out
    if opt_out:
        return _block("opt_out")

    # 5. Idempotency — reject if same key already executed
    if db is not None:
        from app.db.models.action import RecoveryAction
        existing = db.query(RecoveryAction).filter_by(idempotency_key=idempotency_key).first()
        checks["idempotency"] = existing is None
        if existing is not None:
            return _block(f"duplicate_idempotency_key:{idempotency_key}")
    else:
        checks["idempotency"] = True  # skip in no-db mode

    # 6. Contact limit (3 per 7 days) — CLAUDE.md §14
    if db is not None:
        from app.db.models.action import RecoveryAction
        from sqlalchemy import func
        window_start = datetime.now(timezone.utc) - timedelta(days=7)
        contact_count = (
            db.query(func.count(RecoveryAction.id))
            .filter(
                RecoveryAction.customer_id == customer_id,
                RecoveryAction.timestamp >= window_start,
                RecoveryAction.action_type != "suppress",
            )
            .scalar() or 0
        )
        checks["contact_limit"] = contact_count < settings.max_contacts_7d
        if contact_count >= settings.max_contacts_7d:
            return _block(f"contact_limit_reached:{contact_count}/{settings.max_contacts_7d}")
    else:
        checks["contact_limit"] = True

    # 7. Cooldown (24h between contacts)
    if db is not None:
        from app.db.models.action import RecoveryAction
        cooldown_start = datetime.now(timezone.utc) - timedelta(hours=settings.contact_cooldown_hours)
        recent = (
            db.query(RecoveryAction)
            .filter(
                RecoveryAction.customer_id == customer_id,
                RecoveryAction.timestamp >= cooldown_start,
                RecoveryAction.action_type != "suppress",
            )
            .first()
        )
        checks["cooldown"] = recent is None
        if recent is not None:
            return _block(f"cooldown_active:last_contact_within_{settings.contact_cooldown_hours}h")
    else:
        checks["cooldown"] = True

    # 8. Amount threshold — auto vs. human approval
    auto_limit = Decimal(str(settings.auto_action_limit))
    if amount >= auto_limit:
        checks["amount_threshold"] = True  # rule passed but requires escalation
        return PolicyDecision(
            status=PolicyStatus.ESCALATED,
            checks=checks,
            block_reason="amount_requires_human_approval",
            action_type=action_type,
            customer_id=customer_id,
            amount=amount,
            idempotency_key=idempotency_key,
        )

    checks["amount_threshold"] = True

    return PolicyDecision(
        status=PolicyStatus.APPROVED,
        checks=checks,
        block_reason=None,
        action_type=action_type,
        customer_id=customer_id,
        amount=amount,
        idempotency_key=idempotency_key,
    )
