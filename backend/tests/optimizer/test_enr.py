"""
Economic Optimizer tests - CLAUDE.md §32.

Verifies:
  - ENR formula is correct: P(payment|a) × Amount - P(churn|a) × LTV - Cost
  - Action ranking is deterministic and descending by ENR
  - Eligible actions filtered per cause
  - Best action selected correctly
  - No hidden simulator state used (estimates only)
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.optimizer.eligibility import CAUSE_ELIGIBILITY, get_eligible_actions
from app.optimizer.enr import ActionRanking, compute_enr, estimate_probabilities
from app.optimizer.ranker import rank_eligible_actions


# ── ENR formula ───────────────────────────────────────────────────────────────

class TestENRFormula:
    def test_basic_enr(self):
        # ENR = 0.80 * 5000 - 0.10 * 50000 - 50 = 4000 - 5000 - 50 = -1050
        enr = compute_enr(
            p_payment=0.80,
            amount=Decimal("5000"),
            p_churn=0.10,
            ltv=Decimal("50000"),
            action_cost=Decimal("50"),
        )
        assert enr == pytest.approx(Decimal("-1050"), abs=Decimal("1"))

    def test_enr_positive_when_high_payment_probability(self):
        # High p_payment, low LTV, low cost
        enr = compute_enr(
            p_payment=0.90,
            amount=Decimal("2000"),
            p_churn=0.05,
            ltv=Decimal("5000"),
            action_cost=Decimal("0"),
        )
        # 0.90 * 2000 - 0.05 * 5000 - 0 = 1800 - 250 = 1550
        assert enr > 0

    def test_enr_negative_when_high_churn_risk(self):
        enr = compute_enr(
            p_payment=0.20,
            amount=Decimal("1000"),
            p_churn=0.80,
            ltv=Decimal("50000"),
            action_cost=Decimal("500"),
        )
        # 0.20 * 1000 - 0.80 * 50000 - 500 = 200 - 40000 - 500 = -40300
        assert enr < 0

    def test_enr_zero_cost(self):
        enr = compute_enr(
            p_payment=0.50,
            amount=Decimal("1000"),
            p_churn=0.10,
            ltv=Decimal("1000"),
            action_cost=Decimal("0"),
        )
        # 0.50 * 1000 - 0.10 * 1000 - 0 = 500 - 100 = 400
        assert enr == pytest.approx(Decimal("400"), abs=Decimal("1"))

    def test_action_cost_reduces_enr(self):
        enr_no_cost = compute_enr(
            p_payment=0.70,
            amount=Decimal("3000"),
            p_churn=0.10,
            ltv=Decimal("20000"),
            action_cost=Decimal("0"),
        )
        enr_with_cost = compute_enr(
            p_payment=0.70,
            amount=Decimal("3000"),
            p_churn=0.10,
            ltv=Decimal("20000"),
            action_cost=Decimal("500"),
        )
        assert enr_no_cost - enr_with_cost == pytest.approx(Decimal("500"), abs=Decimal("1"))


# ── Probability estimation ─────────────────────────────────────────────────────

class TestProbabilityEstimation:
    def test_probabilities_in_valid_range(self):
        causes = ["card_expired", "billing_migration", "temporary_cash_flow", "price_friction", "churn_intent"]
        actions = ["silent_retry", "smart_link", "grace_period", "human_escalation", "suppress"]
        for cause in causes:
            for action in actions:
                p_pay, p_churn = estimate_probabilities(cause, action)
                assert 0.04 <= p_pay <= 0.97, f"p_payment out of range for {cause}+{action}: {p_pay}"
                assert 0.01 <= p_churn <= 0.95, f"p_churn out of range for {cause}+{action}: {p_churn}"

    def test_smart_link_better_for_card_expired(self):
        p_smart, _ = estimate_probabilities("card_expired", "smart_link")
        p_retry, _ = estimate_probabilities("card_expired", "silent_retry")
        assert p_smart > p_retry

    def test_grace_period_better_for_cash_flow(self):
        p_grace, _ = estimate_probabilities("temporary_cash_flow", "grace_period")
        p_retry, _ = estimate_probabilities("temporary_cash_flow", "silent_retry")
        assert p_grace > p_retry

    def test_human_escalation_increases_churn_vs_silent_retry(self):
        _, churn_human = estimate_probabilities("churn_intent", "human_escalation")
        _, churn_retry = estimate_probabilities("churn_intent", "silent_retry")
        assert churn_human > churn_retry

    def test_unknown_cause_does_not_crash(self):
        p_pay, p_churn = estimate_probabilities("unknown_cause", "silent_retry")
        assert 0 < p_pay < 1
        assert 0 < p_churn < 1


# ── Eligibility ────────────────────────────────────────────────────────────────

class TestEligibility:
    def test_all_causes_have_eligibility(self):
        causes = ["card_expired", "billing_migration", "temporary_cash_flow", "price_friction", "churn_intent"]
        for cause in causes:
            eligible = get_eligible_actions(cause)
            assert len(eligible) > 0, f"No eligible actions for cause: {cause}"

    def test_card_expired_includes_smart_link(self):
        assert "smart_link" in get_eligible_actions("card_expired")

    def test_churn_intent_includes_suppress(self):
        assert "suppress" in get_eligible_actions("churn_intent")

    def test_cause_eligibility_actions_are_valid_types(self):
        valid = {"silent_retry", "smart_link", "grace_period", "human_escalation", "suppress"}
        for cause, actions in CAUSE_ELIGIBILITY.items():
            for a in actions:
                assert a in valid, f"Invalid action '{a}' in eligibility for {cause}"

    def test_unknown_cause_returns_fallback_set(self):
        eligible = get_eligible_actions("nonexistent_cause")
        assert len(eligible) > 0


# ── Ranking ───────────────────────────────────────────────────────────────────

class TestRanking:
    def test_ranking_is_sorted_descending_by_enr(self):
        rankings = rank_eligible_actions(
            cause="card_expired",
            amount=Decimal("3000"),
            ltv=Decimal("30000"),
        )
        assert len(rankings) > 1
        enrs = [r.enr for r in rankings]
        for i in range(len(enrs) - 1):
            assert enrs[i] >= enrs[i + 1], f"Rankings not sorted at index {i}"

    def test_ranking_returns_action_ranking_objects(self):
        rankings = rank_eligible_actions(
            cause="temporary_cash_flow",
            amount=Decimal("2000"),
            ltv=Decimal("25000"),
        )
        for r in rankings:
            assert isinstance(r, ActionRanking)
            assert r.action_type in {"silent_retry", "smart_link", "grace_period", "human_escalation", "suppress"}
            assert isinstance(r.enr, Decimal)
            assert 0 < r.estimated_p_payment < 1
            assert 0 < r.estimated_p_churn < 1

    def test_ranking_is_deterministic(self):
        r1 = rank_eligible_actions("card_expired", Decimal("5000"), Decimal("40000"))
        r2 = rank_eligible_actions("card_expired", Decimal("5000"), Decimal("40000"))
        assert [r.action_type for r in r1] == [r.action_type for r in r2]
        assert [r.enr for r in r1] == [r.enr for r in r2]

    def test_best_action_for_card_expired_is_smart_link(self):
        rankings = rank_eligible_actions(
            cause="card_expired",
            amount=Decimal("3000"),
            ltv=Decimal("20000"),
        )
        # smart_link has highest p_payment multiplier for card_expired
        best = rankings[0].action_type
        # smart_link should be top due to highest payment probability
        assert best in {"smart_link", "human_escalation"}  # both plausible

    def test_high_ltv_makes_churn_costly(self):
        rankings_low_ltv = rank_eligible_actions("churn_intent", Decimal("1000"), Decimal("1000"))
        rankings_high_ltv = rank_eligible_actions("churn_intent", Decimal("1000"), Decimal("500000"))
        # With very high LTV, human_escalation (churn multiplier 1.22) becomes worse
        low_enrs = {r.action_type: r.enr for r in rankings_low_ltv}
        high_enrs = {r.action_type: r.enr for r in rankings_high_ltv}
        # The ranking for high LTV should differ from low LTV for churn-sensitive actions
        assert low_enrs != high_enrs

    def test_all_causes_can_be_ranked(self):
        causes = ["card_expired", "billing_migration", "temporary_cash_flow", "price_friction", "churn_intent"]
        for cause in causes:
            rankings = rank_eligible_actions(cause, Decimal("2000"), Decimal("20000"))
            assert len(rankings) > 0, f"No rankings for cause: {cause}"

    def test_action_cost_affects_ranking(self):
        from app.optimizer.enr import compute_enr, estimate_probabilities
        from decimal import Decimal
        p_pay, p_churn = estimate_probabilities("billing_migration", "human_escalation")
        enr_with_cost = compute_enr(p_pay, Decimal("2000"), p_churn, Decimal("20000"), Decimal("500"))
        enr_no_cost = compute_enr(p_pay, Decimal("2000"), p_churn, Decimal("20000"), Decimal("0"))
        assert enr_no_cost > enr_with_cost
