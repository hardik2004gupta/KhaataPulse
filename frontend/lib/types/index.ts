// KhaataPulse — TypeScript type definitions
// Matches backend API contracts exactly. No business logic duplicated here.

// ── Evaluation ─────────────────────────────────────────────────────────────

export interface PolicyEvaluationResult {
  policy_name: string;
  policy_version: string;
  recovered_amount: string;           // Decimal as string
  total_at_risk_amount: string;       // Decimal as string
  recovery_rate: number;              // [0.0, 1.0]
  incremental_recovery: string | null; // vs smart_retry
  contacts_sent: number;
  contacts_avoided: number;
  human_escalations: number;
  false_positives: number;
  policy_blocks: number;
  cases_evaluated: number;
  llm_fallback_count: number;
}

export interface EvaluationRunResult {
  run_id: string;
  seed: number;
  cohort_size: number;
  simulator_version: string;
  model_version: string;
  policy_version: string;
  incremental_recovery: string;       // primary KPI
  static_dunning: PolicyEvaluationResult;
  smart_retry: PolicyEvaluationResult;
  khaatapulse: PolicyEvaluationResult;
}

export interface EvaluationRunResponse {
  run_id: string;
  status: "completed" | "running" | "failed";
  results: EvaluationRunResult;
}

export interface EvaluationRunRecord {
  run_id: string;
  seed: number;
  cohort_size: number;
  status: string;
  simulator_version: string;
  model_version: string;
  created_at: string | null;
  completed_at: string | null;
}

export interface MultiSeedSummaryEntry {
  seed: number;
  run_id: string;
  incremental_recovery: string;
  khaatapulse_recovered: string;
  smart_retry_recovered: string;
  is_positive: boolean;
}

export interface MultiSeedSummary {
  total_runs: number;
  positive_runs: number;
  negative_runs: number;
  seeds: MultiSeedSummaryEntry[];
}

export interface MultiSeedResponse {
  runs: EvaluationRunResult[];
  summary: MultiSeedSummary;
}

// ── Risk ──────────────────────────────────────────────────────────────────

export interface RiskSignal {
  feature: string;
  impact: number;
}

export interface RiskInfo {
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  model_version: string;
  top_signals: RiskSignal[];
}

// ── Diagnosis ─────────────────────────────────────────────────────────────

export type Cause =
  | "billing_migration"
  | "temporary_cash_flow"
  | "card_expired"
  | "price_friction"
  | "churn_intent";

export type ProposedAction =
  | "silent_retry"
  | "smart_link"
  | "grace_period"
  | "human_escalation"
  | "suppress";

export interface DiagnosisInfo {
  cause: Cause;
  confidence: number;
  rationale: string;
  proposed_action: ProposedAction;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
}

// ── Action Ranking ─────────────────────────────────────────────────────────

export interface ActionRanking {
  rank: number;
  action_type: string;
  enr: string;                      // Decimal as string
  estimated_p_payment: number;
  estimated_p_churn: number;
  action_cost: string;              // Decimal as string
}

// ── Policy Decision ────────────────────────────────────────────────────────

export type PolicyStatus = "APPROVED" | "BLOCKED" | "ESCALATED";

export interface PolicyDecision {
  status: PolicyStatus;
  action_type: string;
  checks: Record<string, boolean>;
  block_reason: string | null;
}

// ── Recovery Cases ─────────────────────────────────────────────────────────

export interface RecoveryCase {
  id: number;
  customer_id: number;
  customer_name: string | null;
  customer_segment: string | null;
  subscription_plan: string | null;
  subscription_amount: string | null;
  currency: string;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  diagnosis: string | null;
  diagnosis_confidence: number | null;
  proposed_action: string | null;
  selected_action: string | null;
  policy_status: string | null;
  outcome_status: string | null;
  created_at: string | null;
  closed_at: string | null;
}

export interface CasesListResponse {
  cases: RecoveryCase[];
  total: number;
  limit: number;
  offset: number;
}

// ── Audit Events ───────────────────────────────────────────────────────────

export interface AuditEvent {
  id?: number;
  event_type: string;
  actor: string;
  payload: Record<string, unknown>;
  timestamp: string;
  idempotency_key?: string | null;
}

// ── Demo / Hero Case ────────────────────────────────────────────────────────

export interface CustomerInfo {
  id: number;
  name: string;
  segment: string;
  ltv: string;
}

export interface SubscriptionInfo {
  plan: string;
  amount: string;
  currency: string;
  renewal_at: string;
  status: string;
}

export interface PaymentInfo {
  status: string;
  failure_code: string | null;
  payment_method: string;
  amount: string;
  created_at: string;
}

export interface ObservableEvent {
  event_type: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface ExecutionInfo {
  action_type: string;
  status: string;
  idempotency_key: string;
}

export interface HeroCase {
  customer: CustomerInfo;
  subscription: SubscriptionInfo;
  payments: PaymentInfo[];
  observable_events: ObservableEvent[];
  risk: RiskInfo;
  diagnosis: DiagnosisInfo;
  action_rankings: ActionRanking[];
  policy_decision: PolicyDecision;
  execution: ExecutionInfo;
  audit_events: AuditEvent[];
}

// ── Live Simulation ────────────────────────────────────────────────────────

export interface SimulationStep {
  step: string;
  label: string;
  description: string;
  actor: string;
  data: Record<string, unknown>;
}

export interface SimulationResponse {
  customer: CustomerInfo;
  subscription: SubscriptionInfo;
  steps: SimulationStep[];
}

// ── UI utility types ───────────────────────────────────────────────────────

export type LoadingState = "idle" | "loading" | "success" | "error";
