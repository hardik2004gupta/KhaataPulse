# KhaataPulse - Project Structure Reference

Every file and folder in the main application, explained.

---

## Root Directory

```
khaata-pulse/
├── CLAUDE.md
├── README.md
├── WALKTHROUGH.md
├── PROJECT_STRUCTURE.md          ← this file
├── KhaataPulse - Architectural MVP Engineering Contract.pdf
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.override.yml
├── media/                        10 visual assets
├── backend/                      FastAPI + Python backend
└── frontend/                     Next.js 14 frontend
```

| File / Folder | Purpose |
|---|---|
| `CLAUDE.md` | The executable engineering contract. Governs all implementation decisions - architecture, boundaries, thresholds, forbidden patterns, definition of done. Read this before touching any code. |
| `README.md` | Production-grade project README with all 10 visual assets, architecture diagrams, quick-start guide, API reference, and test suite summary. |
| `WALKTHROUGH.md` | Detailed screen-by-screen walkthrough of every application surface with component-level descriptions. |
| `KhaataPulse - Architectural MVP Engineering Contract.pdf` | The original authoritative specification. CLAUDE.md is derived from it. |
| `.env` | Active environment configuration (not committed). Contains `DATABASE_URL`, `LLM_API_KEY`, policy thresholds, `KILL_SWITCH`. |
| `.env.example` | Template for `.env`. Documents all required and optional variables with descriptions. |
| `.gitignore` | Excludes `.env`, `__pycache__`, `.next`, `node_modules`, `.pytest_cache`, and build artifacts. |
| `docker-compose.yml` | Defines three services: `postgres` (port 5435→5432), `backend` (port 8000), `frontend` (port 3000). Backend runs Alembic migrations on startup. |
| `docker-compose.override.yml` | Host-port override for PostgreSQL (5435) to avoid conflicts with other local Postgres instances. |

---

## `media/` - Visual Assets

Ten product screenshots used in `README.md`, ordered by narrative role.

| File | Used for |
|---|---|
| `01_khaatapulse_brand_identity_mark.png` | Brand mark / logo - appears in README hero section |
| `02_khaatapulse_flagship_hero_revenue_recovery.png` | Primary hero screenshot of the Revenue Recovery Command Center |
| `03_khaatapulse_intelligence_pipeline.png` | The 7-stage Detect→Audit pipeline visualization |
| `04_khaatapulse_policy_guard.png` | Policy Guard sequential checkpoint interface |
| `05_khaatapulse_revenue_time_machine.png` | Revenue Time Machine - observable event timeline |
| `06_khaatapulse_expected_net_revenue.png` | Economic Optimizer - ENR-ranked action table |
| `07_khaatapulse_same_world_different_policies.png` | Same-cohort evaluation methodology diagram |
| `08_khaatapulse_immutable_audit_trail.png` | Audit event stream with expandable payloads |
| `09_khaatapulse_revenue_recovery_under_control.png` | Closing product visual - safety and control model |
| `10_khaatapulse_intelligence_without_autonomy.png` | Core architectural philosophy - AI proposes, policy decides |

---

## `backend/` - FastAPI Application

### Root backend files

| File | Purpose |
|---|---|
| `Dockerfile` | Multi-stage Python 3.11 image. Installs `requirements.txt`, copies application code, runs Alembic migrations then Uvicorn on port 8000. |
| `requirements.txt` | All Python dependencies: FastAPI 0.115, SQLAlchemy 2.0, Alembic 1.14, Pydantic v2, LangGraph 0.2, scikit-learn, numpy, anthropic, pytest, httpx. |
| `pytest.ini` | Test configuration: sets `testpaths = tests`, registers markers (`integration`, `slow`), configures asyncio mode. |
| `alembic.ini` | Alembic configuration pointing to `alembic/env.py` for migration management. |

### `backend/alembic/` - Database Migrations

| File | Purpose |
|---|---|
| `env.py` | Alembic environment: imports `Base` metadata, reads `DATABASE_URL` from environment, configures the migration context. |
| `script.py.mako` | Template used when generating new migration files with `alembic revision`. |
| `versions/001_initial_schema.py` | Creates the core tables: `customers`, `subscriptions`, `payments`, `events`, `simulation_runs`. |
| `versions/002_phase3_recovery_audit.py` | Adds recovery pipeline tables: `recovery_cases`, `actions`, `audit_events`. Also adds `dispute_hold`, `legal_hold`, `opt_out` boolean columns to `customers`. |
| `versions/003_evaluation_tables.py` | Adds evaluation tables: `evaluation_runs`, `evaluation_results`. |

### `backend/app/` - Application Package

#### `app/main.py`
The FastAPI application entry point. Creates the `FastAPI` instance (`title="KhaataPulse"`, `version="1.0.0"`), adds CORS middleware (allowing `http://localhost:3000`), and registers all five routers: `simulator`, `risk`, `evaluation`, `demo`, `cases`. Also exposes `GET /health`.

