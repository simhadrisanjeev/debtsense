"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { AxiosError } from "axios";

// ─── Types ───────────────────────────────────────────────────────────────────

interface DebtInputItem {
  name: string;
  balance: string;
  interest_rate: string;
  minimum_payment: string;
}

interface PayoffResultItem {
  strategy: string;
  total_months: number;
  total_interest_paid: string;
  total_paid: string;
  payoff_order: string[];
  debt_free_date: string;
}

interface StrategyComparisonResponse {
  strategies: PayoffResultItem[];
  recommended: string;
  interest_savings_vs_minimum: string;
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

// ─── useStrategies ───────────────────────────────────────────────────────────

export function useStrategies(debts: DebtInputItem[], extraPayment: string = "0") {
  const [comparison, setComparison] = useState<StrategyComparisonResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const debtsKey = JSON.stringify(debts);

  const fetchComparison = useCallback(async () => {
    const parsed = JSON.parse(debtsKey) as DebtInputItem[];
    if (parsed.length === 0) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<StrategyComparisonResponse>(
        "/financial-engine/compare",
        { debts: parsed, extra_payment: extraPayment },
      );
      setComparison(data);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [debtsKey, extraPayment]);

  useEffect(() => {
    fetchComparison();
  }, [fetchComparison]);

  return { comparison, loading, error, refetch: fetchComparison };
}
