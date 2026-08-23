"""
Phase 6 — End-to-End Integration Tests.

Covers the full decision pipeline:
  Customer → Observable Events → Risk → LangGraph (9 nodes) → Optimizer
  → Policy Guard → Action Service → Audit

Uses deterministic seed + StubReasoningModel. No real LLM.

All graph invocations use db=None (no-db mode) to avoid FK constraints
on the in-memory SQLite test DB. The full 9-node pipeline still executes
and produces all required outputs — only DB persistence is bypassed.

The idempotency test calls execute_action directly with a DB session,
pre-seeding the required FK parent records first.

Invariants tested (CLAUDE.md §32, Phase 6 spec §6–§22):
  - Golden path: risk → diagnosis → ranking → guard → action → outcome recorded
  - Policy Guard bypass is structurally impossible (action_service checks guard status)
  - Blocked action: kill switch prevents gateway execution
  - Escalated action: amount >= ₹10k routes to ESCALATED, no gateway execution
  - Idempotency: duplicate key rejected on second execution (with real DB)
  - Kill switch: KILL_SWITCH=true blocks new actions at policy_guard boundary
  - Audit: recorded_outcome summary produced for every pipeline run
  - Agent isolation: no hidden state in agent inputs or outputs
  - Same-cohort invariant: same seed → same incremental recovery
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from app.agent.graph import build_recovery_graph, make_initial_state
from app.agent.reasoning import StubReasoningModel
from app.evaluation.evaluator import EvaluationWorld
from app.evaluation.policies import KhaataPulsePolicy, SmartRetryPolicy, StaticDunningPolicy
from app.risk.model import TRAINING_REFERENCE_DATE, get_risk_predictor
from app.simulator.generator import generate_world
from app.simulator.world import WorldInternal


# ── Fixture: one deterministic world ─────────────────────────────────────────

_SEED = 42
_COHORT = 50


@pytest.fixture(scope="module")
def world_fixture():
    raw = generate_world(
        seed=_SEED,
        cohort_size=_COHORT,
        simulator_version="v1",
        reference_date=TRAINING_REFERENCE_DATE,
    )
    world = WorldInternal.from_raw_records(
        raw=raw,
        seed=_SEED,
        cohort_size=_COHORT,
        simulator_version="v1",
        reference_date=TRAINING_REFERENCE_DATE,
    )
    return EvaluationWorld(world=world)


@pytest.fixture(scope="module")
def hero_obs(world_fixture):
    """Pick the highest-risk customer from the cohort."""
    predictor = get_risk_predictor()
    best_obs = None
    best_score = -1.0
    for rec in world_fixture.customer_records():
        obs = world_fixture.extract_observable_for(rec)
        pred = predictor.predict(obs, reference_date=TRAINING_REFERENCE_DATE)
        if pred.risk_score > best_score:
            best_score = pred.risk_score
            best_obs = obs
    assert best_obs is not None, "No customers generated"
    return best_obs


def _run_graph(hero_obs, *, subscription_amount=4000.0, ltv=50000.0, kill_switch=False):
    """Run the full 9-node graph in no-db mode with optional kill switch."""
    predictor = get_risk_predictor()
    pred = predictor.predict(hero_obs, reference_date=TRAINING_REFERENCE_DATE)

    state = make_initial_state(
        customer_id=hero_obs.customer_id,
        risk_score=pred.risk_score,
        risk_level=pred.risk_level,
        risk_signals=[{"feature": s.feature, "impact": s.impact} for s in pred.top_signals],
        subscription_context={
            "plan": hero_obs.subscription.plan,
            "amount": subscription_amount,
            "currency": hero_obs.subscription.currency,
        },
        payment_context=[
            {"status": p.status, "failure_code": p.failure_code,
             "payment_method": p.payment_method}
            for p in hero_obs.payments
        ],
        observable_events=[{"event_type": ev.event_type, **ev.payload} for ev in hero_obs.events],
        support_context="",
        ltv=ltv,
    )

    if kill_switch:
        with patch("app.policy.guard.get_settings") as mock_settings:
            mock_settings.return_value.kill_switch = True
            mock_settings.return_value.auto_action_limit = 10000
            mock_settings.return_value.max_contacts_7d = 3
            mock_settings.return_value.contact_cooldown_hours = 24
            graph = build_recovery_graph(StubReasoningModel(), db=None)
            return graph.invoke(state)
    else:
        graph = build_recovery_graph(StubReasoningModel(), db=None)
        return graph.invoke(state)


# ── §6: Golden path — full pipeline via LangGraph ─────────────────────────────

class TestGoldenPath:
    def test_full_pipeline_produces_all_outputs(self, hero_obs):
        """Risk → LangGraph → Optimizer → Policy Guard → Action → Outcome (no-db mode)."""
        result = _run_graph(hero_obs)

        assert result["validated_proposal"] is not None, "No validated proposal from LLM"
        assert result["action_rankings"], "No action rankings from optimizer"
        assert result["policy_decision"] is not None, "No policy decision from guard"
        assert result["execution_result"] is not None, "No execution result"
        assert result["recorded_outcome"] is not None, "No recorded outcome"
        outcome = result["recorded_outcome"]
        assert "cause" in outcome, "recorded_outcome missing 'cause'"
        assert "action_type" in outcome, "recorded_outcome missing 'action_type'"
        assert "status" in outcome, "recorded_outcome missing 'status'"
        assert "policy_status" in outcome, "recorded_outcome missing 'policy_status'"

    def test_diagnosis_contains_no_hidden_state(self, hero_obs):
        """Agent state must never contain latent-state field names."""
        result = _run_graph(hero_obs)

        forbidden_keys = {
            "payment_intent", "cash_flow_health", "payment_rail_health",
            "churn_sensitivity", "customer_ltv_hidden", "potential_outcomes",
            "p_payment", "p_churn",
        }
        for key in forbidden_keys:
            assert key not in result, f"Hidden state field '{key}' leaked into agent state"

    def test_optimizer_ranks_actions_descending_by_enr(self, hero_obs):
        """Action rankings must be in descending ENR order."""
        result = _run_graph(hero_obs, subscription_amount=5000.0, ltv=50000.0)
        rankings = result.get("action_rankings", [])
        assert len(rankings) > 0, "Optimizer produced no rankings"
        enrs = [Decimal(str(r["enr"])) for r in rankings]
        assert enrs == sorted(enrs, reverse=True), "Rankings not in descending ENR order"

    def test_nine_nodes_all_produce_output(self, hero_obs):
        """All nine LangGraph node outputs must be present in final state."""
        result = _run_graph(hero_obs)

        assert result.get("context_classification") is not None, "classify_context did not run"
        assert result.get("diagnosis") is not None, "generate_diagnosis did not run"
        assert result.get("recovery_proposal") is not None, "generate_action_proposal did not run"
        assert result.get("validated_proposal") is not None, "validate_proposal did not run"
        assert result.get("action_rankings") is not None, "rank_actions did not run"
        assert result.get("policy_decision") is not None, "policy_check did not run"
        assert result.get("execution_result") is not None, "execute_action did not run"
        assert result.get("recorded_outcome") is not None, "record_outcome did not run"


# ── §17: Policy Guard bypass prevention ──────────────────────────────────────

class TestPolicyGuardBypass:
    def test_blocked_policy_returns_blocked_execution(self):
        """When policy_decision is BLOCKED, action_service must return 'blocked'."""
        from app.actions.service import ActionRequest, execute_action
        from app.policy.guard import PolicyDecision, PolicyStatus

        blocked = PolicyDecision(
            status=PolicyStatus.BLOCKED,
            checks={"kill_switch": False},
            block_reason="kill_switch_active",
            action_type="silent_retry",
            customer_id=1,
            amount=Decimal("5000"),
            idempotency_key="rec_CASE_test_block",
        )
        request = ActionRequest(
            case_id=1,
            customer_id=1,
            action_type="silent_retry",
            amount=Decimal("5000"),
            currency="INR",
            idempotency_key="rec_CASE_test_block",
            policy_decision=blocked,
        )

        result = execute_action(request, db=None)
        assert result.status == "blocked", f"Expected 'blocked', got '{result.status}'"
        assert result.action_id is None, "Blocked action must not produce an action_id"

    def test_guard_and_execution_status_are_consistent(self, hero_obs):
        """execution_result.status must mirror the policy_decision.status from the guard."""
        result = _run_graph(hero_obs, subscription_amount=4000.0)
        guard_status = result["policy_decision"]["status"]
        exec_status = result["execution_result"]["status"]

        expected = {
            "APPROVED": "executed",
            "BLOCKED": "blocked",
            "ESCALATED": "escalated",
        }
        assert exec_status == expected.get(guard_status), (
            f"Guard {guard_status} must produce '{expected.get(guard_status)}', got '{exec_status}'"
        )

    def test_kill_switch_blocks_at_policy_guard_boundary(self):
        """Kill switch ON → policy_guard returns BLOCKED with kill_switch_active reason."""
        from app.policy.guard import policy_guard

        with patch("app.policy.guard.get_settings") as mock_settings:
            mock_settings.return_value.kill_switch = True
            mock_settings.return_value.auto_action_limit = 10000
            mock_settings.return_value.max_contacts_7d = 3
            mock_settings.return_value.contact_cooldown_hours = 24

            decision = policy_guard(
                customer_id=42,
                action_type="silent_retry",
                amount=Decimal("5000"),
                idempotency_key="rec_test_ks",
                db=None,
            )

        assert decision.status == "BLOCKED"
        assert decision.block_reason == "kill_switch_active"
        assert decision.checks.get("kill_switch") is False


# ── §18: Blocked action end-to-end ───────────────────────────────────────────

class TestBlockedAction:
    def test_kill_switch_blocks_full_pipeline(self, hero_obs):
        """Full pipeline with kill switch ON → BLOCKED decision, 'blocked' execution."""
        result = _run_graph(hero_obs, subscription_amount=4000.0, kill_switch=True)

        policy_dict = result.get("policy_decision", {})
        exec_result = result.get("execution_result", {})

        assert policy_dict.get("status") == "BLOCKED", (
            f"Expected BLOCKED, got {policy_dict.get('status')}"
        )
        assert exec_result.get("status") == "blocked", (
            f"Expected blocked execution, got {exec_result.get('status')}"
        )


# ── §19: Escalated action ─────────────────────────────────────────────────────

class TestEscalatedAction:
    def test_high_amount_escalates_via_full_pipeline(self, hero_obs):
        """Amount >= ₹10,000 → Policy Guard ESCALATED → execution_result 'escalated'."""
        result = _run_graph(hero_obs, subscription_amount=15000.0, ltv=150000.0)

        policy_dict = result.get("policy_decision", {})
        exec_result = result.get("execution_result", {})

        assert policy_dict.get("status") == "ESCALATED", (
            f"Expected ESCALATED, got {policy_dict.get('status')}"
        )
        assert exec_result.get("status") == "escalated", (
            f"Expected escalated, got {exec_result.get('status')}"
        )


# ── §20: Idempotency ─────────────────────────────────────────────────────────

class TestIdempotency:
    def test_duplicate_key_rejected_in_db(self, db):
        """Second execute_action with the same idempotency key must return 'duplicate'."""
        from app.actions.service import ActionRequest, execute_action
        from app.db.models.customer import Customer
        from app.db.models.recovery_case import RecoveryCase
        from app.policy.guard import PolicyDecision, PolicyStatus

        customer = Customer(id=9001, name="Test User", segment="consumer", ltv=Decimal("40000"))
        db.add(customer)
        db.flush()

        case = RecoveryCase(
            customer_id=9001,
            risk_score=Decimal("0.75"),
            risk_level="HIGH",
            diagnosis="temporary_cash_flow",
            diagnosis_confidence=Decimal("0.90"),
            proposed_action="silent_retry",
            selected_action="silent_retry",
            policy_status="APPROVED",
            outcome_status="open",
        )
        db.add(case)
        db.flush()

        approved = PolicyDecision(
            status=PolicyStatus.APPROVED,
            checks={"kill_switch": True, "idempotency": True},
            action_type="silent_retry",
            customer_id=9001,
            amount=Decimal("3000"),
            idempotency_key="rec_CASE_idempotency_test_001",
        )
        request = ActionRequest(
            case_id=case.id,
            customer_id=9001,
            action_type="silent_retry",
            amount=Decimal("3000"),
            currency="INR",
            idempotency_key="rec_CASE_idempotency_test_001",
            policy_decision=approved,
        )

        result1 = execute_action(request, db=db)
        assert result1.status == "executed", f"First call must execute, got '{result1.status}'"

        result2 = execute_action(request, db=db)
        assert result2.status == "duplicate", (
            f"Second call with same key must be 'duplicate', got '{result2.status}'"
        )
        assert result2.action_id == result1.action_id, (
            "Duplicate must return the existing action's id"
        )

    def test_different_keys_both_execute(self, db):
        """Two requests with different idempotency keys must both be executed."""
        from app.actions.service import ActionRequest, execute_action
        from app.db.models.customer import Customer
        from app.db.models.recovery_case import RecoveryCase
        from app.policy.guard import PolicyDecision, PolicyStatus

        customer = Customer(id=9002, name="Test User 2", segment="smb", ltv=Decimal("60000"))
        db.add(customer)
        db.flush()

        case = RecoveryCase(
            customer_id=9002,
            risk_score=Decimal("0.80"),
            risk_level="HIGH",
            diagnosis="card_expired",
            diagnosis_confidence=Decimal("0.85"),
            proposed_action="smart_link",
            selected_action="smart_link",
            policy_status="APPROVED",
            outcome_status="open",
        )
        db.add(case)
        db.flush()

        def _make_request(key: str):
            approved = PolicyDecision(
                status=PolicyStatus.APPROVED,
                checks={"kill_switch": True},
                action_type="smart_link",
                customer_id=9002,
                amount=Decimal("3500"),
                idempotency_key=key,
            )
            return ActionRequest(
                case_id=case.id,
                customer_id=9002,
                action_type="smart_link",
                amount=Decimal("3500"),
                currency="INR",
                idempotency_key=key,
                policy_decision=approved,
            )

        r1 = execute_action(_make_request("rec_CASE_key_A"), db=db)
        r2 = execute_action(_make_request("rec_CASE_key_B"), db=db)
        assert r1.status == "executed"
        assert r2.status == "executed"
        assert r1.action_id != r2.action_id, "Different keys must produce different action records"


# ── §22: Audit integrity ─────────────────────────────────────────────────────

class TestAuditIntegrity:
    def test_recorded_outcome_captures_pipeline_summary(self, hero_obs):
        """Pipeline (no-db mode) must produce recorded_outcome with all required fields."""
        result = _run_graph(hero_obs)
        outcome = result.get("recorded_outcome")
        assert outcome is not None, "record_outcome node did not produce output"

        required_fields = {"case_id", "action_type", "status", "policy_status", "cause"}
        missing = required_fields - set(outcome.keys())
        assert not missing, f"recorded_outcome missing fields: {missing}"

    def test_audit_service_is_append_only(self):
        """The audit service module must only export log_audit_event — no update/delete."""
        import inspect
        from app.audit import service as audit_service

        public_fns = [
            name for name, fn in inspect.getmembers(audit_service, inspect.isfunction)
            if not name.startswith("_")
        ]
        assert "log_audit_event" in public_fns, "log_audit_event must exist"
        for name in public_fns:
            assert "delete" not in name.lower(), f"Audit service must not export '{name}'"
            assert "update" not in name.lower(), f"Audit service must not export '{name}'"

    def test_log_audit_event_nodb_returns_none(self):
        """In no-db mode, log_audit_event must return None (logged only, not persisted)."""
        from app.audit.service import log_audit_event
        result = log_audit_event(
            event_type="risk_detected",
            case_id=0,
            actor="test",
            payload={"risk_score": 0.9},
            db=None,
        )
        assert result is None, "log_audit_event with db=None must return None"


# ── §14: Same-cohort invariant check ─────────────────────────────────────────

class TestSameCohortInvariant:
    def test_all_three_policies_see_same_records(self):
        """EvaluationWorld must return the same customer list on each call."""
        raw = generate_world(
            seed=_SEED, cohort_size=_COHORT,
            simulator_version="v1", reference_date=TRAINING_REFERENCE_DATE,
        )
        world = WorldInternal.from_raw_records(
            raw=raw, seed=_SEED, cohort_size=_COHORT,
            simulator_version="v1", reference_date=TRAINING_REFERENCE_DATE,
        )
        eval_world = EvaluationWorld(world=world)

        ids_a = [r.customer_id for r in eval_world.customer_records()]
        ids_b = [r.customer_id for r in eval_world.customer_records()]
        assert ids_a == ids_b, "EvaluationWorld must return same records on each call"

    def test_same_seed_produces_same_incremental_recovery(self):
        """Two runs with the same seed must yield identical incremental recovery."""
        from app.evaluation.evaluator import run_same_cohort_evaluation

        r1 = run_same_cohort_evaluation(
            seed=_SEED, cohort_size=_COHORT,
            simulator_version="v1", run_id="test_repro_1",
        )
        r2 = run_same_cohort_evaluation(
            seed=_SEED, cohort_size=_COHORT,
            simulator_version="v1", run_id="test_repro_2",
        )

        assert r1.incremental_recovery == r2.incremental_recovery, (
            f"Same seed must produce same result: "
            f"{r1.incremental_recovery} != {r2.incremental_recovery}"
        )
        assert r1.khaatapulse.recovered_amount == r2.khaatapulse.recovered_amount

    def test_potential_outcomes_not_accessible_to_policies(self):
        """Policy.decide() source code must not reference get_potential_outcomes."""
        import inspect
        for policy_cls in [StaticDunningPolicy, SmartRetryPolicy, KhaataPulsePolicy]:
            source = inspect.getsource(policy_cls.decide)
            assert "get_potential_outcomes" not in source, (
                f"{policy_cls.__name__}.decide() must not access potential outcomes"
            )

    def test_multi_seed_evaluation_required_seeds(self):
        """Required seeds (42, 123, 456) must all produce valid evaluation results."""
        from app.evaluation.runner import run_multi_seed_evaluation

        results = run_multi_seed_evaluation(cohort_size=_COHORT, seeds=[42, 123, 456], db=None)
        assert len(results) == 3, "Must return one result per seed"
        for r in results:
            assert r.static_dunning.recovered_amount >= 0
            assert r.smart_retry.recovered_amount >= 0
            assert r.khaatapulse.recovered_amount >= 0