#### `app/core/` - Configuration and Logging

| File | Purpose |
|---|---|
| `config.py` | `Settings` dataclass powered by `pydantic-settings`. Reads all environment variables: `DATABASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `APP_ENV`, `AUTO_ACTION_LIMIT`, `MAX_CONTACTS_7D`, `CONTACT_COOLDOWN_HOURS`, `KILL_SWITCH`, and per-action cost variables (`ACTION_COST_SILENT_RETRY`, etc.). All policy thresholds come from here - never hardcoded elsewhere. `get_settings()` is a cached factory. |
| `logging.py` | Configures structured JSON logging via Python's `logging` module. `get_logger(name)` returns a module-scoped logger. Logs include `event`, `level`, `timestamp`, and arbitrary structured fields. |

#### `app/db/` - Database Layer

| File | Purpose |
|---|---|
| `base.py` | Declares `Base = declarative_base()` - the SQLAlchemy metadata object inherited by all ORM models. |
| `session.py` | Creates the SQLAlchemy `engine` from `DATABASE_URL`. Provides `SessionLocal` (session factory) and `get_db()` - a FastAPI dependency that yields a database session and closes it after the request. |
| `models/__init__.py` | Re-exports all ORM models so Alembic's `env.py` can import `Base` with all tables registered. |
| `models/customer.py` | `Customer` ORM model: `id`, `name`, `segment` (consumer/smb/enterprise), `ltv`, `subscription_id`, `dispute_hold`, `legal_hold`, `opt_out`, `created_at`. |
| `models/subscription.py` | `Subscription`: `id`, `customer_id`, `plan`, `amount`, `currency`, `renewal_at`, `status`. |
| `models/payment.py` | `Payment`: `id`, `customer_id`, `subscription_id`, `amount`, `status`, `failure_code`, `payment_method`, `created_at`. |
| `models/event.py` | `CustomerEvent`: `id`, `customer_id`, `event_type`, `payload` (JSONB), `timestamp`. Represents observable events only - no hidden state. |
| `models/simulation_run.py` | `SimulationRun`: tracks cohort generation runs with `seed`, `cohort_size`, `status`, timing. |
| `models/recovery_case.py` | `RecoveryCase`: the central record for one customer going through the KhaataPulse pipeline. Contains `risk_score`, `risk_level`, `diagnosis`, `diagnosis_confidence`, `proposed_action`, `selected_action`, `policy_status`, `outcome_status`, timestamps. |
| `models/action.py` | `RecoveryAction`: records every executed gateway action. Contains `action_type`, `amount`, `currency`, `idempotency_key`, `timestamp`, `policy_result` (JSONB). The Policy Guard queries this table for contact-limit and cooldown checks. |
| `models/audit_event.py` | `AuditEvent`: the immutable audit log entry. Contains `case_id`, `event_type`, `actor`, `payload` (JSONB), `timestamp`, `idempotency_key`. Append-only by convention - no update or delete operations exist in the codebase. |
| `models/evaluation.py` | `EvaluationRun` and `EvaluationResult`. `EvaluationRun` holds run metadata (seed, cohort size, versions, status). `EvaluationResult` holds per-policy metrics as JSONB. |

#### `app/simulator/` - World Generator (Ground Truth Layer)

The simulator is the only component with access to hidden state and potential outcomes. Everything here is strictly isolated from the agent.

| File | Purpose |
|---|---|
| `latent_state.py` | `CustomerLatentState` - the hidden ground truth for one customer: `payment_intent`, `cash_flow_health`, `payment_rail_health`, `churn_sensitivity`, `customer_ltv`. **Never passed to any API route, agent node, or frontend component.** Existence in this file is the only place it should appear. |
| `outcomes.py` | `PotentialOutcomes` - per-customer, per-action probability table: `P(payment \| action)` and `P(churn \| action)` for every valid action type. **Available to the evaluation harness only.** The agent estimates its own probabilities independently. |
| `events.py` | `generate_observable_events()` - converts `CustomerLatentState` into a sequence of observable events (`payment_failed`, `invoice_viewed`, `checkout_reopened`, `payment_method_changed`, `support_message`, `payment_delayed`, `renewal_approaching`, `subscription_changed`). This is the only crossing of the hidden→observable boundary. |
| `generator.py` | `generate_world(seed)` - the deterministic cohort generator. Given a seed, produces exactly the same 3,000 customers every time. Generates `CustomerLatentState`, derives observable events, and creates `PotentialOutcomes`. Same seed always → same world. |
| `world.py` | Defines the isolation types: `WorldInternal` (full ground truth, evaluation-harness only) and `ObservableWorld` (observable data only, agent-facing). Also defines `ObservableCustomerData`, `ObservableEvent`, `ObservablePayment`, `ObservableSubscription` - the typed data structures the agent receives. |
| `persistence.py` | `persist_world(world, db)` - writes a generated world to PostgreSQL. Stores customers, subscriptions, payments, and events. **Never stores** `CustomerLatentState` or `PotentialOutcomes` in the database - they live only in memory during evaluation. |

#### `app/schemas/` - API Schemas

| File | Purpose |
|---|---|
| `simulator.py` | Pydantic response schemas for the simulator API: `SimulationRunResponse`, `SimulationRunListResponse`. Explicitly excludes hidden state fields - only observable data appears in API responses. |

#### `app/risk/` - Risk Sieve

| File | Purpose |
|---|---|
| `features.py` | `RiskFeatures` - a frozen dataclass of 12 observable features. `FEATURE_NAMES` list defines the exact array order used by the model. `FeatureBuilder.build(observable_data)` converts `ObservableCustomerData` into `RiskFeatures`. No hidden state fields exist on this class - isolation enforced by the type system. Features: `days_to_renewal`, `invoice_views`, `checkout_reopens`, `payment_method_changes`, `previous_payment_failures`, `average_payment_delay`, `subscription_age`, `payment_success_rate`, `support_event_count`, `days_since_last_payment`, `renewal_amount`, `segment_encoded`. |
| `model.py` | `RiskPredictor` - wraps a scikit-learn `LogisticRegression` + `StandardScaler` pipeline. `train(records)` fits from scratch on observable data. `predict(features)` returns `RiskPrediction(risk_score, risk_level, top_signals)`. Top signals: the 3 features with the highest absolute logistic coefficient × feature value impact. `MODEL_VERSION` constant used for audit metadata. `get_risk_predictor()` returns a cached singleton trained on the current world. |
| `service.py` | `RiskService` - orchestrates scoring. `route(observable_data)` returns a `RoutingDecision`: score, level, top signals, and whether this account is routed to LangGraph (`score >= threshold`) or standard flow. Threshold comes from `Settings` (default 0.30). |

#### `app/agent/` - LangGraph Agent

| File | Purpose |
|---|---|
| `schemas.py` | `RecoveryProposal` - the Pydantic model the LLM must produce. Fields: `cause` (5 literals), `confidence` (0.0–1.0), `proposed_action` (5 literals), `rationale` (str), `risk_level` (3 literals). Any response that fails validation triggers the fallback chain. |
| `state.py` | `RecoveryReasoningState` - TypedDict that carries data between all 9 graph nodes. Contains both observable inputs (risk score, events, subscription info) and accumulated outputs (diagnosis, action rankings, policy decision, execution result, audit record). No hidden state fields. |
| `reasoning.py` | LLM provider abstraction. `BaseReasoningModel` (ABC), `StubReasoningModel` (deterministic, no API call - used in demo mode and CI), `AnthropicReasoningModel` (calls Claude with a structured prompt, validates output against `RecoveryProposal`). `get_reasoning_model()` returns Anthropic if `LLM_API_KEY` is set, Stub otherwise. |
| `fallback.py` | `smart_retry_proposal(risk_score, events)` - the deterministic LLM fallback. Applies rule-based logic to observable data to produce a valid `RecoveryProposal`. Used when the LLM fails for any reason. |
| `nodes.py` | All 9 LangGraph node implementations: `classify_context`, `make_generate_diagnosis`, `generate_action_proposal`, `validate_proposal`, `make_rank_actions`, `make_policy_check`, `make_execute_action`, `make_record_outcome`. Each node takes the graph state and returns a state update dict. |
| `graph.py` | `build_recovery_graph(reasoning_model, db)` - compiles the `StateGraph` with nodes added in the required order and edges wired sequentially. Returns a compiled LangGraph ready for `invoke()`. `make_initial_state()` constructs the starting state from an observable customer record. |
| `fallback.py` | Deterministic Smart Retry fallback used when LLM fails. Produces a valid `RecoveryProposal` from observable signals alone. |

#### `app/optimizer/` - Economic Optimizer

| File | Purpose |
|---|---|
| `eligibility.py` | Maps each `cause` to the set of eligible `action_type` values. For example, `card_expired` makes `smart_link` eligible but not `suppress`. The LLM's diagnosis determines which actions are even considered by the optimizer. |
| `enr.py` | `compute_enr(p_payment, amount, p_churn, ltv, action_cost)` - the ENR formula using `Decimal` arithmetic. `estimate_probabilities(cause, action_type)` - returns `(p_payment, p_churn)` from a lookup table indexed by cause × action type. These are **estimated** values, not simulator ground truth. `ActionRanking` frozen dataclass holds one ranked result. |
| `ranker.py` | `rank_eligible_actions(cause, amount, ltv, db)` - calls `eligibility.py` to get the candidate set, calls `enr.py` to compute ENR for each candidate, returns the list sorted descending by ENR. The first item is the recommended action. |

#### `app/policy/` - Policy Guard

| File | Purpose |
|---|---|
| `guard.py` | `policy_guard(customer_id, action_type, amount, idempotency_key, dispute_hold, legal_hold, opt_out, db)` - evaluates all 8 policy rules in strict order. Returns `PolicyDecision(status, checks, block_reason)`. Pure function - no side effects, no randomness. All thresholds from `Settings`. The `checks` dict records a per-rule pass/fail boolean for every rule evaluated, which becomes part of the audit trail. |

#### `app/actions/` - Action Service

| File | Purpose |
|---|---|
| `service.py` | `ActionService.execute(request, db)` - takes an `ActionRequest` (typed: `action_id`, `case_id`, `customer_id`, `action_type`, `amount`, `currency`, `idempotency_key`, `timestamp`, `policy_result`) and writes a `RecoveryAction` row. Checks for duplicate idempotency keys before writing - returns the original result without a second write if already executed. Returns `ActionResult` with `status` (`executed`, `blocked`, `escalated`) and metadata. |

#### `app/audit/` - Audit Service

| File | Purpose |
|---|---|
| `service.py` | `AuditService.log_audit_event(case_id, event_type, actor, payload, db)` - appends one `AuditEvent` row. Eight supported event types: `risk_detected`, `diagnosis_generated`, `action_proposed`, `policy_check`, `action_executed`, `payment_received`, `case_closed`, `llm_fallback`. Returns `None` in no-db mode (demo). No update or delete operations exist - the service is append-only by design. |

#### `app/evaluation/` - Evaluation Engine

| File | Purpose |
|---|---|
| `metrics.py` | `PolicyEvaluationResult` and `EvaluationRunResult` - dataclasses for evaluation output. Every field is computed dynamically: `recovered_amount`, `recovery_rate`, `contacts_sent`, `contacts_avoided`, `human_escalations`, `false_positives`, `policy_blocks`, `total_at_risk_amount`, `cases_evaluated`. No default values - all must be computed by the evaluator. |
| `policies.py` | Three `RecoveryPolicy` implementations (all share `evaluate_customer(observable_data, potential_outcomes)` interface): `StaticDunningPolicy` (failure count → retry timing → escalation), `SmartRetryPolicy` (failure code → deterministic retry timing → payment link → escalation), `KhaataPulsePolicy` (risk sieve → stub LLM → ENR optimizer → policy guard, no-db mode). |
| `evaluator.py` | `EvaluationWorld` - wraps a `WorldInternal` and exposes `PotentialOutcomes` only to the evaluator (not to policies). `evaluate_policy_on_world(world, policy)` - runs one policy across all customers in the world, uses `PotentialOutcomes` to compute expected recovered amounts. `run_same_cohort_evaluation(seed, cohort_size)` - generates the world **once**, then calls `evaluate_policy_on_world` three times. The same-cohort invariant is enforced here. |
| `runner.py` | `run_evaluation(seed, cohort_size, db)` - orchestrates a full evaluation run, persists `EvaluationRun` and `EvaluationResult` rows, returns `EvaluationRunResult`. `run_multi_seed_evaluation(seeds, cohort_size, db)` - runs seeds 42, 123, 456 (default). `get_run_from_db(run_id, db)` - retrieves a previously completed run in the same shape as the POST response (for frontend polling). |

#### `app/api/routes/` - FastAPI Routers

| File | Endpoints | Purpose |
|---|---|---|
| `simulator.py` | `POST /simulation/generate`, `GET /simulation/runs` | Generate a new world from seed; list past simulation runs. |
| `risk.py` | `POST /risk/predict`, `POST /risk/reason` | Score one or many accounts; run the full 9-node LangGraph pipeline on an account. |
| `evaluation.py` | `POST /evaluation/run`, `GET /evaluation/run/{id}`, `POST /evaluation/run/multi-seed`, `GET /evaluation/runs` | Same-cohort evaluation (async); poll results; multi-seed validation; list history. |
| `demo.py` | `GET /demo/hero`, `POST /demo/simulate` | Return the deterministic hero customer (no DB required); run full pipeline in demo mode synchronously. |
| `cases.py` | `GET /cases/`, `GET /cases/{case_id}` | List recovery cases from the database; get full case detail with audit events. |

### `backend/tests/` - Test Suite

260 tests pass (6 skipped - require a live Docker PostgreSQL).

| Folder / File | What it tests |
|---|---|
| `conftest.py` | Shared pytest fixtures: in-memory SQLite engine for DB tests, sample `ObservableCustomerData`, pre-built worlds. |
| `simulator/test_simulator.py` | Cohort generation determinism (same seed → same world), cohort size, simulator isolation (hidden state never in observable output), observable event types. |
| `db/test_models.py` | All 10 ORM tables exist and accept valid data; referential integrity; Phase 2, 3, and 4 columns present. |
| `risk/test_features.py` | Feature engineering from observable data, isolation (no hidden fields), `to_array()` contract (shape = 12). |
| `risk/test_model.py` | Model training, deterministic prediction, threshold routing (P < 0.30 → standard, P ≥ 0.30 → LangGraph), top-signal explainability. |
| `agent/test_graph.py` | 9-node order, `RecoveryProposal` validation, LLM schema failures, fallback activation, all Phase 3 node outputs, agent isolation (no hidden state in state dict). |
| `optimizer/test_enr.py` | ENR formula correctness, all cause × action combinations, Decimal precision, eligibility mapping, ranking determinism, action cost effects. |
| `policy/test_guard.py` | Each of the 8 rules independently: APPROVED, BLOCKED (kill switch, dispute hold, legal hold, opt-out, idempotency, contact limit, cooldown), ESCALATED (amount threshold). Configuration-driven thresholds. |
| `evaluation/test_evaluator.py` | Same-cohort invariant, `EvaluationWorld` isolation (policies never see `PotentialOutcomes`), false positive detection, incremental recovery formula, reproducibility, recovery rate bounds. |
| `evaluation/test_runner.py` | Multi-seed (42, 123, 456), no-db mode, DB persistence (skipped without Docker), re-run overwrite. |
| `evaluation/test_api.py` | `POST /evaluation/run`, `GET /evaluation/run/{id}`, multi-seed endpoint, error responses, field contracts (all metrics present, no hardcoded values). |
| `integration/test_e2e_pipeline.py` | **18 end-to-end tests** - `TestGoldenPath` (full 9-node pipeline, no hidden state in state), `TestPolicyGuardBypass` (BLOCKED → no execution), `TestBlockedAction` (kill switch), `TestEscalatedAction` (amount threshold), `TestIdempotency` (duplicate rejection), `TestAuditIntegrity` (append-only, no-db fallback), `TestSameCohortInvariant` (determinism, isolation, multi-seed). |

---

## `frontend/` - Next.js 14 Application

### Root frontend files

| File | Purpose |
|---|---|
| `Dockerfile` | Multi-stage build: `node:18-alpine` builder runs `npm ci` + `next build` (standalone output), then copies the standalone artifact into a minimal runtime image. Exposes port 3000. |
| `.dockerignore` | Excludes `node_modules`, `.next`, `.env.local` from the Docker build context. |
| `.env.local.example` | Template for local frontend environment. Only one variable: `NEXT_PUBLIC_APP_ENV`. `BACKEND_URL` is server-side only - never in `.env.local`. |
| `.eslintrc.json` | ESLint config extending `next/core-web-vitals`. Zero errors required for the build to pass. |
| `next.config.mjs` | Two rewrite rules: (1) `source: "/api/cases"` → `destination: ${BACKEND_URL}/cases/` (explicit, prevents FastAPI 307 from leaking the internal origin); (2) `source: "/api/:path*"` → `destination: ${BACKEND_URL}/:path*` (wildcard catch-all). Security headers: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`. |
| `tailwind.config.ts` | All design system tokens (CLAUDE.md §29): semantic colour tokens (`recovery`, `warning`, `critical`, `ai`), surface colours, `rounded-panel` (0.625rem), `max-w-shell` (80rem), `duration-fast/base/slow`, `ease-out/in-out`, `text-hero/display/metric/eyebrow`, `tracking-eyebrow`, font families. |
| `postcss.config.js` | PostCSS config enabling Tailwind CSS and Autoprefixer. |
| `tsconfig.json` | TypeScript config: strict mode, path alias `@/*` → `./`, `moduleResolution: bundler`, targets ES2017. |
| `next-env.d.ts` | Auto-generated Next.js TypeScript declarations. Do not edit. |
| `package.json` | Dependencies: `next 14`, `react 18`, `react-dom 18`. Dev: TypeScript 5, Tailwind 3, ESLint, `@types/*`. No third-party component libraries - all UI is custom. |

