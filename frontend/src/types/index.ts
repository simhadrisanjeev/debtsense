// ─── User ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
  updated_at: string;
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

// ─── Debt ────────────────────────────────────────────────────────────────────

export interface Debt {
  id: string;
  user_id: string;
  name: string;
  debt_type: string;
  lender_name: string | null;
  principal_amount: string;
  current_balance: string;
  interest_rate: string;
  interest_type: string;
  repayment_style: string;
  payment_frequency: string;
  minimum_payment: string;
  due_day_of_month: number;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface DebtCreate {
  name: string;
  debt_type: string;
  lender_name?: string | null;
  principal_amount: string;
  current_balance: string;
  interest_rate: string;
  interest_type?: string;
  repayment_style?: string;
  payment_frequency?: string;
  minimum_payment: string;
  due_day_of_month?: number;
  start_date?: string;
  end_date?: string | null;
  is_active?: boolean;
  notes?: string | null;
}

export interface DebtUpdate extends Partial<DebtCreate> {}

// ─── Income ──────────────────────────────────────────────────────────────────

export type IncomeTypeValue =
  | "salary"
  | "freelance"
  | "business"
  | "bonus"
  | "gift"
  | "investment"
  | "other";

export type IncomeAllocationTypeValue = "same_month" | "next_month";

export interface Income {
  id: string;
  user_id: string;
  income_type: IncomeTypeValue;
  amount: number;
  date_received: string;
  allocation_month: string;
  income_allocation_type: IncomeAllocationTypeValue;
  is_recurring: boolean;
  recurring_day: number | null;
  is_active: boolean;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncomeCreate {
  income_type: IncomeTypeValue;
  amount: number;
  date_received: string;
  income_allocation_type?: IncomeAllocationTypeValue;
  is_recurring?: boolean;
  recurring_day?: number | null;
  note?: string | null;
}

export interface IncomeUpdate extends Partial<IncomeCreate> {}

export interface IncomeByTypeBreakdown {
  income_type: string;
  total: number;
  count: number;
}

export interface IncomeSummary {
  user_id: string;
  month: string;
  monthly_total: number;
  entry_count: number;
  breakdown: IncomeByTypeBreakdown[];
}

// ─── Expense ─────────────────────────────────────────────────────────────────

export interface Expense {
  id: string;
  user_id: string;
  category: string;
  description: string;
  amount: number;
  frequency: "weekly" | "biweekly" | "monthly" | "annually" | "one-time";
  is_recurring: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExpenseCreate {
  category: string;
  description: string;
  amount: number;
  frequency: "weekly" | "biweekly" | "monthly" | "annually" | "one-time";
  is_recurring?: boolean;
}

// ─── Financial Engine ────────────────────────────────────────────────────────

export interface DebtInput {
  name: string;
  balance: string;
  interest_rate: string;
  minimum_payment: string;
}

export type PayoffStrategy = "avalanche" | "snowball" | "hybrid" | "custom";

export interface PayoffScheduleEntry {
  month: number;
  debt_name: string;
  payment: string;
  principal: string;
  interest: string;
  remaining_balance: string;
}

export interface PayoffResult {
  strategy: string;
  total_months: number;
  total_interest_paid: string;
  total_paid: string;
  payoff_order: string[];
  schedule: PayoffScheduleEntry[];
  debt_free_date: string;
}

export interface StrategyComparison {
  strategies: PayoffResult[];
  recommended: string;
  interest_savings_vs_minimum: string;
}

// ─── Simulation Engine ──────────────────────────────────────────────────────

export interface ScenarioInput {
  scenario_type: "extra_payment" | "rate_change" | "new_debt" | "income_change" | "lump_sum";
  parameters: Record<string, unknown>;
}

export interface SimulationRequest {
  base_debts: DebtInput[];
  base_extra_payment?: string;
  scenarios: ScenarioInput[];
}

export interface SimulationResult {
  scenario_type: string;
  description: string;
  original_payoff_months: number;
  new_payoff_months: number;
  original_total_interest: string;
  new_total_interest: string;
  monthly_savings: string;
  total_savings: string;
}

export interface SimulationResponse {
  results: SimulationResult[];
  generated_at: string;
}

// ─── AI Advisor ──────────────────────────────────────────────────────────────

export interface AdvisorContext {
  total_debt: string;
  total_income: string;
  total_expenses: string;
  debt_count: number;
  highest_rate_debt: string;
  debt_to_income_ratio: string;
}

export interface AdvisorRequest {
  question: string;
  context?: AdvisorContext | null;
  conversation_history?: Array<{ role: string; content: string }>;
}

export interface AdvisorResponse {
  advice: string;
  suggestions: string[];
  risk_level: string;
  disclaimer: string;
}

export interface QuickTip {
  tip: string;
  category: string;
  priority: number;
}

export interface QuickTipsResponse {
  tips: QuickTip[];
}

// ─── Notifications ───────────────────────────────────────────────────────────

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  body: string;
  notification_type: string;
  channel: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  unread_count: number;
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_debt: string;
  total_income: string;
  total_expenses: string;
  debt_count: number;
  monthly_payment: string;
  estimated_payoff_date: string | null;
  debt_free_progress_pct: string;
}

// ─── Pagination ──────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ─── API Error ───────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status_code: number;
}
