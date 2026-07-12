/**
 * FutureLens API Client
 * Axios instance with JWT interceptors and typed methods.
 */
import axios, { AxiosInstance, AxiosError } from "axios";
import type {
  TokenResponse,
  FinancialProfile,
  ProfileCreate,
  Goal,
  GoalCreate,
  SimulationRequest,
  SimulationResult,
  StressTestRequest,
  StressTestResult,
  OptimizationRequest,
  OptimizationResult,
  ExplainRequest,
  ExplainResponse,
  DashboardData,
  CustomerSummary,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 60000, // 60s for long simulations
});

// ── Request interceptor: attach JWT ─────────────────────────────────────────
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("fl_token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return config;
});

// ── Response interceptor: handle 401 ────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("fl_token");
      localStorage.removeItem("fl_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role?: string }) =>
    api.post<TokenResponse>("/auth/register", data).then((r) => r.data),

  login: (email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { email, password }).then((r) => r.data),
};

// ── Profile ───────────────────────────────────────────────────────────────────
export const profileApi = {
  create: (data: ProfileCreate) =>
    api.post<FinancialProfile>("/profile/create", data).then((r) => r.data),

  get: (userId: string) =>
    api.get<FinancialProfile>(`/profile/${userId}`).then((r) => r.data),

  update: (data: ProfileCreate) =>
    api.put<FinancialProfile>("/profile/update", data).then((r) => r.data),
};

// ── Goals ─────────────────────────────────────────────────────────────────────
export const goalsApi = {
  create: (data: GoalCreate) =>
    api.post<Goal>("/goals/create", data).then((r) => r.data),

  list: (userId: string) =>
    api.get<Goal[]>(`/goals/${userId}`).then((r) => r.data),

  delete: (goalId: string) =>
    api.delete(`/goals/${goalId}`),
};

// ── Simulation ────────────────────────────────────────────────────────────────
export const simulationApi = {
  run: (data: SimulationRequest) =>
    api.post<SimulationResult>("/simulation/run", data).then((r) => r.data),
};

// ── Stress Test ───────────────────────────────────────────────────────────────
export const stressTestApi = {
  run: (data: StressTestRequest) =>
    api.post<StressTestResult>("/stress-test/run", data).then((r) => r.data),
};

// ── Optimization ──────────────────────────────────────────────────────────────
export const optimizationApi = {
  run: (data: OptimizationRequest) =>
    api.post<OptimizationResult>("/optimization/run", data).then((r) => r.data),
};

// ── Explain ───────────────────────────────────────────────────────────────────
export const explainApi = {
  explain: (data: ExplainRequest) =>
    api.post<ExplainResponse>("/explain", data).then((r) => r.data),
};

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const dashboardApi = {
  get: (userId: string) =>
    api.get<DashboardData>(`/dashboard/${userId}`).then((r) => r.data),

  getRmCustomers: (skip = 0, limit = 50) =>
    api.get<CustomerSummary[]>(`/dashboard/rm/customers?skip=${skip}&limit=${limit}`).then((r) => r.data),
};

// ── Utilities ─────────────────────────────────────────────────────────────────
export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || error.message || "An error occurred";
  }
  return String(error);
}

export default api;