### `frontend/app/` - Next.js App Router

| File / Folder | Route | Purpose |
|---|---|---|
| `layout.tsx` | All routes | Root layout. Loads `Inter` and `JetBrains Mono` via `next/font` (self-hosted, no render-blocking external fonts). Sets `<html lang="en">`, applies font CSS variables, renders `{children}`. |
| `globals.css` | Global | Design system CSS: CSS custom properties (all colour tokens, motion variables, z-index scale), base styles, `.tabular` and `.mono` utility classes, ambient background layers (5 CSS-only layers), all animation keyframes, glow utilities, drawer/overlay classes, reduced-motion block (`animation-duration: 0.001ms !important`, `animation-delay: 0ms !important`). |
| `page.tsx` | `/` | Cinematic landing page. Composes: `<AmbientBackground>`, `<HeroSection>`, `<PipelineSection>`, `<ArchitectureStory>`, `<ProductPreview>`, `<TimeMachinePreview>`, `<FinalCTA>`. Do not modify. |
| `dashboard/page.tsx` | `/dashboard` | Revenue Recovery Command Center. Fires `POST /evaluation/run` (seed=42, cohort=3,000) and `GET /demo/hero` on mount. Polls evaluation every 2s (max 120 attempts). Renders `<CommandShell>` wrapping: `<DashboardHeader>`, `<HeroKPIGrid>`, `<RevenueExposure>`, `<IncrementalHero>`, `<PolicyComparison>`, `<HeroCasePanel>`, `<LiveActivity>`, `<LiveEventStream>`, audit section. |
| `dashboard/time-machine/page.tsx` | `/dashboard/time-machine` | Revenue Time Machine. Fetches the hero case via `demoApi.getHeroCase()`. Renders customer subject panel and `<EventTimeline>` with observable events and pipeline decisions side-by-side. |
| `cases/page.tsx` | `/cases` | Risk Queue. Fetches `GET /cases/`. Renders `<CommandShell>` wrapping `<RiskQueue>`. Opens `<CaseDetailDrawer>` when a case is clicked. |
| `evaluation/page.tsx` | `/evaluation` | Policy Stress Test. Renders `<CommandShell>` wrapping `<EvaluationRunner>`, `<EvaluationResults>`, and `<MultiSeedMatrix>`. |

