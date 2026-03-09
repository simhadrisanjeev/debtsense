import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { getToken, clearAuth, getRefreshToken, setToken } from "@/lib/auth";
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Debt,
  DebtCreate,
  DebtUpdate,
  DebtInput,
  Income,
  IncomeCreate,
  IncomeSummary,
  Expense,
  ExpenseCreate,
  StrategyComparison,
  SimulationRequest,
  SimulationResponse,
  SimulationResult,
  PayoffResult,
  PayoffStrategy,
  AdvisorRequest,
  AdvisorResponse,
  AdvisorContext,
  QuickTipsResponse,
  DashboardStats,
  NotificationListResponse,
} from "@/types";

// ─── Axios Instance ──────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

// ─── Request Interceptor ────────────────────────────────────────────────────

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

// ─── Response Interceptor ───────────────────────────────────────────────────

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // If 401 and we haven't already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearAuth();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post<{ access_token: string }>(
          `${api.defaults.baseURL}/auth/refresh`,
          { refresh_token: refreshToken },
        );
        setToken(data.access_token);
        processQueue(null, data.access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearAuth();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

// ─── Auth API ───────────────────────────────────────────────────────────────

export const authApi = {
  login(data: LoginRequest) {
    return api.post<AuthResponse>("/auth/login", data);
  },

  register(data: RegisterRequest) {
    return api.post<AuthResponse>("/auth/register", data);
  },

  refresh(refreshToken: string) {
    return api.post<{ access_token: string }>("/auth/refresh", {
      refresh_token: refreshToken,
    });
  },

  me() {
    return api.get<User>("/auth/me");
  },

  logout(refreshToken: string) {
    return api.post("/auth/logout", { refresh_token: refreshToken });
  },
};

// ─── Debts API ──────────────────────────────────────────────────────────────

export const debtsApi = {
  list(params?: { page?: number; page_size?: number }) {
    return api.get<Debt[]>("/debts/", { params });
  },

  get(id: string) {
    return api.get<Debt>(`/debts/${id}`);
  },

  create(data: DebtCreate) {
    return api.post<Debt>("/debts/", data);
  },

  update(id: string, data: DebtUpdate) {
    return api.patch<Debt>(`/debts/${id}`, data);
  },

  delete(id: string) {
    return api.delete(`/debts/${id}`);
  },
};

// ─── Income API ─────────────────────────────────────────────────────────────

export const incomeApi = {
  list() {
    return api.get<Income[]>("/income/");
  },

  listByMonth(month: string) {
    return api.get<Income[]>(`/income/month/${month}`);
  },

  get(id: string) {
    return api.get<Income>(`/income/${id}`);
  },

  create(data: IncomeCreate) {
    return api.post<Income>("/income/", data);
  },

  update(id: string, data: Partial<IncomeCreate>) {
    return api.patch<Income>(`/income/${id}`, data);
  },

  delete(id: string) {
    return api.delete(`/income/${id}`);
  },

  getSummary(month?: string) {
    const params = month ? { month } : {};
    return api.get<IncomeSummary>("/analytics/income-summary", { params });
  },
};

// ─── Expenses API ───────────────────────────────────────────────────────────

export const expensesApi = {
  list() {
    return api.get<Expense[]>("/expenses");
  },

  get(id: string) {
    return api.get<Expense>(`/expenses/${id}`);
  },

  create(data: ExpenseCreate) {
    return api.post<Expense>("/expenses", data);
  },

  update(id: string, data: Partial<ExpenseCreate>) {
    return api.put<Expense>(`/expenses/${id}`, data);
  },

  delete(id: string) {
    return api.delete(`/expenses/${id}`);
  },
};

// ─── Financial Engine API ───────────────────────────────────────────────────

export const engineApi = {
  calculatePayoff(data: { debts: DebtInput[]; strategy: PayoffStrategy; extra_payment?: string }) {
    return api.post<PayoffResult>("/financial-engine/calculate", data);
  },

  compareStrategies(data: { debts: DebtInput[]; extra_payment?: string }) {
    return api.post<StrategyComparison>("/financial-engine/compare", data);
  },

  simulate(data: SimulationRequest) {
    return api.post<SimulationResult>("/simulations/run", data);
  },

  simulateBatch(data: SimulationRequest) {
    return api.post<SimulationResponse>("/simulations/batch", data);
  },
};

// ─── AI Advisor API ─────────────────────────────────────────────────────────

export const advisorApi = {
  getAdvice(data: AdvisorRequest) {
    return api.post<AdvisorResponse>("/ai-advisor/ask", data);
  },

  getQuickTips(data: AdvisorContext) {
    return api.post<QuickTipsResponse>("/ai-advisor/quick-tips", data);
  },
};

// ─── Dashboard API ──────────────────────────────────────────────────────────

export const dashboardApi = {
  getStats() {
    return api.get<DashboardStats>("/analytics/dashboard");
  },
};

// ─── Notifications API ─────────────────────────────────────────────────────

export const notificationsApi = {
  list(params?: { offset?: number; limit?: number; is_read?: boolean | null }) {
    return api.get<NotificationListResponse>("/notifications/", { params });
  },

  getUnreadCount() {
    return api.get<{ unread_count: number }>("/notifications/unread-count");
  },

  markRead(notificationIds: string[]) {
    return api.patch<{ updated_count: number }>("/notifications/mark-read", {
      notification_ids: notificationIds,
    });
  },

  delete(id: string) {
    return api.delete(`/notifications/${id}`);
  },
};

export default api;
