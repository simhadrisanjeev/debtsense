"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { AxiosError } from "axios";
import type { Income, IncomeCreate } from "@/types";

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

// ─── useIncome ──────────────────────────────────────────────────────────────

export function useIncome() {
  const [incomes, setIncomes] = useState<Income[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncomes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<Income[]>("/income/");
      setIncomes(data);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const addIncome = useCallback(async (payload: IncomeCreate) => {
    setError(null);
    try {
      const { data } = await api.post<Income>("/income/", payload);
      setIncomes((prev) => [data, ...prev]);
      return data;
    } catch (err: unknown) {
      const message = extractErrorMessage(err);
      setError(message);
      throw new Error(message);
    }
  }, []);

  const updateIncome = useCallback(async (id: string, payload: Partial<IncomeCreate>) => {
    setError(null);
    try {
      const { data } = await api.patch<Income>(`/income/${id}`, payload);
      setIncomes((prev) => prev.map((i) => (i.id === id ? data : i)));
      return data;
    } catch (err: unknown) {
      const message = extractErrorMessage(err);
      setError(message);
      throw new Error(message);
    }
  }, []);

  const removeIncome = useCallback(async (id: string) => {
    setError(null);
    try {
      await api.delete(`/income/${id}`);
      setIncomes((prev) => prev.filter((i) => i.id !== id));
    } catch (err: unknown) {
      const message = extractErrorMessage(err);
      setError(message);
      throw new Error(message);
    }
  }, []);

  useEffect(() => {
    fetchIncomes();
  }, [fetchIncomes]);

  return { incomes, loading, error, fetchIncomes, addIncome, updateIncome, removeIncome };
}
