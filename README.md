<div align="center">

<img src="media/01_khaatapulse_brand_identity_mark.png" alt="KhaataPulse" width="700" />

### **Revenue recovery, under control.**

---

<table align="center">
  <tr>
    <td align="center">
      <strong>⚡ BUILT FOR RAZORPAY AI BUILDTHON 2026</strong><br>
      <sub>TRACK: AI REVENUE RECOVERY</sub>
    </td>
  </tr>
</table>

---

</div>

<div align="center">
  <img src="media/02_khaatapulse_flagship_hero_revenue_recovery.png" alt="KhaataPulse - Revenue Recovery Command Center" width="100%" />
</div>

---

Payment failures are not all the same.

A card expiry, a billing migration, temporary cash flow pressure, price friction, and genuine churn intent each demand a different response - a different intervention, at a different cost, with a different expected return. A static retry schedule treats them identically.

**KhaataPulse does not.**

It diagnoses the failure context, ranks recovery interventions by expected net revenue, enforces deterministic policy constraints, and measures outcomes - all in a fully observable, auditable pipeline.

> **AI proposes. Economics ranks. Policy authorizes. Actions execute. Outcomes are measured.**

---

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2-6366F1?style=flat-square)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Logistic%20Regression-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-260%20passing-10B981?style=flat-square)

---

## See KhaataPulse in Action

<div align="center">
  <img src="media/command_center.gif" alt="KhaataPulse Command Center - Revenue Recovery in Action" width="100%" />
</div>

> The Command Center turns revenue recovery into an observable decision system - from risk detection and AI diagnosis to action ranking, policy enforcement, and outcome measurement. Every number originates from a live evaluation run. Nothing is authored.

<br/>

<div align="center">
  <img src="media/dashboard.png" alt="KhaataPulse Dashboard" width="100%" />
</div>

**What you're looking at:**
- Live incremental recovery - KhaataPulse vs. Smart Retry, computed dynamically
- Three-policy comparison: Static Dunning / Smart Retry / KhaataPulse against the same cohort
- Hero case: full pipeline trace from risk signal to executed action
- Policy Guard visualization - sequential checkpoint with per-rule pass/fail
- Immutable audit trail - every decision recorded and expandable

---

## Run It Yourself

```bash
git clone <repository-url>
cd khaata-pulse

cp .env.example .env        # add LLM_API_KEY if available (optional - demo works without it)

docker compose up --build   # starts postgres + backend (migrations run automatically)
```

Then start the frontend:

```bash
cd frontend
npm install
npm run dev
```

| Surface | URL |
|---|---|
| Command Center | `http://localhost:3000/dashboard` |
| Risk Queue | `http://localhost:3000/cases` |
| Revenue Time Machine | `http://localhost:3000/dashboard/time-machine` |
| Policy Stress Test | `http://localhost:3000/evaluation` |
| API Docs | `http://localhost:8000/docs` |

> Demo mode works without an LLM API key. The system uses a deterministic fallback that produces a valid, structured diagnosis from observable signals alone.

---

## Watch a Recovery Decision Happen

<div align="center">
  <img src="media/command_center_Live_Webhook_Simulation.gif" alt="Live Webhook Simulation - Full Pipeline in Real Time" width="100%" />
</div>

> One webhook. One decision. A fully traceable recovery path.

A simulated payment failure enters the system. In real time, you watch:

```
Payment Signal
    → Risk Detection       - Logistic Regression scores the account
    → Diagnosis            - LLM classifies cause and proposes action
    → Economic Ranking     - ENR selects the highest-value eligible action
    → Policy Guard         - deterministic authorization check
    → Action               - executed or blocked, with reason
    → Audit                - every step recorded, immutable
```

Every stage is visible. Every decision is explained. Nothing is a black box.

---

## Why This Is Different

### 01 - Reasoning, Not Rules

The system does not route every failed payment through the same retry schedule. It first classifies the failure cause - card expiry, billing migration, temporary cash flow, price friction, or churn intent - then selects a recovery strategy appropriate to that context.

### 02 - Economics, Not Confidence

