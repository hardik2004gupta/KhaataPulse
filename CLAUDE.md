# KhaataPulse — Engineering Contract

## Authority Hierarchy

```
KhaataPulse — Architectural MVP Engineering Contract.pdf   ← original specification
                          ↓
                      CLAUDE.md                            ← executable engineering contract
                          ↓
                  Implementation / Code
```

`KhaataPulse — Architectural MVP Engineering Contract.pdf` is the authoritative product and architecture specification.  
`CLAUDE.md` translates that specification into enforceable engineering rules.  
All future implementation must comply with both. When the PDF specifies a requirement explicitly, follow it — do not substitute with assumptions, convenience, or familiar patterns.

---

## 1. Project Identity

- **Product:** KhaataPulse — AI Revenue Recovery Policy Engine
- **Primary Scenario:** Subscription renewal payment risk
- **Version:** MVP 1.0 (Frozen specification)
- **Central engineering claim:** KhaataPulse can identify payment friction before failure and evaluate whether its recovery policy produces better expected revenue outcomes than existing dunning policies, without exceeding predefined customer-contact and escalation boundaries.

KhaataPulse is NOT a payment processor, collections platform, or autonomous financial system. It is a **controlled revenue-recovery policy evaluation environment**.

---

## 2. Product Definition

KhaataPulse detects subscription payment risk before failure, understands the reason behind the risk, proposes a recovery intervention, evaluates its expected financial value, enforces deterministic policy constraints, and measures the resulting policy performance against established recovery strategies.

It demonstrates this pipeline:

```
Detect → Diagnose → Optimize → Guard → Act → Measure → Audit
```

---

## 3. Core Engineering Principles

These are architectural constraints, not optional design preferences:

1. **ML finds risk.** The risk model determines which accounts deserve additional reasoning. It does not execute recovery actions.
2. **AI understands context.** The LLM handles semi-structured information (support text, payment error context, billing explanations, cancellation feedback, customer intent signals). The LLM does not directly call payment APIs.
3. **Optimization determines economics.** Expected Net Revenue determines which eligible intervention is financially preferable.
4. **Policy determines authority.** The Policy Guard is deterministic. The LLM cannot override it.
5. **Every action is auditable.** Every meaningful decision produces an immutable audit event.
6. **The simulator is independent.** The agent must never access latent customer variables, counterfactual outcomes, hidden simulator state, or ground-truth action probabilities.
7. **No hardcoded headline metrics.** Dashboard metrics must originate from an evaluation run. Never hardcode values like `₹95,000 recovered`, `66.4% recovery`, or `+6.2pp lift`.

---

## 4. Technology Stack

Do not substitute any of these without explicit architectural approval:

| Layer | Technology |
|---|---|
| Frontend | Next.js + TypeScript |
| Backend | FastAPI + Python |
| Database | PostgreSQL |
| Agent Orchestration | LangGraph |
| Risk Model | Scikit-learn Logistic Regression |
| LLM | Structured-output reasoning model |
| Deployment | Docker / Vercel + Railway-compatible |

Local development must work with:
```
docker compose up
```
Services: `frontend`, `backend`, `postgres`. Optional: `llm provider`. Demo mode must work even if the external LLM is unavailable.

---

## 5. Non-Negotiable Architecture

The full pipeline is:

```
CUSTOMER WORLD
      ↓
OBSERVABLE DATA
      ↓
RISK SIEVE (Logistic Regression)
      ↓
AI REASONER (LangGraph)
      ↓
ECONOMIC RANKER (Expected Net Revenue)
      ↓
POLICY GUARD (Deterministic)
      ↓
EXECUTE / STOP
      ↓
AUDIT LOG
      ↓
OUTCOME ENGINE
      ↓
POLICY EVALUATION (Static vs Smart vs KhaataPulse)
      ↓
INCREMENTAL RECOVERY
```

No layer may bypass the layer immediately below it.

---

## 6. Architectural Boundaries

The system has five hard boundaries. No boundary may be crossed in either direction:

```
SIMULATION WORLD
Hidden states + potential outcomes
      |
      | observable events only
      ↓
CORE AGENT
Risk → Diagnosis → Proposal → Optimization
      |
      ↓
POLICY LAYER
Deterministic authorization / stopping rules
      |
      ↓
ACTION LAYER
Typed, idempotent simulated gateway operations
      |
      ↓
EVALUATION
Baselines → outcomes → incremental recovery
```

---

## 7. Simulator Isolation Rules

The simulator represents the customer environment. It contains:

- **Hidden state** — `CustomerLatentState(payment_intent, cash_flow_health, payment_rail_health, churn_sensitivity, customer_ltv)` — the agent must **never** receive this object.
- **Observable events** — generated from latent state: `invoice_viewed`, `checkout_reopened`, `payment_method_changed`, `payment_failed`, `subscription_changed`, `support_message`, `payment_delayed`, `renewal_approaching`. These are the **only** data the agent may receive from the simulator.
- **Potential outcomes** — for each customer and action: `P(payment | action)` and `P(churn | action)`. These are generated independently of the agent. The agent does not see them. Only the evaluation harness uses them to calculate policy performance.

Simulator violations are critical defects. Any code path that exposes hidden state or potential outcomes to the agent is forbidden.

---

## 8. Risk Sieve Rules

- **Model:** Scikit-learn Logistic Regression only.
- **Input:** Observable customer features only (never latent state).
- **Output:** `payment_failure_probability` (float 0.0–1.0).
- **Routing threshold:**
  - `P(failure) < 0.30` → Standard Flow
  - `P(failure) >= 0.30` → LangGraph (~350 cases from 3,000 cohort)
- The risk model is a **compute and reasoning gate**, not the final recovery policy.
- **Explainability contract:** Every risk decision must expose `risk_score` and `top_signals` (list of `{feature, impact}`). The frontend must display the top three signals.

**Minimum feature set:**
```
days_to_renewal, invoice_views, checkout_reopens,
payment_method_changes, previous_payment_failures,
average_payment_delay, subscription_age,
payment_success_rate, support_event_count, days_since_last_payment
```

**Optional features:** `payment_failure_code`, `renewal_amount`, `plan_type`, `customer_tenure`

---

## 9. LangGraph Rules

The LangGraph agent graph must contain exactly these nodes in this order:

```
START
  ↓
classify_context
  ↓
generate_diagnosis
  ↓
generate_action_proposal
  ↓
validate_proposal
  ↓
rank_actions
  ↓
policy_check
  ↓
execute_action
  ↓
record_outcome
  ↓
END
```

- The graph must remain **single-stage**.
- Do **not** introduce autonomous agent-to-agent conversations.
- Do not split into multi-agent architectures.

---

## 10. LLM Responsibility Rules

The LLM receives (observable data only):
```
risk_score
observable event history
payment failure context
support text
subscription information
```

The LLM must produce:
```
cause
confidence
proposed_action
risk_level
rationale
```

The LLM must **NOT**:
- access hidden latent state
- calculate final revenue metrics
- bypass Policy Guard
- directly invoke gateway actions
- decide whether an action is legally permitted

---

## 11. Structured Output Contract

All LLM responses must validate against this Pydantic model:

```python
class RecoveryProposal(BaseModel):
    cause: Literal[
        "billing_migration",
        "temporary_cash_flow",
        "card_expired",
        "price_friction",
        "churn_intent"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    proposed_action: Literal[
        "silent_retry",
        "smart_link",
        "grace_period",
        "human_escalation",
        "suppress"
    ]
    rationale: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
```

Any response that does not validate against this schema is a failure and must trigger the fallback contract.

---

## 12. LLM Failure / Fallback Contract

Every LLM call must be treated as unreliable. Failures include: timeout, malformed JSON, invalid enum, missing required field, provider error, schema validation failure.

Required fallback chain:
```
LLM failure
      ↓
Smart Rule baseline
      ↓
Policy Guard
      ↓
Continue
```

Every failure must be logged with:
```json
{
  "event": "llm_fallback",
  "reason": "<failure_type>",
  "fallback_policy": "smart_retry"
}
```

A **single LLM failure must never terminate an evaluation batch**. Every fallback must be auditable.

---

## 13. Economic Optimization Rules

The Expected Net Revenue formula is the only financial ranking authority:

```
ExpectedNetRevenue = P(payment | action) × Amount
                   − P(churn | action) × LTV
                   − ActionCost
```

The LLM's diagnosis narrows the eligible action space. The deterministic optimizer performs the financial ranking among eligible actions. The LLM must not become the financial authority.

---

## 14. Policy Guard Rules

The Policy Guard is pure deterministic code:

```python
policy_check(action, customer, case) -> PolicyDecision
```

It must be:
- **Deterministic** — same inputs always produce same output
- **Pure** — no side effects
- **Independently unit-testable** — tested in complete isolation
- **Configuration-driven** — all thresholds come from environment config
- **Non-bypassable** — no code path may skip the Policy Guard

Policy rules (all configuration-driven via environment variables):

| Rule | Value |
|---|---|
| Maximum contacts | 3 / 7 days |
| Cooldown | 24 hours |
| Auto-action threshold | < ₹10,000 |
| Human approval threshold | >= ₹10,000 |
| Dispute hold | STOP |
| Legal hold | STOP |
| Opt-out | STOP |
| Kill switch | STOP |
| Idempotency | REQUIRED |

Every action produces a `PolicyDecision` with status `APPROVED`, `BLOCKED`, or `ESCALATED`, and a `checks` object showing which rules passed or failed.

---

## 15. Action Execution Rules

Every action must carry these required fields:

```
action_id, case_id, customer_id, action_type,
amount, currency, idempotency_key, timestamp, policy_result
```

Example idempotency key format: `rec_CASE_1042`

Valid action types: `silent_retry`, `smart_link`, `grace_period`, `human_escalation`, `suppress`

The action service must reject duplicate execution (same idempotency key). Repeated execution of the same action must not produce duplicate recovery actions.

---

## 16. Auditability Requirements

Every meaningful decision produces an immutable `AuditEvent`:

```
AuditEvent: id, case_id, event_type, actor, payload, timestamp, idempotency_key
```

The `payload` must preserve structured information required for reconstruction. The audit drawer must show events in chronological order with expandable payloads. Gateway payload viewer must use monospace typography and syntax highlighting.

Required audit event types: `risk_detected`, `diagnosis_generated`, `action_proposed`, `policy_check`, `action_executed`, `payment_received`, `case_closed`, `llm_fallback`.

---

## 17. Evaluation Integrity Rules

This is one of the most important rules in the entire project.

**CORRECT — same world, different policies:**
```python
world = generate_world(seed)
static_result  = evaluate(world, static_dunning)
smart_result   = evaluate(world, smart_retry)
kp_result      = evaluate(world, khaatapulse)
```

**FORBIDDEN — separate worlds per policy:**
```python
evaluate(generate_world(), static_dunning)   # WRONG
evaluate(generate_world(), smart_retry)       # WRONG
evaluate(generate_world(), khaatapulse)       # WRONG
```

All three policies must operate against the **same cohort**, **same event history**, **same customer population**, **same potential outcomes**. Only the policy changes.

The evaluator must dynamically calculate (never hardcode):
```
recovered_amount, recovery_rate, incremental_recovery,
contacts_sent, contacts_avoided, human_escalations,
false_positives, policy_blocks
```

**Multi-seed validation** — minimum required seeds: `42`, `123`, `456`. Recommended additional: `789`, `1337`.

Every evaluation run stores: `run_id`, `seed`, `cohort_size`, `timestamp`, `model_version`, `policy_version`, `simulator_version`, `metrics`.

**Evaluation API:**
```
POST /evaluation/run
  → { run_id, status, results: { static_dunning, smart_retry, khaatapulse } }
```
Evaluation is asynchronous: POST returns `evaluation_run_id`, frontend polls/subscribes for results.

---

## 18. Baseline Policies

Three policy implementations must exist and be maintained:

**Static Dunning:**
```
payment_failure → 24h retry → reminder → human_escalation
```

**Smart Retry:**
```
payment_failure → failure-code rules → deterministic retry timing → payment_link → escalation
```

**KhaataPulse:**
```
risk_detection → contextual_diagnosis → action_proposal → expected_net_revenue → policy_guard → action
```

**Primary KPI:**
```
Incremental Recovery = Recovery(KhaataPulse) − Recovery(Smart Retry)
```
The number must be generated dynamically. No target recovery amount may be hardcoded.

