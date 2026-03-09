"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { AxiosError } from "axios";

// ─── Types ───────────────────────────────────────────────────────────────────

interface DashboardStatsResponse {
  total_debt: string;
  total_income: string;
  total_expenses: string;
  debt_count: number;
  monthly_payment: string;
  estimated_payoff_date: string | null;
  debt_free_progress_pct: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  if (err instanceof AxiosError) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((d: { msg?: string }) => d.msg ?? String(d)).join("; ");
    }
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "An unexpected error occurred";
}

// ─── useDashboard ────────────────────────────────────────────────────────────

export function useDashboard() {
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<DashboardStatsResponse>("/analytics/dashboard");
      setStats(data);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
}