Recovery actions are ranked by **Expected Net Revenue** rather than model confidence alone. The optimizer considers the probability of payment, the risk of churn, and the cost of contact. A high-confidence recommendation with poor economics does not get selected.

### 03 - Policy, Not Probability

AI does not authorize execution. A deterministic Policy Guard - not a model, not a threshold, not a heuristic - is the only component with execution authority. A valid, high-confidence AI proposal can still be blocked.

---

## Intelligence Without Autonomy

<div align="center">
  <img src="media/10_khaatapulse_intelligence_without_autonomy.png" alt="Intelligence Without Autonomy" width="100%" />
</div>

> Most AI systems either guess or take control.
>
> KhaataPulse does neither.

The LLM diagnoses and proposes. The optimizer ranks. The Policy Guard decides. The Action Service executes only what was authorized. The Audit Service records everything.

```
AI REASONING
     ↓
  PROPOSAL
     ↓
 ECONOMIC RANKING
     ↓
 POLICY GUARD          ← the only execution authority
     ↓
APPROVED / BLOCKED / ESCALATED
     ↓
 ACTION SERVICE
     ↓
 AUDIT LOG
```

This is intentional architecture. An LLM with a hallucinated confidence score, a poorly calibrated output, or a malformed response cannot reach the execution layer. The guard is pure deterministic code - independently unit-tested, configuration-driven, with no side effects.

---

## From AI Reasoning to Revenue Economics

<div align="center">
  <img src="media/06_khaatapulse_expected_net_revenue.png" alt="Expected Net Revenue Optimizer" width="100%" />
</div>

The optimizer does not ask: *"Which action sounds best?"*

It asks: **"Which eligible action produces the highest expected net return?"**

```
ENR(action) = P(payment | action) × Amount
            − P(churn   | action) × LTV
            − Action Cost
```

The AI diagnosis determines which actions are **eligible**. The optimizer ranks only the eligible set. Action costs are configuration-driven - never scattered as constants in code.

The optimizer uses **estimated** probabilities derived from observable features (cause + action type). It does not receive the simulator's ground-truth potential outcomes - that architectural boundary is maintained by type isolation in the codebase.

---

## The Model Proposes. Policy Decides.

<div align="center">
  <img src="media/04_khaatapulse_policy_guard.png" alt="Policy Guard - Deterministic Authorization" width="100%" />
</div>

A high-confidence AI recommendation is still only a proposal.

The deterministic Policy Guard evaluates eight authorization rules - in strict order, all thresholds from environment configuration - before any action proceeds:

**kill switch · dispute hold · legal hold · opt-out · idempotency · contact frequency · cooldown · amount threshold**

> **No AI output can bypass the authorization boundary.**

Every outcome produces a `PolicyDecision` containing a per-rule pass/fail record that becomes part of the immutable audit trail. The guard is pure code: same inputs, same output, every time.

---

## Same World. Different Policies.

<div align="center">
  <img src="media/07_khaatapulse_same_world_different_policies.png" alt="Same World. Different Policies." width="100%" />
</div>

Comparing recovery policies on different customer populations is not a fair test. KhaataPulse enforces a stricter evaluation methodology:

```python
world = generate_world(seed=42)          # generated ONCE

static_result = evaluate(world, StaticDunningPolicy())
smart_result  = evaluate(world, SmartRetryPolicy())
kp_result     = evaluate(world, KhaataPulsePolicy())
```

**One cohort. One event history. One set of potential outcomes.**

Three policies evaluated against the same world. Only the recovery logic changes. This is the only valid basis for measuring policy lift - and it is enforced by the evaluation engine, not by convention.

---

## Prove It Across Seeds

<div align="center">
  <img src="media/policy_test_seed_and_multi-seed_validation.gif" alt="Policy Evaluation - Seed Selection and Multi-Seed Validation" width="100%" />
</div>

A single-seed result could be peculiar to one random world. KhaataPulse validates policy performance across three independent seeds:

| Seed | Purpose |
|---|---|
| `42` | Default dashboard seed |
| `123` | Independent world validation |
| `456` | Third independent world validation |

`POST /evaluation/run/multi-seed` runs all three in a single request and returns per-seed metrics alongside cross-seed consistency analysis. The evaluation page lets you run any seed or cohort size - and watch the results compute in real time.

