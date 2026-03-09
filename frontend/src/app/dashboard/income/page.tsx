"use client";

import { useState } from "react";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useIncome } from "@/hooks/useIncome";
import { formatCurrency } from "@/lib/utils";
import type { Income, IncomeTypeValue, IncomeAllocationTypeValue } from "@/types";
import {
  Plus,
  X,
  DollarSign,
  Briefcase,
  Laptop,
  TrendingUp,
  Hash,
  Trash2,
  Wallet,
  Gift,
  Building2,
  Award,
  CalendarDays,
  Repeat,
} from "lucide-react";

// ─── Constants ────────────────────────────────────────────────────────────────

const INCOME_TYPE_OPTIONS: { value: IncomeTypeValue; label: string }[] = [
  { value: "salary", label: "Salary" },
  { value: "freelance", label: "Freelance" },
  { value: "business", label: "Business" },
  { value: "bonus", label: "Bonus" },
  { value: "gift", label: "Gift" },
  { value: "investment", label: "Investment" },
  { value: "other", label: "Other" },
];

const ALLOCATION_TYPE_OPTIONS: {
  value: IncomeAllocationTypeValue;
  label: string;
  description: string;
}[] = [
  {
    value: "same_month",
    label: "Same Month",
    description: "Allocated to the month it was received",
  },
  {
    value: "next_month",
    label: "Next Month",
    description: "Allocated to the following month (e.g. salary on Mar 31 → April budget)",
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getTypeLabel(type: string): string {
  return INCOME_TYPE_OPTIONS.find((o) => o.value === type)?.label ?? type;
}

function getTypeIcon(type: string): React.ElementType {
  switch (type) {
    case "salary":
      return Briefcase;
    case "freelance":
      return Laptop;
    case "business":
      return Building2;
    case "bonus":
      return Award;
    case "gift":
      return Gift;
    case "investment":
      return TrendingUp;
    default:
      return Wallet;
  }
}

function formatAllocationMonth(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

function formatDateReceived(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ─── Form State ──────────────────────────────────────────────────────────────

interface FormState {
  income_type: IncomeTypeValue;
  amount: string;
  date_received: string;
  income_allocation_type: IncomeAllocationTypeValue;
  is_recurring: boolean;
  recurring_day: string;
  note: string;
}

const DEFAULT_FORM: FormState = {
  income_type: "salary",
  amount: "",
  date_received: new Date().toISOString().split("T")[0] ?? "",
  income_allocation_type: "same_month",
  is_recurring: false,
  recurring_day: "",
  note: "",
};

// ─── Page Component ─────────────────────────────────────────────────────────

export default function IncomePage() {
  const { incomes: sources, loading: pageLoading, addIncome, removeIncome } = useIncome();
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Derived totals
  const totalMonthlyIncome = sources.reduce((sum, s) => sum + Number(s.amount), 0);

  // Modal helpers
  function openModal() {
    setForm(DEFAULT_FORM);
    setFormError(null);
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setFormError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);

    try {
      await addIncome({
        income_type: form.income_type,
        amount: parseFloat(form.amount),
        date_received: form.date_received,
        income_allocation_type: form.income_allocation_type,
        is_recurring: form.is_recurring,
        recurring_day: form.is_recurring ? parseInt(form.recurring_day, 10) : null,
        note: form.note || null,
      });
      closeModal();
    } catch (err: unknown) {
      const message =
        (err as { message?: string })?.message ??
        "Failed to add income entry. Please try again.";
      setFormError(message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this income entry?")) return;
    try {
      await removeIncome(id);
    } catch {
      // error shown via hook state
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Income</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your income sources and allocation months
          </p>
        </div>
        <Button variant="primary" onClick={openModal}>
          <Plus className="h-4 w-4" />
          Add Income
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-100">
                <DollarSign className="h-5 w-5 text-success-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Income</p>
                <p className="text-xl font-bold text-gray-900">
                  {pageLoading ? "—" : formatCurrency(totalMonthlyIncome)}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                <Hash className="h-5 w-5 text-primary-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Income Entries</p>
                <p className="text-xl font-bold text-gray-900">
                  {pageLoading ? "—" : sources.length}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Income Entries List */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-gray-900">Income Entries</h2>
        </CardHeader>
        <CardBody className="p-0">
          {pageLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
          ) : sources.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
                <DollarSign className="h-6 w-6 text-gray-400" />
              </div>
              <p className="text-sm text-gray-500">
                No income entries yet. Add your first income entry to get started.
              </p>
              <Button variant="primary" className="mt-4" onClick={openModal}>
                <Plus className="h-4 w-4" />
                Add Income
              </Button>
            </div>
          ) : (
            <ul className="divide-y divide-gray-100">
              {sources.map((source) => {
                const TypeIcon = getTypeIcon(source.income_type);

                return (
                  <li
                    key={source.id}
                    className="flex items-center justify-between px-6 py-4 transition-colors hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-100">
                        <TypeIcon className="h-5 w-5 text-success-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {getTypeLabel(source.income_type)}
                        </p>
                        <div className="mt-1 flex flex-wrap items-center gap-2">
                          <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                            <CalendarDays className="h-3 w-3" />
                            Received {formatDateReceived(source.date_received)}
                          </span>
                          <span className="inline-flex items-center rounded-full bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700">
                            Allocated: {formatAllocationMonth(source.allocation_month)}
                          </span>
                          {source.is_recurring && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-warning-50 px-2 py-0.5 text-xs font-medium text-warning-700">
                              <Repeat className="h-3 w-3" />
                              Recurring (day {source.recurring_day})
                            </span>
                          )}
                          {source.income_allocation_type === "next_month" && (
                            <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                              Next month allocation
                            </span>
                          )}
                        </div>
                        {source.note && (
                          <p className="mt-1 text-xs text-gray-400">{source.note}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <p className="text-lg font-semibold text-gray-900">
                        {formatCurrency(Number(source.amount))}
                      </p>
                      <button
                        type="button"
                        onClick={() => handleDelete(source.id)}
                        className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardBody>
      </Card>

      {/* Add Income Modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeModal();
          }}
        >
          <div className="w-full max-w-md rounded-xl bg-white shadow-xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Add Income Entry
              </h3>
              <button
                type="button"
                className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                onClick={closeModal}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5">
              {/* Income Type select */}
              <div className="w-full">
                <label
                  htmlFor="income-type"
                  className="mb-1.5 block text-sm font-medium text-gray-700"
                >
                  Income Type
                </label>
                <select
                  id="income-type"
                  required
                  value={form.income_type}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      income_type: e.target.value as IncomeTypeValue,
                    }))
                  }
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                >
                  {INCOME_TYPE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Amount input */}
              <Input
                id="income-amount"
                label="Amount"
                type="number"
                required
                min={0.01}
                step={0.01}
                placeholder="0.00"
                value={form.amount}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, amount: e.target.value }))
                }
              />

              {/* Date Received */}
              <div className="w-full">
                <label
                  htmlFor="income-date"
                  className="mb-1.5 block text-sm font-medium text-gray-700"
                >
                  Date Received
                </label>
                <input
                  id="income-date"
                  type="date"
                  required
                  value={form.date_received}
                  max={new Date().toISOString().split("T")[0]}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      date_received: e.target.value,
                    }))
                  }
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>

              {/* Allocation Type */}
              <div className="w-full">
                <label
                  htmlFor="income-allocation"
                  className="mb-1.5 block text-sm font-medium text-gray-700"
                >
                  Allocation Month
                </label>
                <select
                  id="income-allocation"
                  required
                  value={form.income_allocation_type}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      income_allocation_type:
                        e.target.value as IncomeAllocationTypeValue,
                    }))
                  }
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                >
                  {ALLOCATION_TYPE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-400">
                  {ALLOCATION_TYPE_OPTIONS.find(
                    (o) => o.value === form.income_allocation_type,
                  )?.description}
                </p>
              </div>

              {/* Is Recurring */}
              <div className="flex items-center gap-2">
                <input
                  id="income-recurring"
                  type="checkbox"
                  checked={form.is_recurring}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      is_recurring: e.target.checked,
                      recurring_day: e.target.checked ? prev.recurring_day : "",
                    }))
                  }
                  className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <label
                  htmlFor="income-recurring"
                  className="text-sm font-medium text-gray-700"
                >
                  Recurring income
                </label>
              </div>

              {/* Recurring Day (conditionally shown) */}
              {form.is_recurring && (
                <Input
                  id="income-recurring-day"
                  label="Recurring Day of Month"
                  type="number"
                  required
                  min={1}
                  max={31}
                  placeholder="e.g. 31"
                  value={form.recurring_day}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      recurring_day: e.target.value,
                    }))
                  }
                />
              )}

              {/* Note */}
              <div className="w-full">
                <label
                  htmlFor="income-note"
                  className="mb-1.5 block text-sm font-medium text-gray-700"
                >
                  Note (optional)
                </label>
                <textarea
                  id="income-note"
                  rows={2}
                  maxLength={500}
                  placeholder="e.g. March salary"
                  value={form.note}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, note: e.target.value }))
                  }
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>

              {/* Inline error */}
              {formError && (
                <p className="text-sm text-danger-600" role="alert">
                  {formError}
                </p>
              )}

              {/* Action buttons */}
              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  className="flex-1"
                  onClick={closeModal}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  loading={submitting}
                >
                  Add Income
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