### `frontend/components/` - React Components

#### `components/shell/` - Application Frame

| File | Purpose |
|---|---|
| `CommandShell.tsx` | The application frame used by every operational surface (`/dashboard`, `/cases`, `/evaluation`, `/dashboard/time-machine`). Renders `<TopBar>` (full width) + a flex row of `<Sidebar>` (220px) and `<main>`. Manages mobile nav open/close state. Collapses sidebar on route change via `usePathname`. Props: `children`, `evalResult?` (passed to TopBar for run context). |
| `TopBar.tsx` | 48px sticky top bar (`z-nav`). Left: hamburger (mobile) + KhaataPulse logo. Center: run context chip - shows `SEED 42 · 3,000 ACCOUNTS` when `evalResult` is provided. Right: `TelemetryChip` ("System · Healthy", "Automation · Active"), live clock (updates every second via `useEffect`). |
| `Sidebar.tsx` | Desktop: 220px sticky rail (`hidden lg:flex`). Mobile: fixed slide-in sheet (`translate-x-0` / `-translate-x-full`). Four nav sections: Command (Overview), Operations (Command Center, Risk Queue, Revenue Time Machine), Evaluation (Policy Comparison, Stress Test), Governance (Audit Trail). Active state shown with 2px left accent bar in section-appropriate colour. Escape key closes mobile overlay. Version badge at bottom: `v1.0 · MVP`. |

