# KhaataPulse — Application Walkthrough & Functionality Reference

> **KhaataPulse** is an AI-powered revenue recovery policy engine designed for subscription businesses. It detects payment friction before failure, diagnoses the underlying cause, proposes the financially optimal recovery intervention, enforces deterministic policy constraints, and measures outcomes — all in a controlled, fully auditable environment.

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Core Claim](#2-core-claim)
3. [The Intelligence Pipeline](#3-the-intelligence-pipeline)
4. [Technology Stack](#4-technology-stack)
5. [Application Surfaces](#5-application-surfaces)
   - 5.1 [Landing Page — Overview (`/`)](#51-landing-page--overview)
   - 5.2 [Command Center — Dashboard (`/dashboard`)](#52-command-center--dashboard)
   - 5.3 [Revenue Time Machine (`/dashboard/time-machine`)](#53-revenue-time-machine)
   - 5.4 [Risk Queue — Cases (`/cases`)](#54-risk-queue--cases)
   - 5.5 [Policy Stress Test — Evaluation (`/evaluation`)](#55-policy-stress-test--evaluation)
6. [Backend Architecture](#6-backend-architecture)
   - 6.1 [Simulator](#61-simulator)
   - 6.2 [Risk Sieve](#62-risk-sieve)
   - 6.3 [LangGraph Agent](#63-langgraph-agent)
   - 6.4 [Economic Optimizer](#64-economic-optimizer)
   - 6.5 [Policy Guard](#65-policy-guard)
   - 6.6 [Action Service](#66-action-service)
   - 6.7 [Audit Service](#67-audit-service)
   - 6.8 [Evaluation Engine](#68-evaluation-engine)
7. [Key Architectural Boundaries](#7-key-architectural-boundaries)
8. [Design System](#8-design-system)
9. [Running the Application](#9-running-the-application)
10. [API Reference (Summary)](#10-api-reference-summary)
11. [Demo Mode](#11-demo-mode)

---

## 1. Product Overview

KhaataPulse solves a specific, high-value problem: **subscription businesses lose revenue not because customers intend to churn, but because payment friction — expired cards, temporary cash flow issues, failed retries — goes undiagnosed and unresolved at the right moment.**

Traditional dunning strategies (retry after N hours, send a reminder, escalate) treat all payment failures identically. KhaataPulse treats them as a reasoning problem: _why_ did this payment fail, _what_ is the best recovery action for this specific customer's situation, and _is the expected financial return_ worth the cost of contact?

The system operates on three levels simultaneously:

| Level | Mechanism | Output |
|---|---|---|
| Detection | Logistic Regression risk model | `P(failure)` — which accounts need attention |
| Diagnosis | LangGraph + LLM reasoning | Cause, confidence, proposed action |
| Evaluation | Same-cohort policy comparison | Incremental recovery vs. baseline policies |

KhaataPulse is **not** a payment processor, collections platform, or autonomous financial system. It is a **controlled revenue-recovery policy evaluation environment** — every action is proposed, guard-checked, and audited before execution.

---

## 2. Core Claim

> KhaataPulse can identify payment friction before failure and evaluate whether its recovery policy produces better expected revenue outcomes than existing dunning policies, without exceeding predefined customer-contact and escalation boundaries.

This claim is verified end-to-end within the application: the same 3,000-customer cohort is evaluated against three policies simultaneously, and the incremental recovery delta is computed dynamically — never hardcoded.

---

## 3. The Intelligence Pipeline

Every account processed by KhaataPulse travels through seven deterministic stages:

```
DETECT → DIAGNOSE → OPTIMIZE → GUARD → ACT → MEASURE → AUDIT
```

### Stage 1 — Detect
The **Risk Sieve** (Logistic Regression) scores every account against 12 observable features derived from payment history and behavioural signals. Accounts with `P(failure) ≥ 0.30` are routed into the full KhaataPulse pipeline (~350 of 3,000 accounts). The rest follow the standard flow.

### Stage 2 — Diagnose
The **LangGraph Agent** receives only observable data (event history, payment context, support messages, subscription info). It calls an LLM with a structured-output contract to produce a `RecoveryProposal`:
- **Cause**: `billing_migration | temporary_cash_flow | card_expired | price_friction | churn_intent`
- **Confidence**: 0.0 – 1.0
- **Proposed action**: `silent_retry | smart_link | grace_period | human_escalation | suppress`
- **Risk level**: `LOW | MEDIUM | HIGH`
- **Rationale**: natural-language explanation

If the LLM fails (timeout, invalid schema, provider error), a deterministic Smart Retry fallback activates automatically.

### Stage 3 — Optimize
The **Economic Optimizer** computes Expected Net Revenue (ENR) for every eligible action:

```
ENR = P(payment | action) × Amount
    − P(churn | action) × LTV
    − ActionCost
```

The cause diagnosis narrows the eligible action set. The optimizer ranks survivors by ENR and selects the highest-value option.

### Stage 4 — Guard
The **Policy Guard** — pure deterministic code, no ML, no LLM — applies all authorization rules before any action proceeds:

| Rule | Threshold |
|---|---|
| Contact limit | 3 contacts per 7 days |
| Cooldown | 24 hours between contacts |
| Auto-action limit | Amount < ₹10,000 |
| Human approval | Amount ≥ ₹10,000 → ESCALATED |
| Dispute hold | STOP |
| Legal hold | STOP |
| Customer opt-out | STOP |
| Kill switch (global) | STOP |
| Idempotency | Duplicate key rejected |

Every action produces a `PolicyDecision` with status `APPROVED`, `BLOCKED`, or `ESCALATED`, and a `checks` object showing exactly which rules passed or failed.

### Stage 5 — Act
The **Action Service** executes the approved action through a simulated (but structurally real) gateway. Every action carries an idempotency key (`rec_CASE_{id}`). Duplicate execution of the same key is rejected. Valid action types: `silent_retry`, `smart_link`, `grace_period`, `human_escalation`, `suppress`.

### Stage 6 — Measure
The **Evaluation Engine** computes policy performance across the full cohort. Three policies operate against the **same world** (same customers, same events, same potential outcomes — only the recovery logic changes):
- **Static Dunning**: failure → 24h retry → reminder → escalation
- **Smart Retry**: failure code → deterministic timing → payment link → escalation
- **KhaataPulse**: risk detection → AI diagnosis → ENR optimization → policy guard → action

The primary KPI is **Incremental Recovery** = KhaataPulse recovery − Smart Retry recovery.

### Stage 7 — Audit
Every meaningful decision at every stage produces an immutable `AuditEvent`:
- `risk_detected`, `diagnosis_generated`, `action_proposed`, `policy_check`
- `action_executed`, `payment_received`, `case_closed`, `llm_fallback`

The audit trail is append-only, chronologically ordered, and fully queryable through the frontend audit drawer.

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS |
| Backend | FastAPI + Python |
| Database | PostgreSQL 16 |
| Agent Orchestration | LangGraph |
| Risk Model | Scikit-learn Logistic Regression |
| LLM | Anthropic Claude (structured output) |
| Containerisation | Docker Compose |

All services start with:
```bash
docker compose up
```

Frontend: `http://localhost:3000`  
Backend: `http://localhost:8000`  
PostgreSQL: `localhost:5432` (Docker internal) / `5435` (host, configurable)

---

## 5. Application Surfaces

### 5.1 Landing Page — Overview (`/`)

The entry point for first-time visitors. Seven sections communicate the product's purpose and architecture:

**Hero Section**
- Tagline: "Recover revenue before it becomes lost."
- Two primary CTAs: Enter Command Center → / Explore Evaluation
- Animated pipeline badge: `Detect · Diagnose · Optimize · Guard · Act · Measure · Audit`

**Hero Visualization**
- Interactive SVG showing the full 9-node LangGraph pipeline
- Signal dots travel between nodes; connections energise as signals pass through
- Nodes: classify_context → generate_diagnosis → generate_action_proposal → validate_proposal → rank_actions → policy_check → execute_action → record_outcome

**Pipeline Section — "The Intelligence Pipeline"**
Seven numbered pipeline stages, each with a title, description, and the specific technology responsible. Communicates that every stage has a defined role and none exceeds its authority.

**Architecture Story — "Intelligence without autonomy"**
Five architectural boundaries explained:
1. Simulation World (hidden states + potential outcomes)
2. Core Agent (risk → diagnosis → proposal → optimization)
3. Policy Layer (deterministic authorization)
4. Action Layer (typed, idempotent gateway operations)
5. Evaluation (baselines → outcomes → incremental recovery)

**Product Preview — "Every layer, visible"**
Four illustrative panels previewing key UI surfaces:
- Risk Intelligence (logistic regression score + signals)
- AI Diagnosis (cause classification + confidence)
- Economic Optimizer (ENR-ranked action table)
- Policy Guard (sequential checkpoint visualization)

**Time Machine Preview**
An illustrative customer journey timeline showing the observable event stream KhaataPulse works from — payment failures, invoice views, support messages, renewal signals.

**Final CTA — "Revenue recovery, under control"**
Closing statement with direct links to the Command Center and Evaluation surface.

---

### 5.2 Command Center — Dashboard (`/dashboard`)

The primary operational surface for a merchant. All metrics originate from a live evaluation run against the backend — nothing is authored or hardcoded.

**On load:** The dashboard immediately fires `POST /evaluation/run` (seed=42, cohort=3,000) and `GET /demo/hero` in parallel. The evaluation may take 5–30 seconds; a loading panel describes what is happening ("Evaluating 3,000 accounts across 3 recovery policies…"). The hero case resolves quickly from the demo endpoint.

#### Dashboard Header
Shows the current run context: seed, cohort size, run status (loading / completed / error), and the evaluation run ID in monospace. A Retry button appears on failure.

#### Hero KPI Grid
Six metric cards derived from the KhaataPulse policy results:

| Card | Content |
|---|---|
| Recovered · KhaataPulse | Total ₹ recovered, out of ₹ at risk |
| KP Recovery Rate | Recovery %, and the pp lift vs Smart Retry |
| Revenue Exposure | Total ₹ at risk, and number of cases |
| Contacts Avoided | Accounts not contacted, vs Smart Retry |
| Human Escalations | Cases routed above the auto-action limit |
| Policy Blocks | Cases stopped by Policy Guard |

All values in Indian Rupee format (L/Cr for large numbers, tabular numerals).

#### Revenue Exposure Bar
A proportional horizontal bar chart comparing the at-risk revenue across the three policies. Bar widths are computed from the actual evaluation data, not authored.

#### Incremental Hero Panel
The **dominant KPI panel** — visually larger than the rest. Shows:
- `+₹X` Incremental Recovery (KhaataPulse − Smart Retry)
- Recovery rate lift in percentage points (pp)
- Contacts saved count
- Directional wash (green radial gradient for positive, red for negative)
- A glow that responds to the sign of incremental recovery

#### Policy Comparison Matrix
Three-column table comparing Static Dunning / Smart Retry / KhaataPulse across all evaluation metrics:
- Recovered amount, recovery rate, contacts sent, contacts avoided, human escalations, policy blocks, false positives
- Each KhaataPulse column cell shows the delta vs Smart Retry
- Delta cells are coloured semantically (recovery-green for improvements, warning-amber for regressions)

#### Hero Case Panel
A full pipeline narrative for the demo customer (deterministic, always the same account):

1. **Customer header** — name, segment, LTV, subscription ID, renewal amount
2. **Subscription fields** — plan, renewal date, last payment status and failure code
3. **Risk Assessment** — risk score (colour-coded by threshold), risk level badge, model version, top 3 feature signals with impact bars
4. **AI Diagnosis** — cause label, confidence bar (fills via CSS transition; ai-violet above 50%, warning-amber below), rationale text
5. **Intervention Optimizer** — ranked action table showing ENR for each eligible action; selected action highlighted
6. **Policy Guard** — sequential checkpoint visualization: each rule animates in with a 60ms stagger; APPROVED rules show a brief green pulse then settle; BLOCKED rules trigger a sharp red interruption
7. **Outcome** — action type, execution status (executed/escalated/blocked) with colour, idempotency key in monospace
8. Link: "Replay in Time Machine →"

#### Live Activity Feed
Chronological list of the hero customer's audit events pulled from `GET /demo/hero`. Each event shows: event type (monospace), timestamp, actor. Idle state: "Pipeline awaiting activity."

#### Live Webhook Simulation
A `SIMULATE PAYMENT WEBHOOK` button triggers a visual walk-through of the full pipeline:
1. Webhook Received
2. Risk Sieve — score computed
3. AI Reasoning — LLM diagnosis
4. Policy Guard — authorization
5. Action Executed — gateway call
6. Outcome Recorded — audit sealed

Each stage activates sequentially with a 400ms CSS-staggered delay. Completion triggers a summary of the simulated result. The animation uses CSS `animation-delay` (not JS timers), so it fully respects `prefers-reduced-motion`.

#### Audit Trail
The full audit event stream for the hero case, rendered below the webhook simulator. Each event is expandable to reveal the raw JSON payload (syntax-highlighted, JetBrains Mono, copy button).

---

### 5.3 Revenue Time Machine (`/dashboard/time-machine`)

A cinematic account-level reconstruction showing the exact observable signals the agent worked from — and the pipeline decisions derived from them.

**Subject panel:**
- Customer name, ID, segment, plan
- Renewal amount and date
- Risk score (colour-coded) and level
- Lifetime value

**Reconstruction timeline — 11 entries:**
Two groups render side-by-side:

| Observable Event Stream | Pipeline Decision Log |
|---|---|
| PAYMENT_FAILED (10 Aug) | risk_detected |
| PAYMENT_FAILED (9 Sept) | diagnosis_generated |
| INVOICE_VIEWED (15 Dec) | action_proposed |
| PAYMENT_DELAYED (19 Dec) | policy_check |
| SUPPORT_MESSAGE (26 Dec) | action_executed |
| RENEWAL_APPROACHING (2 Jan) | case_closed |

Each event card is expandable. Observable events show the raw event payload (what the agent saw). Pipeline events show the decision payload (what the agent produced).

The design communicates a critical architectural invariant: **the agent sees only the left column**. Hidden simulator state (payment intent, cash flow health, churn sensitivity) never appears anywhere in the timeline.

---

### 5.4 Risk Queue — Cases (`/cases`)

The operational queue of accounts that the risk sieve routed into the KhaataPulse pipeline.

**Header:** Case count badge, RECOVERY QUEUE label, Refresh button.

**Case list:** Each row/card shows:
- Customer name
- Risk score with colour-coded indicator bar (green < 0.30, amber 0.30–0.70, red ≥ 0.70)
- Risk level text label (LOW / MEDIUM / HIGH — colour never the only indicator)
- Case status badge (open / in-progress / closed)
- Proposed action
- Renewal amount

**Empty state:** When no cases are in the database, renders: "No high-risk accounts in current cohort — The risk sieve routed no accounts into the recovery pipeline for this run."

**Case Detail Drawer:** Clicking any case slides in a full-width detail panel (right-to-left) with:
- Customer profile
- Full pipeline trace: diagnosis → action rankings → policy decision → outcome
- Audit event list with expandable raw JSON payloads (PayloadViewer — JetBrains Mono, syntax-coloured)
- Escape key closes the drawer; focus is trapped inside while open

---

### 5.5 Policy Stress Test — Evaluation (`/evaluation`)

The evaluation control surface for running custom cohort experiments.

**Run Evaluation panel:**
- Cohort size selector: 500 / 1,000 / 3,000 customers
- Seed selector: 42 (default) / 123 / 456 / 789 / 1337
- `RUN SAME-COHORT EVALUATION` button

On submit: `POST /evaluation/run` is called. The UI polls `GET /evaluation/run/{id}` every 2 seconds (max 120 attempts). A progress indicator shows elapsed time.

**Results — when completed:**
- Three-column comparison matrix: Static Dunning / Smart Retry / KhaataPulse
- All metrics: recovered amount, recovery rate, contacts sent/avoided, escalations, blocks, false positives
- Incremental recovery highlighted with sign-appropriate colour
- Run metadata: run_id, seed, cohort size, timestamp, model/policy/simulator versions

**Multi-Seed Validation panel:**
- Cohort size selector: 500 / 1,000
- `RUN MULTI-SEED` button — runs seeds 42, 123, 456 in a single request
- Results matrix shows per-seed results plus cross-seed stability analysis (mean, variance, consistency)
- Validates that KhaataPulse's incremental lift is consistent across independent random worlds

---

## 6. Backend Architecture

### 6.1 Simulator

The simulator generates a synthetic 3,000-customer world. It is the only component with access to ground truth.

**Hidden state** (`CustomerLatentState`) — never exposed to the agent:
- `payment_intent`: genuine willingness to pay
- `cash_flow_health`: temporary liquidity position
- `payment_rail_health`: technical payment infrastructure quality
- `churn_sensitivity`: likelihood of cancellation under contact pressure
- `customer_ltv`: true lifetime value

**Observable events** (generated from latent state, the only data the agent sees):
`invoice_viewed`, `checkout_reopened`, `payment_method_changed`, `payment_failed`, `subscription_changed`, `support_message`, `payment_delayed`, `renewal_approaching`

**Potential outcomes** (used only by the evaluation harness):
- `P(payment | action)` — probability of successful payment given each action
- `P(churn | action)` — probability of churn given each action

The simulator generates the world deterministically from a seed. Same seed always produces the same cohort — enabling reproducible experiments and the same-cohort evaluation invariant.

**API:**
- `POST /simulation/generate` — generate and persist a new world
- `GET /simulation/runs` — list previous simulation runs

### 6.2 Risk Sieve

**Model:** Scikit-learn Logistic Regression with StandardScaler.

**Features (12 observable):**
```
days_to_renewal, invoice_views, checkout_reopens,
payment_method_changes, previous_payment_failures,
average_payment_delay, subscription_age,
payment_success_rate, support_event_count,
days_since_last_payment, payment_failure_code (encoded),
renewal_amount
```

**Output:** `payment_failure_probability` (0.0–1.0) + `top_signals` (3 feature-impact pairs)

**Routing:**
- `P(failure) < 0.30` → Standard flow (no recovery action)
- `P(failure) ≥ 0.30` → KhaataPulse pipeline (~350 of 3,000 accounts)

**API:**
- `POST /risk/predict` — score one or many accounts
- `POST /risk/reason` — run full LangGraph pipeline on a scored account

### 6.3 LangGraph Agent

Nine-node graph, single-stage, no agent-to-agent communication:

```
START → classify_context → generate_diagnosis → generate_action_proposal
      → validate_proposal → rank_actions → policy_check
      → execute_action → record_outcome → END
```

**LLM contract:** Structured output validated against `RecoveryProposal` Pydantic model. Any validation failure triggers the deterministic fallback chain: LLM failure → Smart Rule baseline → Policy Guard → Continue. Every fallback is logged as an `llm_fallback` audit event.

The agent receives only observable data. It never sees `CustomerLatentState` or `PotentialOutcomes`.

### 6.4 Economic Optimizer

Implements the ENR formula for ranking recovery actions:

```
ENR = P(payment | action) × Amount
    − P(churn | action) × LTV
    − ActionCost
```

- `P(payment | action)` and `P(churn | action)` are **estimated** from the action type and cause diagnosis — the agent's own estimates, not the simulator's ground truth
- `ActionCost` is configuration-driven (env variable per action type)
- Eligibility mapping: the LLM's diagnosed cause narrows which actions are eligible before ENR ranking
- Output: `ActionRanking` list sorted descending by ENR; the top-ranked eligible action is proposed to Policy Guard

### 6.5 Policy Guard

Pure deterministic function — same inputs always produce the same output, no side effects, independently unit-tested:

```python
policy_check(action, customer, case) -> PolicyDecision
```

All thresholds come from environment config (never hardcoded):
```env
AUTO_ACTION_LIMIT=10000
MAX_CONTACTS_7D=3
CONTACT_COOLDOWN_HOURS=24
KILL_SWITCH=false
```

Returns `PolicyDecision(status, checks)` where `status` is `APPROVED`, `BLOCKED`, or `ESCALATED`.

### 6.6 Action Service

Typed, idempotent simulated gateway operations. Every action carries:
- `action_id`, `case_id`, `customer_id`, `action_type`
- `amount`, `currency`, `idempotency_key`, `timestamp`, `policy_result`

The service rejects duplicate idempotency keys — re-submitting the same key returns the original result without side effects.

### 6.7 Audit Service

Append-only event log. `log_audit_event()` writes an immutable `AuditEvent` record:

```
id, case_id, event_type, actor, payload, timestamp, idempotency_key
```

Required event types: `risk_detected`, `diagnosis_generated`, `action_proposed`, `policy_check`, `action_executed`, `payment_received`, `case_closed`, `llm_fallback`.

Payloads preserve the structured data required for full reconstruction of any decision.

### 6.8 Evaluation Engine

**Same-cohort invariant (the most important rule):**
```python
world = generate_world(seed)
static_result  = evaluate(world, static_dunning)
smart_result   = evaluate(world, smart_retry)
kp_result      = evaluate(world, khaatapulse)
```

All three policies see the same customers, the same event history, and the same potential outcomes. Only the recovery logic changes. Running separate worlds per policy is a critical integrity violation.

**Dynamic metrics (never hardcoded):**
```
recovered_amount, recovery_rate, incremental_recovery,
contacts_sent, contacts_avoided, human_escalations,
false_positives, policy_blocks
```

**Multi-seed validation:** Seeds 42, 123, 456 (minimum). Results are stored per run with full metadata: `run_id`, `seed`, `cohort_size`, `timestamp`, `model_version`, `policy_version`, `simulator_version`.

**API:**
- `POST /evaluation/run` — start evaluation (async; returns run_id immediately)
- `GET /evaluation/run/{run_id}` — poll for results
- `POST /evaluation/run/multi-seed` — run seeds 42/123/456 in one request
- `GET /evaluation/runs` — list all past runs

---

## 7. Key Architectural Boundaries

Five hard boundaries that no code may cross in either direction:

```
┌─────────────────────────────────────────────────────────┐
│  SIMULATION WORLD                                       │
│  Hidden states (CustomerLatentState)                    │
│  + Potential outcomes (P(payment|action), P(churn|...)) │
└────────────────────┬────────────────────────────────────┘
                     │  observable events only ↓
┌────────────────────▼────────────────────────────────────┐
│  CORE AGENT                                             │
│  Risk → Diagnosis → Proposal → Optimization             │
└────────────────────┬────────────────────────────────────┘
                     │ ranked action ↓
┌────────────────────▼────────────────────────────────────┐
│  POLICY LAYER                                           │
│  Deterministic authorization / stopping rules           │
└────────────────────┬────────────────────────────────────┘
                     │ APPROVED / ESCALATED ↓
┌────────────────────▼────────────────────────────────────┐
│  ACTION LAYER                                           │
│  Typed, idempotent simulated gateway operations         │
└────────────────────┬────────────────────────────────────┘
                     │ outcomes ↓
┌────────────────────▼────────────────────────────────────┐
│  EVALUATION                                             │
│  Baselines → outcomes → incremental recovery            │
└─────────────────────────────────────────────────────────┘
```

**What the LLM can and cannot do:**

| ✅ LLM CAN | ❌ LLM CANNOT |
|---|---|
| Read observable event history | Access CustomerLatentState |
| Classify payment failure cause | Calculate final revenue metrics |
| Propose a recovery action | Bypass Policy Guard |
| Explain its reasoning | Invoke gateway actions directly |
| Request human escalation | Decide legal permission |

---

## 8. Design System

KhaataPulse uses a bespoke dark financial terminal design system. Colour communicates semantic state — never decoration.

### Colour Palette

| Token | Hex | Meaning |
|---|---|---|
| `--bg-primary` | `#07090D` | Page background |
| `--bg-secondary` | `#0C1017` | Secondary background |
| `--surface` | `#11161F` | Panel surface |
| `--surface-elevated` | `#161E2A` | Elevated panels / headers |
| `--accent-recovery` | `#10B981` | Recovered / positive / successful |
| `--accent-warning` | `#F59E0B` | Risk / caution / pending |
| `--accent-critical` | `#EF4444` | Blocked / failed / critical |
| `--accent-ai` | `#6366F1` | AI operations / reasoning |

### Typography

- **UI text:** Inter (self-hosted via `next/font`)
- **Financial metrics:** `.tabular` class — `font-variant-numeric: tabular-nums` ensures digits align in tables
- **Technical text** (IDs, timestamps, event names, payloads, policy decisions): `.mono` class — JetBrains Mono

### Risk Score → Colour Mapping

| Score range | Colour | Meaning |
|---|---|---|
| < 0.30 | Recovery green | Low risk — standard flow |
| 0.30 – 0.70 | Warning amber | Medium risk — KhaataPulse pipeline |
| ≥ 0.70 | Critical red | High risk — immediate attention |

### Motion

Motion communicates system state, not decoration:

| Event | Animation |
|---|---|
| Risk detected | Amber pulse around affected account |
| AI reasoning | Signal lines animate through diagnosis panel |
| Policy check | Sequential gate indicators with 60ms stagger |
| APPROVED | Green pulse then steady |
| BLOCKED | Sharp red interruption, then stop |
| Payment recovered | Metric counter rises |
| Pipeline stages | 400ms CSS-staggered step activation |

All animations respect `prefers-reduced-motion` — the CSS reduced-motion block zeroes both duration and delay for all animations.

---

## 9. Running the Application

### Prerequisites
- Docker Desktop
- Node.js 18+ (for frontend dev server)

### Start all services

```bash
docker compose up
```

This starts:
- `postgres` — PostgreSQL 16 with all migrations applied (Alembic runs on startup)
- `backend` — FastAPI on port 8000

### Start the frontend dev server

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:3000`.

### Environment configuration

Copy `.env.example` to `.env` and adjust:

```env
DATABASE_URL=postgresql://khaatapulse:khaatapulse@localhost:5432/khaatapulse
LLM_API_KEY=           # Optional — demo mode works without it
LLM_MODEL=claude-sonnet-5

APP_ENV=development

AUTO_ACTION_LIMIT=10000
MAX_CONTACTS_7D=3
CONTACT_COOLDOWN_HOURS=24

KILL_SWITCH=false
```

### Build for production

```bash
cd frontend
npm run build     # Produces standalone Next.js output
npm run lint      # Zero errors required
```

### Run backend tests

```bash
cd backend
pip install -r requirements.txt
pytest             # 254 passed, 6 skipped (6 require Docker DB)
```

---

## 10. API Reference (Summary)

All endpoints are served from the backend at `http://localhost:8000`. The frontend proxies `/api/*` → backend via Next.js rewrites.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/simulation/generate` | Generate a new 3,000-customer simulation world |
| GET | `/simulation/runs` | List simulation run history |
| POST | `/risk/predict` | Score account(s) with the risk model |
| POST | `/risk/reason` | Run full LangGraph pipeline on an account |
| POST | `/evaluation/run` | Start same-cohort evaluation (async) |
| GET | `/evaluation/run/{id}` | Poll evaluation run status and results |
| POST | `/evaluation/run/multi-seed` | Run seeds 42/123/456 in one request |
| GET | `/evaluation/runs` | List all past evaluation runs |
| GET | `/demo/hero` | Fetch the deterministic demo customer (no DB needed) |
| POST | `/demo/simulate` | Trigger a simulated pipeline run (no DB needed) |
| GET | `/cases/` | List recovery cases from DB |
| GET | `/cases/{case_id}` | Get full case detail with audit events |

**Security note:** `BACKEND_URL` is server-side only. The Next.js rewrite proxies all `/api/*` requests — the browser never sees the internal backend origin. API keys are never exposed to the frontend.

---

## 11. Demo Mode

Demo mode is a first-class requirement. The 3-minute demo must work even when:
- The LLM provider is unavailable
- No network connectivity
- No long-running evaluation in progress
- No real payment system exists

**Demo endpoints** (`/demo/hero`, `/demo/simulate`) produce deterministic results from precomputed in-memory state:
- The same hero customer always appears (deterministic seed → same account)
- LLM responses use the Smart Retry fallback (structured, valid, instant)
- All 9 pipeline nodes execute and produce real outputs
- All 8 audit event types are generated and returned
- Gateway actions simulate success/escalation/block status correctly

**The `SIMULATE PAYMENT WEBHOOK` button** on the dashboard uses `/demo/simulate` — it runs the full pipeline end-to-end in ~100ms and animates the result without requiring any external dependency.

---

*Built with KhaataPulse Architectural MVP Engineering Contract v1.0 · All evaluation metrics are dynamically computed — no values are authored or hardcoded.*