---

## 19. Data Model Contract

Minimum PostgreSQL entities:

```
customers        — id, name, segment, ltv, subscription_id, created_at
subscriptions    — id, customer_id, plan, amount, currency, renewal_at, status
payments         — id, customer_id, subscription_id, amount, status, failure_code, payment_method, created_at
events           — observable customer events (type, customer_id, payload, timestamp)
recovery_cases   — id, customer_id, risk_score, risk_level, diagnosis, diagnosis_confidence,
                   proposed_action, selected_action, policy_status, outcome_status, created_at, closed_at
actions          — id, case_id, customer_id, action_type, amount, currency,
                   idempotency_key, timestamp, policy_result
audit_events     — id, case_id, event_type, actor, payload, timestamp, idempotency_key
evaluation_runs  — id, seed, cohort_size, simulator_version, model_version, policy_version,
                   status, started_at, completed_at
evaluation_results — evaluation metrics per policy per run
```

Do not introduce unnecessary databases or infrastructure.

---

## 20. API Design Principles

- RESTful FastAPI endpoints
- All policy thresholds from environment config — never scattered as magic constants
- Evaluation endpoint is asynchronous (`POST /evaluation/run` → poll `GET /evaluation/run/{id}`)
- Structured error responses
- API keys server-side only — never exposed to the frontend

---

## 21. Security & Privacy

Even though the MVP uses synthetic data:

- Treat PII as sensitive
- Keep API keys server-side only
- Never expose secrets in frontend code
- Do not store payment credentials
- Send only required fields to the LLM
- Structure the architecture for future PII redaction
- Avoid unnecessary PII in audit logs
- No secret may be embedded in the frontend

---

## 22. Idempotency

Every executable action must carry an idempotency key (format: `rec_CASE_{id}`). The action service must reject duplicate execution. Repeated invocation of the same action with the same idempotency key must produce no additional side effects.

---

## 23. Kill Switch

A global merchant-level automation kill switch must exist:

```
AUTOMATION STATUS: ACTIVE   →   automated actions proceed
AUTOMATION STATUS: PAUSED   →   all new automated actions BLOCKED
```

When the kill switch is active (PAUSED):
- Risk detection continues
- All automated actions are blocked
- No action may execute

The kill switch state is controlled by the `KILL_SWITCH` environment variable and must be checked by the Policy Guard on every action.

---

## 24. Observability

The backend must expose/log at minimum:

```
request_latency, llm_latency, llm_failures, fallback_count,
policy_blocks, action_execution, evaluation_duration
```

Use structured logging. Basic structured logging is sufficient for MVP. Do not build unnecessary observability infrastructure.

---

## 25. Environment Configuration

All policy thresholds must come from environment variables — never scattered through code:

```
DATABASE_URL=
LLM_API_KEY=
LLM_MODEL=

APP_ENV=development

AUTO_ACTION_LIMIT=10000
MAX_CONTACTS_7D=3
CONTACT_COOLDOWN_HOURS=24

KILL_SWITCH=false
```

---

## 26. Demo Mode

Demo mode is a first-class requirement. It must support:
- Precomputed evaluation results
- Deterministic hero customer
- Cached LLM responses
- Simulated gateway actions
- Fully functional audit events

The 3-minute demo must not depend on: LLM availability, network reliability, API rate limits, long-running evaluation, or external payment systems.

---

## 27. Production Mode Boundary

Production architecture swaps the simulator's synthetic event generator for real payment webhooks, and the outcome simulator for real payment outcomes. The agent, policy layer, audit layer, and frontend architecture remain largely unchanged. Real payment processing is explicitly out of scope for the MVP.

---

## 28. Frontend Design Contract

The frontend is not a generic SaaS dashboard. It must feel like an **AI financial command center**.

Visual concept: **"Financial Intelligence × Mission Control"**

The interface must communicate: money, risk, precision, AI intelligence, real-time operations, trust, control.

Visual hierarchy:
```
MONEY → RISK → DECISION → CONTROL → OUTCOME
```