#### `components/home/` - Landing Page Sections

| File | Purpose |
|---|---|
| `AmbientBackground.tsx` | Five CSS-only fixed background layers rendered behind all landing content: base wash, structural grid, three animated atmospheric blobs (ai/recovery/warning), horizon fade, scanning line. No canvas, no JS loops. |
| `HeroSection.tsx` | Hero: KhaataPulse brand mark, headline ("Recover revenue before it becomes lost."), description, two CTAs (Enter Command Center, Explore Evaluation), animated pipeline badge. |
| `HeroVisualization.tsx` | Animated SVG of the 9-node LangGraph graph. Signal dots travel between nodes; connections energise as signals pass. Nodes labeled: `classify_context` → `record_outcome`. CSS animation, no JS intervals. |
| `PipelineSection.tsx` | "The Intelligence Pipeline" - seven numbered stage cards, each with a title, description, and responsible technology. |
| `ArchitectureStory.tsx` | "Intelligence without autonomy" - five architectural boundary cards explaining what each layer can and cannot do. |
| `ProductPreview.tsx` | "Every layer, visible" - four illustrative product panels: Risk Intelligence, AI Diagnosis, Economic Optimizer, Policy Guard. Marked "illustrative values · not live data". |
| `TimeMachinePreview.tsx` | "Revenue Time Machine" - illustrative customer journey timeline showing observable events. Marked "Example · Not Live Data". |
| `FinalCTA.tsx` | Closing section with pipeline tagline, positioning statement, and two links. Renders the page footer. |

