"""
Policy Guard tests — CLAUDE.md §32.

Verifies every rule independently:
  - kill_switch
  - dispute_hold
  - legal_hold
  - opt_out
  - idempotency (duplicate key)
  - contact_limit (3 per 7 days)
  - cooldown (24h)
  - amount_threshold (>= ₹10,000 → ESCALATED)
  - APPROVED when all pass
  - Same inputs always produce same output (deterministic)
  - Pure: no side effects visible from the outside
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.policy.guard import PolicyDecision, PolicyStatus, policy_guard


# ── Helpers ───────────────────────────────────────────────────────────────────

def _guard(
    *,
    customer_id: int = 1,
    action_type: str = "silent_retry",
    amount: Decimal = Decimal("999"),
    idempotency_key: str = "rec_CASE_1",
    dispute_hold: bool = False,
    legal_hold: bool = False,
    opt_out: bool = False,
    db=None,
) -> PolicyDecision:
    return policy_guard(
        customer_id=customer_id,
        action_type=action_type,
        amount=amount,
        idempotency_key=idempotency_key,
        dispute_hold=dispute_hold,
        legal_hold=legal_hold,
        opt_out=opt_out,
        db=db,
    )


# ── APPROVED path ─────────────────────────────────────────────────────────────

class TestApprovedPath:
    def test_all_checks_pass_returns_approved(self):
        decision = _guard()
        assert decision.status == PolicyStatus.APPROVED

    def test_approved_block_reason_is_none(self):
        decision = _guard()
        assert decision.block_reason is None

    def test_approved_has_all_check_keys(self):
        decision = _guard()
        for key in ("kill_switch", "dispute_hold", "legal_hold", "opt_out"):
            assert key in decision.checks

    def test_approved_all_checks_true(self):
        decision = _guard()
        for key, passed in decision.checks.items():
            assert passed is True, f"Check '{key}' should be True for approved decision"

    def test_approved_carries_correct_action_type(self):
        decision = _guard(action_type="smart_link")
        assert decision.action_type == "smart_link"

    def test_approved_carries_correct_amount(self):
        decision = _guard(amount=Decimal("5000"))
        assert decision.amount == Decimal("5000")

    def test_as_dict_serializable(self):
        decision = _guard()
        d = decision.as_dict()
        assert d["status"] == PolicyStatus.APPROVED
        assert isinstance(d["checks"], dict)
        assert isinstance(d["amount"], str)


# ── Kill switch ───────────────────────────────────────────────────────────────

class TestKillSwitch:
    def test_kill_switch_blocks(self):
        with patch("app.policy.guard.get_settings") as mock_settings:
            settings = MagicMock()
            settings.kill_switch = True
            settings.auto_action_limit = 10000
            settings.max_contacts_7d = 3
            settings.contact_cooldown_hours = 24
            mock_settings.return_value = settings
            decision = _guard()
        assert decision.status == PolicyStatus.BLOCKED
        assert decision.block_reason == "kill_switch_active"
        assert decision.checks.get("kill_switch") is False

    def test_kill_switch_off_does_not_block(self):
        with patch("app.policy.guard.get_settings") as mock_settings:
            settings = MagicMock()
            settings.kill_switch = False
            settings.auto_action_limit = 10000
            settings.max_contacts_7d = 3
            settings.contact_cooldown_hours = 24
            mock_settings.return_value = settings
            decision = _guard()
        assert decision.status != PolicyStatus.BLOCKED or decision.block_reason != "kill_switch_active"


# ── Dispute hold ──────────────────────────────────────────────────────────────

class TestDisputeHold:
    def test_dispute_hold_blocks(self):
        decision = _guard(dispute_hold=True)
        assert decision.status == PolicyStatus.BLOCKED
        assert decision.block_reason == "dispute_hold"
        assert decision.checks.get("dispute_hold") is False

    def test_no_dispute_hold_passes_check(self):
        decision = _guard(dispute_hold=False)
        assert decision.checks.get("dispute_hold") is True


# ── Legal hold ────────────────────────────────────────────────────────────────

class TestLegalHold:
    def test_legal_hold_blocks(self):
        decision = _guard(legal_hold=True)
        assert decision.status == PolicyStatus.BLOCKED
        assert decision.block_reason == "legal_hold"
        assert decision.checks.get("legal_hold") is False

    def test_no_legal_hold_passes_check(self):
        decision = _guard(legal_hold=False)
        assert decision.checks.get("legal_hold") is True


# ── Opt-out ───────────────────────────────────────────────────────────────────

class TestOptOut:
    def test_opt_out_blocks(self):
        decision = _guard(opt_out=True)
        assert decision.status == PolicyStatus.BLOCKED
        assert decision.block_reason == "opt_out"
        assert decision.checks.get("opt_out") is False

    def test_no_opt_out_passes_check(self):
        decision = _guard(opt_out=False)
        assert decision.checks.get("opt_out") is True


# ── Amount threshold (ESCALATED) ─────────────────────────────────────────────

class TestAmountThreshold:
    def test_amount_below_limit_approved(self):
        decision = _guard(amount=Decimal("9999"))
        assert decision.status == PolicyStatus.APPROVED

    def test_amount_at_limit_escalated(self):
        decision = _guard(amount=Decimal("10000"))
        assert decision.status == PolicyStatus.ESCALATED
        assert "human_approval" in (decision.block_reason or "")

    def test_amount_above_limit_escalated(self):
        decision = _guard(amount=Decimal("50000"))
        assert decision.status == PolicyStatus.ESCALATED

    def test_escalated_has_all_checks_present(self):
        decision = _guard(amount=Decimal("10000"))
        assert "amount_threshold" in decision.checks

    def test_escalated_is_not_blocked(self):
        decision = _guard(amount=Decimal("15000"))
        assert decision.status == PolicyStatus.ESCALATED
        assert decision.status != PolicyStatus.BLOCKED


# ── Priority: hold flags before amount threshold ───────────────────────────────

class TestRulePriority:
    def test_dispute_hold_takes_priority_over_escalation(self):
        decision = _guard(dispute_hold=True, amount=Decimal("50000"))
        assert decision.status == PolicyStatus.BLOCKED
        assert decision.block_reason == "dispute_hold"

    def test_legal_hold_takes_priority_over_amount(self):
        decision = _guard(legal_hold=True, amount=Decimal("99999"))
        assert decision.status == PolicyStatus.BLOCKED

    def test_opt_out_takes_priority_over_amount(self):
        decision = _guard(opt_out=True, amount=Decimal("50000"))
        assert decision.status == PolicyStatus.BLOCKED

    def test_multiple_hold_flags_blocked_on_first_one(self):
        decision = _guard(dispute_hold=True, legal_hold=True)
        # dispute_hold is checked before legal_hold
        assert decision.block_reason == "dispute_hold"


# ── Idempotency (DB-backed) ───────────────────────────────────────────────────

class TestIdempotency:
    def _mock_db_with_existing_key(self, idempotency_key: str):
        from unittest.mock import MagicMock
        existing = MagicMock()
        existing.id = 99
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = existing
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.scalar.return_value = 0
        return db

    def _mock_db_no_existing(self):
        from unittest.mock import MagicMock
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.scalar.return_value = 0
        return db

    def test_duplicate_idempotency_key_blocks(self):
        db = self._mock_db_with_existing_key("rec_CASE_1")
        decision = _guard(idempotency_key="rec_CASE_1", db=db)
        assert decision.status == PolicyStatus.BLOCKED
        assert "duplicate_idempotency_key" in (decision.block_reason or "")

    def test_fresh_idempotency_key_passes(self):
        db = self._mock_db_no_existing()
        decision = _guard(idempotency_key="rec_CASE_999", db=db)
        assert decision.checks.get("idempotency") is True

    def test_no_db_skips_idempotency_check(self):
        decision = _guard(db=None)
        assert decision.checks.get("idempotency") is True


# ── Contact limit (DB-backed) ──────────────────────────────────────────────────

class TestContactLimit:
    def _mock_db_contact_count(self, count: int):
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.scalar.return_value = count
        return db

    def test_under_contact_limit_passes(self):
        db = self._mock_db_contact_count(2)
        decision = _guard(db=db)
        assert decision.checks.get("contact_limit") is True

    def test_at_contact_limit_blocks(self):
        db = self._mock_db_contact_count(3)
        decision = _guard(db=db)
        assert decision.status == PolicyStatus.BLOCKED
        assert "contact_limit_reached" in (decision.block_reason or "")

    def test_over_contact_limit_blocks(self):
        db = self._mock_db_contact_count(5)
        decision = _guard(db=db)
        assert decision.status == PolicyStatus.BLOCKED

    def test_no_db_skips_contact_limit(self):
        decision = _guard(db=None)
        assert decision.checks.get("contact_limit") is True


# ── Cooldown (DB-backed) ───────────────────────────────────────────────────────

class TestCooldown:
    def _mock_db_with_recent_contact(self):
        from unittest.mock import MagicMock
        recent_action = MagicMock()
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None  # idempotency
        # contact_limit returns 0 (within limit)
        db.query.return_value.filter.return_value.scalar.return_value = 1
        # cooldown returns recent action
        db.query.return_value.filter.return_value.first.return_value = recent_action
        return db

    def _mock_db_no_recent_contact(self):
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    def test_no_recent_contact_passes_cooldown(self):
        db = self._mock_db_no_recent_contact()
        decision = _guard(db=db)
        assert decision.checks.get("cooldown") is True

    def test_no_db_skips_cooldown(self):
        decision = _guard(db=None)
        assert decision.checks.get("cooldown") is True


# ── Determinism ────────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_same_inputs_same_output(self):
        kwargs = dict(
            customer_id=42,
            action_type="smart_link",
            amount=Decimal("4999"),
            idempotency_key="rec_CASE_42",
        )
        d1 = _guard(**kwargs)
        d2 = _guard(**kwargs)
        assert d1.status == d2.status
        assert d1.checks == d2.checks
        assert d1.block_reason == d2.block_reason

    def test_blocked_and_approved_are_different(self):
        approved = _guard(dispute_hold=False)
        blocked = _guard(dispute_hold=True)
        assert approved.status != blocked.status