**Avoid:**
- Generic blue SaaS dashboards
- Excessive rounded cards
- Cartoon AI graphics
- Excessive gradients
- Generic chatbot styling
- Dashboard clutter
- Bouncing cards, excessive parallax, flashy particle effects, unnecessary page transitions

The frontend should make the architecture visible. KhaataPulse should visually communicate that **money is moving through an intelligent but controlled system**.

---

## 29. Design System Rules

**Color palette (dark financial terminal):**

| Token | Value | Semantic meaning |
|---|---|---|
| `--bg-primary` | `#07090D` | Primary background |
| `--bg-secondary` | `#0C1017` | Secondary |
| `--surface` | `#11161F` | Panel surface |
| `--surface-elevated` | (slightly lighter) | Elevated panels |
| `--accent-recovery` | Emerald | Recovery / positive |
| `--accent-warning` | Amber | Risk |
| `--accent-critical` | Red | Critical |
| `--accent-ai` | Electric violet / indigo | AI operations |
| Neutral data | Cool gray | Data / neutral |

**Typography:**
- UI: `Inter` (recommended) or `Geist`
- Financial metrics: tabular numerals
- Code / audit / payloads: `JetBrains Mono` for audit IDs, webhook payloads, timestamps, event names, policy decisions

**Target resolution:** 1440 × 900 desktop-first.

**Responsive fallbacks:**
- Tablet: sidebar collapsible, comparison matrix horizontally scrollable, audit drawer full-width
- Mobile: dashboard stacked, metrics 2-column grid, risk queue as cards, Time Machine vertical timeline

**Design tokens — centralize all:**
```
colors, spacing, radii, typography, shadows, motion, z-index
```

No arbitrary color values scattered throughout components. Color communicates semantic state, not decoration.

---

## 30. Required Frontend Components

Build these as reusable domain components:

```
MetricCard, PolicyBadge, RiskIndicator, CustomerRow,
EventTimeline, DiagnosisPanel, InterventionTable, PolicyGuard,
AuditDrawer, PayloadViewer, EvaluationMatrix, RecoveryDelta,
StatusBadge, LiveEventStream, SimulationButton
```

Do not create one-off implementations when a reusable domain component is appropriate.

**Key screens:**
- **Hero Dashboard** — `₹14.8L Revenue Exposure`, `₹X Recovered`, `+₹Y Incremental Recovery`, `-Z% Customer Contacts`. Incremental recovery number must visually dominate.
- **Policy Comparison Matrix** — Static vs Smart vs KhaataPulse. Emphasize the delta, not just the totals.
- **Revenue Time Machine** — cinematic customer state timeline; clicking events expands contextual information.
- **AI Diagnosis Panel** — cause, confidence bar, rationale, top signals.
- **Intervention Optimizer** — action ranked by Expected Net Revenue, showing selected action and rationale.
- **Policy Guard visualization** — feels like a security checkpoint showing sequential checks.
- **Audit Drawer** — enterprise event stream with expandable events and gateway payload viewer.
- **Live Webhook interaction** — `[SIMULATE PAYMENT WEBHOOK]` button triggers real-time animation of the full pipeline.

**Motion design** — motion communicates system state, not decoration:
- Risk detected: subtle amber pulse around affected account
- AI reasoning: small animated signal lines through diagnosis panel
- Policy check: sequential check indicators
- Approved: green confirmation sweep
- Blocked: short red interruption pulse
- Payment recovered: metric counter animates upward

---

## 31. Performance Requirements

| Surface | Requirement |
|---|---|
| Dashboard load (precomputed) | < 500ms perceived |
| Risk queue | Virtualize if necessary |
| Live case LLM response | Streamed or returned quickly |
| Batch evaluation | Non-blocking; never block the UI |

Evaluation runs asynchronously. The frontend must display progress.

---

## 32. Testing Requirements

Critical business boundaries must have tests. At minimum:

- Simulator isolation (hidden state never exposed to agent)
- Risk model training and prediction
- Risk threshold routing (< 0.30 → standard, ≥ 0.30 → LangGraph)
- LLM schema validation (RecoveryProposal)
- LLM fallback (all six failure types)
- Expected Net Revenue calculation
- Action ranking by ENR
- Policy Guard — all rules (cooldown, contact limit, consent, amount threshold, dispute hold, legal hold, opt-out, kill switch, idempotency)
- Blocked actions
- Escalated actions
- Same-cohort evaluation integrity
- Incremental recovery calculation
- Multi-seed evaluation (seeds 42, 123, 456)