### Policy Comparison

| Metric | Static Dunning | Smart Retry | KhaataPulse |
|---|---|---|---|
| Recovered (₹) | - | - | - |
| Recovery Rate | - | - | - |
| Contacts Sent | - | - | - |
| Contacts Avoided | - | - | - |
| Human Escalations | - | - | - |
| Policy Blocks | - | - | - |
| **Incremental Recovery** | **baseline** | **baseline** | **+₹ vs Smart Retry** |

> Results are generated dynamically by the evaluation engine. Run the Seed 42 evaluation to reproduce the comparison - no values are authored in the codebase.

### The KPI That Matters

```
Incremental Recovery = KhaataPulse Recovered − Smart Retry Recovered
```

Smart Retry is the primary comparison baseline - not Static Dunning - because it already applies failure-code logic and deterministic retry timing. KhaataPulse must demonstrate lift above an intelligent baseline, not a naive one.

---

## Every Decision Leaves Evidence

<div align="center">
  <img src="media/08_khaatapulse_immutable_audit_trail.png" alt="Immutable Audit Trail" width="100%" />
</div>

Every stage of the pipeline produces an immutable audit event:

```
risk_detected → diagnosis_generated → action_proposed →
policy_check → action_executed / blocked / escalated →
case_closed
```

LLM fallback events are also recorded - with reason and fallback policy - so no failure is invisible.

The audit drawer in the frontend renders the full decision lifecycle in chronological order, with expandable raw JSON payloads in monospace. The service is append-only: no update or delete paths exist.

---

## Under the Hood

<div align="center">
  <img src="media/03_khaatapulse_intelligence_pipeline.png" alt="KhaataPulse Intelligence Pipeline" width="100%" />
</div>

Seven deterministic layers. Each with a defined role. None exceeding its authority.

```
Simulator (3,000-customer synthetic world)
    ↓  observable events only
Risk Sieve (Logistic Regression · 12 features · P(failure) threshold: 0.30)
    ↓  ~350 high-risk accounts
LangGraph Agent (9-node single-stage graph)
    ↓  RecoveryProposal (Pydantic-validated)
Economic Optimizer (ENR ranking · Decimal precision)
    ↓  top-ranked eligible action
Policy Guard (deterministic · 8 rules · configuration-driven)
    ↓  APPROVED / BLOCKED / ESCALATED
Action Service (typed · idempotent · duplicate-key rejection)
    ↓
Audit Service (append-only · 8 event types)
    ↓
Evaluation Engine (same-cohort · 3 policies · multi-seed)
```

### Safety and Control Model

| Component | Authority |
|---|---|
| Risk Sieve | Identifies who needs attention. Cannot execute actions. |
| AI (LLM) | Diagnoses context. Proposes actions. Cannot authorize or execute. |
| Optimizer | Ranks proposals by ENR. Cannot override Policy Guard. |
| Policy Guard | The only authority to authorize, block, or escalate. Deterministic. |
| Action Service | Executes only what Policy Guard approved. Enforces idempotency. |
| Audit Service | Records every decision. Append-only. |
| Evaluator | Measures outcomes. Only layer with ground-truth access. |
| Kill Switch | Global STOP - checked first in Policy Guard, before all other rules. |

<details>
<summary><strong>Simulator Isolation & Evaluation Integrity</strong></summary>

The simulator is the only component with access to hidden state and potential outcomes.

**Hidden state** (`CustomerLatentState`) - the actual ground truth:
`payment_intent`, `cash_flow_health`, `payment_rail_health`, `churn_sensitivity`, `customer_ltv`.

**The agent never receives this.** It is enforced by type isolation - `CustomerLatentState` and `PotentialOutcomes` are Python types that exist exclusively inside the simulator package. No API route, no agent node, and no frontend component ever touches them. A dedicated test in the integration suite verifies this.

The agent only receives observable events: `payment_failed`, `invoice_viewed`, `checkout_reopened`, `payment_method_changed`, `support_message`, `payment_delayed`, `renewal_approaching`, `subscription_changed`.