#### `components/dashboard/` - Command Center Panels

| File | Purpose |
|---|---|
| `DashboardHeader.tsx` | Section header for the Command Center. Shows the evaluation state (loading / completed / error), run ID in monospace, seed + cohort size, and a Retry button on failure. |
| `HeroKPIGrid.tsx` | Six `<MetricCard>` components in a responsive grid (2 cols → 3 cols at `lg`). Shows: Recovered (KhaataPulse), KP Recovery Rate (with pp lift vs Smart Retry), Revenue Exposure, Contacts Avoided (with delta vs Smart Retry), Human Escalations, Policy Blocks. All values derived from `EvaluationRunResult`. Shows `<MetricSkeleton>` during loading. |
| `IncrementalHero.tsx` | The dominant KPI panel. `Incremental Recovery = KhaataPulse − Smart Retry`, displayed in large tabular numerals with sign-appropriate colour, directional radial gradient wash, recovery rate lift, contacts saved delta. Glow colour tracks sign of incremental recovery. |
| `RevenueExposure.tsx` | Proportional horizontal bar chart comparing at-risk revenue across all three policies. Bar widths computed from evaluation data with `.bar-grow` CSS transition. |
| `PolicyComparison.tsx` | Three-column table: Static Dunning / Smart Retry / KhaataPulse. Each metric row shows absolute values plus the KhaataPulse delta vs Smart Retry (colour-coded: recovery-green for improvements, warning-amber for regressions). |
| `HeroCasePanel.tsx` | Full pipeline narrative for the demo customer. Customer header → plan/renewal/last payment fields → Risk Assessment (score, level, top signals) → `<DiagnosisPanel>` → action rankings table → `<PolicyGuardViz>` → Outcome (action type, status, idempotency key in mono) → "Replay in Time Machine →" link. |
| `LiveActivity.tsx` | Recent audit events list for the hero case. Each event: event type in mono, timestamp, actor. Idle state: "Pipeline awaiting activity" in mono. |
| `NavBar.tsx` | Legacy component from Phase 1 used by the landing page. Top navigation bar with logo and links. Separate from the `CommandShell` sidebar nav. |