Tests must prioritize business invariants over superficial coverage percentages.

---

## 33. Forbidden Technologies / Patterns

Do NOT introduce these unless a future explicit architectural change authorizes them:

```
Redis
Vector database
RAG (Retrieval-Augmented Generation)
Multi-agent debate / agent-to-agent conversation
Deep-learning risk model
Real payment processing
Production payment settlement
Production WhatsApp integration
Voice recovery
B2B collections
Checkout abandonment recovery
Promise-to-pay state machine
Autonomous legal escalation
```

Do not add infrastructure simply because it is familiar or fashionable.

---

## 34. Implementation Rules for Claude Code

**Rule 1 — Read CLAUDE.md first.** Before modifying code, understand the engineering contract.

**Rule 2 — Inspect existing code.** Never overwrite working code blindly.

**Rule 3 — Preserve architecture.** Do not redesign the system during implementation unless explicitly instructed.

**Rule 4 — Work incrementally.** Implement one coherent subsystem at a time.

**Rule 5 — Test after implementation.** Run relevant tests before declaring a phase complete.

**Rule 6 — Never fake functionality.** Do not replace backend logic with frontend mock data merely to make the UI look complete.

**Rule 7 — Never hardcode business metrics.** Evaluation metrics must originate from the evaluation engine. No target amounts, recovery rates, or lift values may be hardcoded.

**Rule 8 — Never bypass Policy Guard.** No code path may directly execute an LLM-proposed action without passing through the Policy Guard.

**Rule 9 — Never expose simulator secrets.** Hidden state (`CustomerLatentState`) and potential outcomes (`P(payment|action)`, `P(churn|action)`) must remain strictly inside the simulator. They must never appear in any interface visible to the agent.

**Rule 10 — Do not expand MVP scope.** If a feature is not required by the architectural contract, do not introduce it.

**Rule 11 — Configuration-driven policy constants.** All policy thresholds (contact limits, cooldown hours, amount thresholds) must come from environment configuration, not hardcoded in application logic.

**Rule 12 — Optimize for correctness, explainability, bounded execution, evaluation integrity, demo reliability, and visual quality.** Do not optimize for maximum number of agents, maximum LLM usage, maximum dashboard complexity, maximum model complexity, or maximum number of integrations.

---

## 35. Definition of Done

The MVP is complete only when all of the following are true:

```
[ ] 3,000 customer cohort generated
[ ] Hidden simulator state isolated (agent never receives CustomerLatentState)
[ ] Potential outcomes generated and isolated
[ ] Logistic Regression trained and operational
[ ] Risk sieve operational with threshold routing
[ ] LLM diagnosis operational
[ ] Pydantic validation operational
[ ] LLM fallback operational (all failure types handled)
[ ] Expected Net Revenue ranking operational
[ ] Policy Guard operational (all rules enforced)
[ ] Static Dunning implemented
[ ] Smart Retry implemented
[ ] KhaataPulse implemented
[ ] Same-cohort evaluation implemented
[ ] Incremental recovery calculated dynamically
[ ] Multi-seed evaluation implemented (seeds 42, 123, 456)
[ ] Audit trail implemented (immutable, structured)
[ ] Idempotency implemented (action service rejects duplicates)
[ ] Kill switch implemented (blocks all automated actions when active)
[ ] Blocked case implemented
[ ] Escalated case implemented
[ ] Hero case implemented
[ ] Dashboard implemented (no hardcoded metrics)
[ ] Revenue Time Machine implemented
[ ] Audit drawer implemented
[ ] Live webhook simulation implemented
[ ] Demo mode implemented (works without LLM / network)
[ ] Docker deployment works (docker compose up)
```

---

## 36. Phase Execution Rules

The project is implemented through controlled Claude Code phases. Do not prematurely implement later phases.