The optimizer uses **estimated** probabilities derived from observable features - not the simulator's ground-truth `PotentialOutcomes`. Only the evaluation harness accesses those, to compute expected recovered amounts per policy.

</details>

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 · TypeScript · Tailwind CSS |
| Backend | FastAPI · Python 3.11 · SQLAlchemy · Alembic |
| Database | PostgreSQL 16 |
| Agent | LangGraph · Anthropic Claude (structured output) |
| Risk Model | Scikit-learn · Logistic Regression · StandardScaler |
| Containers | Docker · Docker Compose |

---

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
```

```
260 passed · 6 skipped (require live PostgreSQL)
18 end-to-end integration tests
```

Critical invariants tested:

- Simulator isolation - hidden state never enters agent context
- LLM schema validation - `RecoveryProposal` Pydantic enforcement
- LLM fallback - all failure types: timeout, malformed JSON, invalid enum, missing field, provider error, schema failure
- Policy Guard - each of the 8 rules independently (APPROVED, BLOCKED ×5, ESCALATED)
- Action idempotency - duplicate key rejection
- Same-cohort evaluation invariant - all three policies against one world
- Multi-seed stability - seeds 42, 123, 456
- Incremental recovery - dynamically computed, never authored

---

## Project Structure

```
khaata-pulse/
├── backend/
│   ├── app/
│   │   ├── simulator/          # World generation · isolation boundary
│   │   ├── risk/               # Logistic Regression · 12 observable features
│   │   ├── agent/              # LangGraph 9-node graph · LLM · fallback
│   │   ├── optimizer/          # ENR formula · eligibility · ranking
│   │   ├── policy/             # Policy Guard · 8 deterministic rules
│   │   ├── actions/            # Typed · idempotent gateway
│   │   ├── audit/              # Append-only event log
│   │   ├── evaluation/         # Same-cohort engine · 3 policies · multi-seed
│   │   ├── api/routes/         # FastAPI routers
│   │   └── core/               # Config (env-driven) · structured logging
│   ├── alembic/versions/       # 3 migrations · 10 tables
│   └── tests/                  # 260 tests across 9 suites + integration
├── frontend/
│   ├── app/                    # Next.js App Router (5 routes)
│   ├── components/             # 42 components across 9 folders
│   └── lib/                    # Types · API clients · formatters
├── media/                      # Visual assets · GIFs
├── docker-compose.yml
└── CLAUDE.md                   # Engineering contract
```

Full file-by-file reference: [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)

---

## Environment Configuration

```env
DATABASE_URL=postgresql://khaatapulse:khaatapulse@localhost:5432/khaatapulse
LLM_API_KEY=                    # Optional - demo works without it
LLM_MODEL=claude-sonnet-5

APP_ENV=development

# Policy thresholds - all configuration-driven
AUTO_ACTION_LIMIT=10000         # ₹ below which actions auto-execute
MAX_CONTACTS_7D=3               # Contact frequency cap per 7 days
CONTACT_COOLDOWN_HOURS=24       # Minimum hours between contacts
KILL_SWITCH=false               # Set true to pause all automation globally
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health |
| `POST` | `/simulation/generate` | Generate a 3,000-customer synthetic world |
| `POST` | `/risk/predict` | Score accounts with the risk model |
| `POST` | `/risk/reason` | Run the full 9-node LangGraph pipeline |
| `POST` | `/evaluation/run` | Start same-cohort evaluation (async) |
| `GET` | `/evaluation/run/{id}` | Poll evaluation results |
| `POST` | `/evaluation/run/multi-seed` | Validate across seeds 42 · 123 · 456 |
| `GET` | `/demo/hero` | Deterministic hero case (no DB required) |
| `POST` | `/demo/simulate` | Full pipeline in demo mode (~100ms) |
| `GET` | `/cases/` | List recovery cases |
| `GET` | `/cases/{case_id}` | Full case detail with audit events |

Interactive docs: `http://localhost:8000/docs`

---

<div align="center">

**KhaataPulse · Revenue Intelligence Engine**

*Built for Razorpay AI Buildthon 2026 · Track: AI Revenue Recovery*

*Detect · Diagnose · Optimize · Guard · Act · Measure · Audit*

</div>