#### `components/risk/` - Risk and Case Components

| File | Purpose |
|---|---|
| `DiagnosisPanel.tsx` | AI Diagnosis display. Shows cause label (formatted), `ConfidenceBar` (CSS `--bar-width` fill, ai-violet above 50%, warning-amber below, ambient pulse when `isLoading`), rationale text, top 3 risk signals with impact bars. |
| `PolicyGuardViz.tsx` | Sequential policy checkpoint visualization. Eight rule rows, each with a pass/fail icon. CSS stagger via `--gate-index`: each gate animates in 60ms apart. APPROVED gates emit a brief green pulse then settle; BLOCKED gates trigger a sharp red interruption via `.gate-fail` keyframe. |
| `AuditTimeline.tsx` | Chronological audit event list. Each event: coloured icon (by event type), event name in mono, actor, timestamp. Events are expandable to show the raw `payload`. |
| `CaseDetailDrawer.tsx` | Slide-in case detail panel (right edge, `min(520px, 100vw)`, `z-drawer`). Escape key closes. `role="dialog"`, `aria-modal`, `invisible` when closed (removes from tab order). Shows: customer header → risk score → diagnosis → action rankings → policy decision → execution outcome → audit events with `<PayloadViewer>`. |
| `PayloadViewer.tsx` | Syntax-coloured JSON viewer. Renders audit event payloads in JetBrains Mono. Keys in ai-violet, strings in recovery-green, numbers in warning-amber, booleans in critical-red. Copy-to-clipboard button. |
| `RiskQueue.tsx` | Paginated list of recovery cases. Each case card: customer name, risk indicator bar (colour tracks score threshold), risk level text, status badge, proposed action, renewal amount. Empty state via `<EmptyState>`. Aria labels on interactive elements; risk level text always accompanies colour. |

#### `components/simulation/` - Webhook Simulation

| File | Purpose |
|---|---|
| `LiveEventStream.tsx` | The `SIMULATE PAYMENT WEBHOOK` button and 6-step pipeline animation. On click, calls `POST /demo/simulate`. All 6 stage cards render immediately with 400ms CSS `animation-delay` stagger (not JS timers). Completion detected via `animationend` on the last card (guarded against bubbling). Respects `prefers-reduced-motion` via existing CSS block. Shows result summary after animation. |

#### `components/timemachine/` - Revenue Time Machine

| File | Purpose |
|---|---|
| `EventTimeline.tsx` | Two-column timeline: Observable Event Stream (left) and Pipeline Decision Log (right). Each entry is expandable to show the raw payload. Observable events use warning-amber accents; pipeline decisions use ai-violet. The visual separation communicates the boundary between what the customer world emitted and what KhaataPulse derived from it. |

#### `components/evaluation/` - Stress Test Components

| File | Purpose |
|---|---|
| `EvaluationRunner.tsx` | Form for triggering a custom evaluation: cohort size selector (500 / 1,000 / 3,000), seed selector (42 / 123 / 456 / 789 / 1337), submit button. Calls `POST /evaluation/run`, polls for result. Progress indicator shows elapsed time. On error: `<ErrorPanel>` with retry. |
| `EvaluationResults.tsx` | Displays a completed evaluation run: three-column metrics table, run metadata (run_id, seed, cohort, timestamp, versions), incremental recovery highlighted. |
| `MultiSeedMatrix.tsx` | Triggers `POST /evaluation/run/multi-seed`. Cohort size selector (500 / 1,000). Results show per-seed metrics plus cross-seed stability analysis. |

#### `components/ui/` - Shared UI Primitives