```
Phase 0  — Engineering Contract + Repository Foundation       ← CURRENT
Phase 1  — Simulator + Database Foundation
Phase 2  — Risk Sieve + LangGraph + LLM
Phase 3  — Economic Optimizer + Policy Guard + Actions + Audit
Phase 4  — Evaluation Engine + Multi-Seed Validation
Phase 5  — Frontend Command Center
Phase 6  — Integration + Demo Mode + Final Polish
```

Each phase has intentional boundaries. When starting a phase, read this contract first, inspect existing code second, then implement the phase scope only.

---

## Implementation Status

```
Current Phase:  3
Status:         Complete
Completed:
  - Phase 0: CLAUDE.md engineering contract established
  - Phase 1: Simulator + Database Foundation
      backend/app/core/config.py          Settings with all env vars
      backend/app/core/logging.py         Structured JSON logging
      backend/app/db/base.py              SQLAlchemy Base
      backend/app/db/session.py           Engine + get_db dependency
      backend/app/db/models/             ORM models (customers, subscriptions,
                                          payments, events, sim_runs, sim_outcomes,
                                          recovery_cases, actions, audit_events)
      backend/app/simulator/latent_state.py  CustomerLatentState (HIDDEN)
      backend/app/simulator/outcomes.py      PotentialOutcomes (HIDDEN)
      backend/app/simulator/events.py        Observable event generator
      backend/app/simulator/generator.py     Deterministic world generator
      backend/app/simulator/world.py         WorldInternal / ObservableWorld boundary
      backend/app/simulator/persistence.py   DB persistence with isolation guarantees
      backend/app/schemas/simulator.py        API schemas (no hidden data)
      backend/app/api/routes/simulator.py    POST /simulation/generate, GET /simulation/runs
      backend/app/main.py                    FastAPI app
      backend/alembic/                       Alembic migrations (001_initial_schema,
                                             002_phase3_recovery_audit)
      backend/tests/                         63 tests — 63 passed (0 failures)
        tests/simulator/test_simulator.py    Determinism, cohort size, isolation, events
        tests/db/test_models.py              ORM, referential integrity, constraints
      backend/pytest.ini                     Test configuration
      docker-compose.yml                     postgres:16 + backend services
      .env.example                           All required env vars documented
  - Phase 2: Risk Sieve + LangGraph Agent
      backend/app/risk/features.py        RiskFeatures (frozen dataclass), FeatureBuilder
                                          12 observable features, FEATURE_NAMES list
      backend/app/risk/model.py           RiskPredictor (LogisticRegression + StandardScaler)
                                          Observable-only training labels, top-3 explainability
                                          RiskSignal, RiskPrediction, get_risk_predictor()
      backend/app/risk/service.py         RiskService, RoutingDecision, config-driven threshold
      backend/app/agent/schemas.py        RecoveryProposal Pydantic model (CLAUDE.md §11)
      backend/app/agent/reasoning.py      BaseReasoningModel, StubReasoningModel,
                                          AnthropicReasoningModel, ReasoningContext
      backend/app/agent/fallback.py       smart_retry_proposal (deterministic LLM fallback)
      backend/app/api/routes/risk.py      POST /risk/predict, POST /risk/reason
      backend/tests/                      155 tests — 155 passed (0 failures)
        tests/risk/test_features.py       Feature engineering, isolation, array contract
        tests/risk/test_model.py          Model training, reproducibility, routing, explainability
        tests/agent/test_graph.py         Node ordering, structured output, validation,
                                          LLM failure/fallback, agent isolation
  - Phase 3: Economic Optimizer + Policy Guard + Action Execution + Audit
      backend/app/optimizer/eligibility.py  cause → eligible action types mapping
      backend/app/optimizer/enr.py          ENR formula, estimated probability tables,
                                            ActionRanking frozen dataclass
      backend/app/optimizer/ranker.py       rank_eligible_actions() — deterministic by ENR
      backend/app/policy/guard.py           PolicyGuard — pure deterministic, all rules:
                                            kill_switch, dispute_hold, legal_hold, opt_out,
                                            idempotency, contact_limit (3/7d), cooldown (24h),
                                            amount_threshold (≥₹10k → ESCALATED)
                                            PolicyDecision(APPROVED|BLOCKED|ESCALATED, checks)
      backend/app/actions/service.py        ActionService — typed, idempotent simulated gateway
                                            ActionRequest, ActionResult, duplicate rejection
      backend/app/audit/service.py          AuditService — append-only log_audit_event()
                                            All 8 required event types supported
      backend/app/agent/state.py            RecoveryReasoningState — added Phase 3 fields:
                                            ltv, dispute_hold, legal_hold, opt_out,
                                            eligible_actions, action_rankings, selected_action,
                                            policy_decision, execution_result, recorded_outcome,
                                            case_id
      backend/app/agent/nodes.py            All 9 nodes fully implemented:
                                            make_rank_actions() — economic optimizer
                                            make_policy_check(db) — policy guard
                                            make_execute_action(db) — action service
                                            make_record_outcome(db) — audit + case closure
      backend/app/agent/graph.py            build_recovery_graph(reasoning_model, db)
                                            make_initial_state() — includes Phase 3 fields
      backend/app/core/config.py            Added action costs (config-driven):
                                            action_cost_silent_retry/smart_link/grace_period/
                                            human_escalation
      backend/alembic/versions/002_...      Migration: recovery_cases, actions, audit_events,
                                            + customer hold flags (dispute_hold, legal_hold, opt_out)
      backend/tests/                        212 tests — 212 passed (0 failures)
        tests/optimizer/test_enr.py         ENR formula, probability estimation, eligibility,
                                            ranking determinism, action cost effects
        tests/policy/test_guard.py          All Policy Guard rules independently tested:
                                            APPROVED, BLOCKED (kill_switch, dispute_hold,
                                            legal_hold, opt_out, idempotency, contact_limit,
                                            cooldown), ESCALATED (amount_threshold)
        tests/agent/test_graph.py           Updated: Phase 3 nodes produce real outputs
        tests/db/test_models.py             Updated: Phase 3 tables verified present
  - Phase 4: Evaluation Engine + Multi-Seed Validation
      backend/app/db/models/evaluation.py   EvaluationRun + EvaluationResult ORM models
      backend/app/evaluation/__init__.py    Package init
      backend/app/evaluation/metrics.py     PolicyEvaluationResult, EvaluationRunResult
                                            dataclasses — all fields dynamic (no hardcoded values)
      backend/app/evaluation/policies.py    RecoveryPolicy ABC + three implementations:
                                            StaticDunningPolicy — failure count → action
                                            SmartRetryPolicy   — failure code → action
                                            KhaataPulsePolicy  — Risk Sieve → Stub LLM →
                                              Optimizer → Policy Guard (no-db mode)
      backend/app/evaluation/evaluator.py   EvaluationWorld (isolates PotentialOutcomes),
                                            evaluate_policy_on_world(),
                                            run_same_cohort_evaluation() — world generated
                                            ONCE, all three policies see same world, same
                                            potential outcomes (CLAUDE.md §17 invariant)
      backend/app/evaluation/runner.py      run_evaluation(), run_multi_seed_evaluation(),
                                            get_multi_seed_summary(), get_run_from_db()
                                            Persistence: EvaluationRun + EvaluationResult
      backend/app/api/routes/evaluation.py  POST /evaluation/run
                                            POST /evaluation/run/multi-seed
                                            GET  /evaluation/run/{run_id}
                                            GET  /evaluation/runs
      backend/app/main.py                   Evaluation router registered
      backend/app/db/models/__init__.py     EvaluationRun, EvaluationResult exported
      backend/alembic/versions/003_...      Migration: evaluation_runs, evaluation_results
      backend/tests/                        267 tests — 267 passed, 6 skipped (0 failures)
        tests/evaluation/test_evaluator.py  Same-cohort invariant, EvaluationWorld isolation,
                                            false positives, incremental recovery, reproducibility,
                                            recovery rate bounds
        tests/evaluation/test_runner.py     Multi-seed (42, 123, 456), no-db mode, DB persistence
                                            (skipped without Docker), re-run overwrite
        tests/evaluation/test_api.py        POST /evaluation/run, GET /evaluation/run/{id},
                                            multi-seed endpoint, error handling, field contracts
        tests/db/test_models.py             Updated: Phase 4 tables verified present

Current Phase:  4
Status:         Complete

Next Phase:     Phase 5 — Frontend Command Center
```
