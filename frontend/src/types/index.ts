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
  category: string;
  current_balance: number;
  interest_rate: number;
  minimum_payment: number;
  due_date: number;
  start_balance: number;
  start_date: string;
  lender: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DebtCreate {
  name: string;
  category: string;
  current_balance: number;
  interest_rate: number;
  minimum_payment: number;
  due_date?: number;
  start_balance?: number;
  start_date?: string;
  lender?: string;
  notes?: string;
}

export interface DebtUpdate extends Partial<DebtCreate> {}

// ─── Income ──────────────────────────────────────────────────────────────────

export interface Income {
  id: string;
  user_id: string;
  source: string;
  amount: number;
  frequency: "weekly" | "biweekly" | "monthly" | "annually";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface IncomeCreate {
  source: string;
  amount: number;
  frequency: "weekly" | "biweekly" | "monthly" | "annually";
}

// ─── Expense ─────────────────────────────────────────────────────────────────

export interface Expense {
  id: string;
  user_id: string;
  category: string;
  description: string;
  amount: number;
  frequency: "weekly" | "biweekly" | "monthly" | "annually" | "one-time";
  is_essential: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExpenseCreate {
  category: string;
  description: string;
  amount: number;
  frequency: "weekly" | "biweekly" | "monthly" | "annually" | "one-time";
  is_essential?: boolean;
}

// ─── Financial Engine ────────────────────────────────────────────────────────

export type PayoffStrategy = "avalanche" | "snowball" | "hybrid";

export interface PayoffResult {
  strategy: PayoffStrategy;
  total_months: number;
  total_interest_paid: number;
  total_amount_paid: number;
  monthly_schedule: MonthlyScheduleEntry[];
  debt_free_date: string;
}

export interface MonthlyScheduleEntry {
  month: number;
  date: string;
  payments: DebtPayment[];
  total_payment: number;
  remaining_balance: number;
}

export interface DebtPayment {
  debt_id: string;
  debt_name: string;
  payment_amount: number;
  principal: number;
  interest: number;
  remaining_balance: number;
}

export interface StrategyComparison {
  strategies: PayoffResult[];
  recommended: PayoffStrategy;
  savings_vs_minimum: number;
  fastest_strategy: PayoffStrategy;
  cheapest_strategy: PayoffStrategy;
}

export interface SimulationParams {
  extra_payment?: number;
  income_change?: number;
  expense_change?: number;
  new_debt?: DebtCreate;
  removed_debt_id?: string;
}

export interface SimulationResult {
  baseline: PayoffResult;
  simulated: PayoffResult;
  months_difference: number;
  interest_difference: number;
  total_saved: number;
}

// ─── AI Advisor ──────────────────────────────────────────────────────────────

export interface AdvisorRequest {
  question?: string;
  context?: string;
}

export interface AdvisorResponse {
  advice: string;
  recommendations: Recommendation[];
  confidence: number;
  sources: string[];
}

export interface Recommendation {
  title: string;
  description: string;
  impact: "high" | "medium" | "low";
  category: string;
}

// ─── Notifications ───────────────────────────────────────────────────────────

export interface Notification {
  id: string;
  user_id: string;
  type: "info" | "warning" | "success" | "achievement";
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_debt: number;
  total_monthly_payment: number;
  total_interest_saved: number;
  debt_free_date: string;
  debts_count: number;
  active_debts_count: number;
  total_income: number;
  total_expenses: number;
  disposable_income: number;
  payoff_progress_percent: number;
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