| File | Purpose |
|---|---|
| `MetricCard.tsx` | Reusable metric display panel. Props: `label`, `value`, `subValue?`, `accent?` (`recovery`/`warning`/`critical`/`ai`/`neutral`), `size?` (`sm`/`md`/`lg`). Accent determines left border colour and text colour. Value uses `.tabular`. Mounts with `animate-fade-in`. |
| `PolicyBadge.tsx` | Pill badge for policy names. Three variants: `static_dunning`, `smart_retry`, `khaatapulse`. Each has a distinct colour. Text label always accompanies colour (accessibility). |
| `RiskIndicator.tsx` | Coloured horizontal bar + level text for risk scores. Colour tracks score: < 0.30 → neutral/recovery, 0.30–0.70 → warning, ≥ 0.70 → critical. Risk level text spelled out (not colour-only). |
| `StatusBadge.tsx` | Small pill badge for case/action status: `open`, `in_progress`, `closed`, `executed`, `escalated`, `blocked`. Each status has a semantic colour and explicit text. |
| `Skeleton.tsx` | Loading skeleton components: `Skeleton` (single bar, animated shimmer), `MetricSkeleton` (card-shaped), `TableRowSkeleton` (multi-column). Used during data loading states. |
| `StateViews.tsx` | Three shared state components: `LoadingPanel` (spinner + configurable title/detail text), `ErrorPanel` (critical-red icon + message + optional Retry button), `Eyebrow` (uppercase monospace section label with optional tone colour). |
| `EmptyState.tsx` | Empty state display with icon + title + description. Used in Risk Queue when no cases exist and LiveActivity when no events are present. |

### `frontend/lib/` - Utilities and Types

#### `lib/types/index.ts`
All TypeScript types shared across the frontend, mirroring backend API response shapes:
`EvaluationRunResult`, `PolicyEvaluationResult`, `HeroCase`, `Customer`, `Subscription`, `Payment`, `AuditEvent`, `RiskPrediction`, `RiskSignal`, `RecoveryDiagnosis`, `ActionRanking`, `PolicyDecision`, `ExecutionResult`, `LoadingState` (`"loading" | "success" | "error"`).

#### `lib/api/`

| File | Purpose |
|---|---|
| `client.ts` | `ApiError` class (captures status + body). `api.get(path)` and `api.post(path, body)` - both call `/api/*` (the Next.js proxy) and throw `ApiError` on non-2xx responses. No direct `BACKEND_URL` references. |
| `evaluation.ts` | `evaluationApi`: `runEvaluation(seed, cohortSize)`, `getRun(runId)`, `runMultiSeed(seeds, cohortSize)`. Wraps the evaluation endpoints. |
| `demo.ts` | `demoApi`: `getHeroCase()`, `runSimulation()`. Wraps the demo endpoints for the hero case and webhook simulation. |
| `cases.ts` | `casesApi`: `listCases(page?)`, `getCase(caseId)`. Wraps the cases endpoints. Uses `/api/cases` (not `/api/cases/`) to match the explicit Next.js rewrite rule. |

#### `lib/utils/format.ts`
Formatting utilities used throughout the frontend:

| Function | Purpose |
|---|---|
| `formatINR(value)` | Formats numbers as Indian Rupees. Values ≥ 10L display as `₹X.XXL`, ≥ 1Cr as `₹X.XXCr`. Uses tabular numeral formatting. |
| `formatPct(value)` | Formats 0.0–1.0 as a percentage string (e.g. `"64.3%"`). |
| `formatPP(value)` | Formats a percentage-point delta with sign (e.g. `"+6.2pp"`, `"-1.4pp"`). |
| `formatCount(value)` | Locale-aware integer formatting using `en-IN` locale. |
| `formatCause(cause)` | Human-readable cause label (`"billing_migration"` → `"Billing Migration"`). |
| `formatAction(action)` | Human-readable action label (`"smart_link"` → `"Smart Payment Link"`). |
| `formatDateTime(iso)` | Short date + time string from ISO timestamp. |
| `formatTime(iso)` | Time-only string (`HH:MM:SS`) from ISO timestamp. |
| `riskTone(score)` | Returns Tailwind tone string (`"recovery"`, `"warning"`, `"critical"`) based on score thresholds (0.30, 0.70). |
| `riskTextClass(score)` | Returns Tailwind text class for the risk score colour. |
| `riskBarClass(score)` | Returns Tailwind background class for risk bar colour. |

---

## Key Isolation Boundaries (enforced across files)

| Boundary | Files that enforce it |
|---|---|
| Simulator hidden state never reaches agent | `simulator/world.py`, `simulator/persistence.py`, `risk/features.py`, `agent/state.py` |
| Potential outcomes only to evaluator | `evaluation/evaluator.py` (`EvaluationWorld` wrapper), `evaluation/policies.py` (policies get `ObservableCustomerData` only) |
| BACKEND_URL server-side only | `next.config.mjs` (rewrites), `lib/api/client.ts` (calls `/api/*` only) |
| Policy Guard non-bypassable | `agent/nodes.py` (`make_policy_check` always called before `make_execute_action`) |
| No hardcoded business metrics | `evaluation/metrics.py` (all fields computed), `app/dashboard/page.tsx` (all values from API) |
| Idempotency enforced | `actions/service.py` (checks DB before write), `policy/guard.py` (rule 5) |
| All thresholds configuration-driven | `core/config.py` (single source), `policy/guard.py` (reads `Settings`) |
