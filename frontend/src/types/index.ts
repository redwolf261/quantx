// ── Auth ──────────────────────────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  full_name: string;
  role: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "customer" | "rm" | "admin";
  is_active: boolean;
  created_at: string;
}

// ── Financial Profile ─────────────────────────────────────────────────────────
export type RiskProfile = "conservative" | "moderate" | "aggressive";

export interface FinancialProfile {
  id: string;
  user_id: string;
  age: number;
  occupation: string;
  city: string;
  city_tier: number;
  monthly_income: number;
  salary_growth_rate: number;
  monthly_expenses: number;
  inflation_rate: number;
  total_savings: number;
  total_investments: number;
  equity_allocation: number;
  debt_allocation: number;
  total_loans: number;
  monthly_emi: number;
  risk_profile: RiskProfile;
  health_score: number | null;
  created_at: string;
  updated_at: string;
}

export type ProfileCreate = Omit<FinancialProfile, "id" | "user_id" | "health_score" | "created_at" | "updated_at">;

// ── Goals ─────────────────────────────────────────────────────────────────────
export type GoalType = "retirement" | "home_purchase" | "education" | "emergency_fund" | "other";
export type GoalStatus = "active" | "achieved" | "paused" | "cancelled";

export interface Goal {
  id: string;
  user_id: string;
  goal_name: string;
  goal_type: GoalType;
  target_amount: number;
  target_year: number;
  priority: number;
  importance_score: number;
  required_monthly_sip: number | null;
  current_success_probability: number | null;
  status: GoalStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type GoalCreate = Omit<Goal, "id" | "user_id" | "required_monthly_sip" | "current_success_probability" | "status" | "created_at" | "updated_at">;

// ── Simulation ────────────────────────────────────────────────────────────────
export interface PercentileBand {
  year: number;
  p10: number;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
}

export interface HistogramBucket {
  bucket_start: number;
  bucket_end: number;
  count: number;
}

export interface SimulationResult {
  simulation_id: string;
  goal_id: string | null;
  horizon_years: number;
  num_simulations: number;
  success_probability: number;
  failure_probability: number;
  median_corpus: number;
  p10_corpus: number;
  p25_corpus: number;
  p75_corpus: number;
  p90_corpus: number;
  required_monthly_sip: number;
  current_monthly_sip: number;
  percentile_bands: PercentileBand[];
  histogram_data: HistogramBucket[];
  parameters: Record<string, unknown>;
}

export interface SimulationRequest {
  goal_id?: string;
  horizon_years: number;
  monthly_sip: number;
  initial_wealth?: number;
  target_amount?: number;
  num_simulations?: number;
}

// ── Stress Test ───────────────────────────────────────────────────────────────
export type ScenarioType = "market_crash" | "inflation_spike" | "salary_loss" | "medical_emergency";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface ScenarioResult {
  scenario: string;
  scenario_label: string;
  base_success_probability: number;
  stressed_success_probability: number;
  probability_impact: number;
  base_median_corpus: number;
  stressed_median_corpus: number;
  corpus_impact_pct: number;
  risk_level: RiskLevel;
  percentile_bands: PercentileBand[];
}

export interface StressTestResult {
  goal_id: string | null;
  horizon_years: number;
  base_result: SimulationResult;
  scenarios: ScenarioResult[];
}

export interface StressTestRequest {
  goal_id?: string;
  horizon_years: number;
  monthly_sip: number;
  scenarios?: ScenarioType[];
}

// ── Optimization ──────────────────────────────────────────────────────────────
export interface OptimizationResult {
  goal_id: string | null;
  current_probability: number;
  optimized_probability: number;
  improvement: number;
  current_sip: number;
  recommended_sip: number;
  sip_increase: number;
  recommended_savings_rate: number;
  recommended_retirement_age: number | null;
  optimization_path: Array<{ sip: number; probability: number }>;
  parameters: Record<string, unknown>;
}

export interface OptimizationRequest {
  goal_id?: string;
  horizon_years: number;
  target_probability?: number;
  min_sip?: number;
  max_sip?: number;
  min_retirement_age?: number;
  max_retirement_age?: number;
}

// ── Explain ───────────────────────────────────────────────────────────────────
export interface ExplainResponse {
  explanation: string;
  key_insights: string[];
  action_items: string[];
  model_used: string;
  is_fallback: boolean;
}

export interface ExplainRequest {
  context_type: "simulation" | "stress_test" | "optimization" | "goal_status" | "portfolio";
  structured_data: Record<string, unknown>;
  goal_name?: string;
  user_name?: string;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export interface GoalsSummary {
  total: number;
  avg_success_probability: number;
  on_track: number;
}

export interface DashboardData {
  user: User;
  profile: FinancialProfile | null;
  goals: Goal[];
  net_worth: number;
  monthly_surplus: number;
  health_score: number;
  goals_summary: GoalsSummary;
  latest_simulation: SimulationResult | null;
  recommendations_count: number;
}

// ── RM Customer Summary ───────────────────────────────────────────────────────
export interface CustomerSummary {
  user: User;
  profile: FinancialProfile | null;
  health_score: number;
  net_worth: number;
  goals_count: number;
  avg_success_probability: number;
  risk_level: RiskLevel;
  discussion_points: string[];
  last_active: string | null;
}

// ── Utility types ─────────────────────────────────────────────────────────────
export interface ApiError {
  detail: string;
  status?: number;
}

export type LoadingState = "idle" | "loading" | "success" | "error";
