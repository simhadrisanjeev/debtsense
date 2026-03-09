"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { AxiosError } from "axios";

// ─── Types ───────────────────────────────────────────────────────────────────

interface DebtResponse {
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

interface PaymentOverrideResponse {
  id: string;
  debt_id: string;
  user_id: string;
  month_year: string;
  custom_payment_amount: string;
  note: string | null;
  created_at: string;
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

// ─── useDebts ────────────────────────────────────────────────────────────────

export function useDebts() {
  const [debts, setDebts] = useState<DebtResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDebts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<DebtResponse[]>("/debts/");
      setDebts(data);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const addDebt = useCallback(
    async (payload: Omit<DebtResponse, "id" | "user_id" | "created_at" | "updated_at">) => {
      setError(null);
      try {
        const { data } = await api.post<DebtResponse>("/debts/", payload);
        setDebts((prev) => [...prev, data]);
        return data;
      } catch (err: unknown) {
        const message = extractErrorMessage(err);
        setError(message);
        throw new Error(message);
      }
    },
    [],
  );

  const removeDebt = useCallback(async (id: string) => {
    setError(null);
    try {
      await api.delete(`/debts/${id}`);
      setDebts((prev) => prev.filter((d) => d.id !== id));
    } catch (err: unknown) {
      const message = extractErrorMessage(err);
      setError(message);
      throw new Error(message);
    }
  }, []);

  useEffect(() => {
    fetchDebts();
  }, [fetchDebts]);

  return { debts, loading, error, fetchDebts, addDebt, removeDebt };
}

// ─── useDebtOverrides ────────────────────────────────────────────────────────

export function useDebtOverrides(debtId: string) {
  const [overrides, setOverrides] = useState<PaymentOverrideResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverrides = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<PaymentOverrideResponse[]>(
        `/debts/${debtId}/payment-overrides`,
      );
      setOverrides(data);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [debtId]);

  const addOverride = useCallback(
    async (payload: Omit<PaymentOverrideResponse, "id" | "debt_id" | "user_id" | "created_at">) => {
      setError(null);
      try {
        const { data } = await api.post<PaymentOverrideResponse>(
          `/debts/${debtId}/payment-overrides`,
          payload,
        );
        setOverrides((prev) => [...prev, data]);
        return data;
      } catch (err: unknown) {
        const message = extractErrorMessage(err);
        setError(message);
        throw new Error(message);
      }
    },
    [debtId],
  );

  const removeOverride = useCallback(
    async (overrideId: string) => {
      setError(null);
      try {
        await api.delete(`/debts/payment-overrides/${overrideId}`);
        setOverrides((prev) => prev.filter((o) => o.id !== overrideId));
      } catch (err: unknown) {
        const message = extractErrorMessage(err);
        setError(message);
        throw new Error(message);
      }
    },
    [],
  );

  useEffect(() => {
    fetchOverrides();
  }, [fetchOverrides]);

  return { overrides, loading, error, fetchOverrides, addOverride, removeOverride };
}
