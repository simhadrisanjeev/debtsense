"use client";

import { useState, useEffect } from "react";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { expensesApi } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import {
  Plus,
  X,
  Home,
  Car,
  Utensils,
  Zap,
  Gamepad2,
  DollarSign,
  PieChart,
  ShieldCheck,
  MoreVertical,
  Heart,
  Shield,
  ShoppingBag,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type ExpenseCategory =
  | "housing"
  | "transportation"
  | "food"
  | "utilities"
  | "insurance"
  | "healthcare"
  | "entertainment"
  | "subscriptions"
  | "other";

type ExpenseFrequency =
  | "one_time"
  | "weekly"
  | "biweekly"
  | "monthly"
  | "annually";

interface ExpenseResponse {
  id: string;
  user_id: string;
  category: ExpenseCategory;
  description: string;
  amount: string;
  frequency: ExpenseFrequency;
  is_recurring: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface FormState {
  category: ExpenseCategory;
  description: string;
  amount: string;
  frequency: ExpenseFrequency;
  is_recurring: boolean;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const CATEGORY_OPTIONS: { value: ExpenseCategory; label: string }[] = [
  { value: "housing", label: "Housing" },
  { value: "transportation", label: "Transportation" },
  { value: "food", label: "Food" },
  { value: "utilities", label: "Utilities" },
  { value: "insurance", label: "Insurance" },
  { value: "healthcare", label: "Healthcare" },
  { value: "entertainment", label: "Entertainment" },
  { value: "subscriptions", label: "Subscriptions" },
  { value: "other", label: "Other" },
];

const FREQUENCY_OPTIONS: { value: ExpenseFrequency; label: string }[] = [
  { value: "one_time", label: "One Time" },
  { value: "weekly", label: "Weekly" },
  { value: "biweekly", label: "Bi-weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "annually", label: "Annually" },
];

const CATEGORY_CONFIG: Record<
  ExpenseCategory,
  {
    label: string;
    icon: React.ElementType;
    iconBg: string;
    iconColor: string;
  }
> = {
  housing: {
    label: "Housing",
    icon: Home,
    iconBg: "bg-primary-100",
    iconColor: "text-primary-600",
  },
  transportation: {
    label: "Transportation",
    icon: Car,
    iconBg: "bg-warning-100",
    iconColor: "text-warning-600",
  },
  food: {
    label: "Food",
    icon: Utensils,
    iconBg: "bg-success-100",
    iconColor: "text-success-600",
  },
  utilities: {
    label: "Utilities",
    icon: Zap,
    iconBg: "bg-danger-100",
    iconColor: "text-danger-600",
  },
  insurance: {
    label: "Insurance",
    icon: Shield,
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
  },
  healthcare: {
    label: "Healthcare",
    icon: Heart,
    iconBg: "bg-pink-100",
    iconColor: "text-pink-600",
  },
  entertainment: {
    label: "Entertainment",
    icon: Gamepad2,
    iconBg: "bg-purple-100",
    iconColor: "text-purple-600",
  },
  subscriptions: {
    label: "Subscriptions",
    icon: ShoppingBag,
    iconBg: "bg-indigo-100",
    iconColor: "text-indigo-600",
  },
  other: {
    label: "Other",
    icon: DollarSign,
    iconBg: "bg-gray-100",
    iconColor: "text-gray-600",
  },
};

const FREQUENCY_BADGE: Record<
  ExpenseFrequency,
  { label: string; color: string }
> = {
  one_time: { label: "One Time", color: "bg-gray-100 text-gray-600" },
  weekly: { label: "Weekly", color: "bg-warning-100 text-warning-700" },
  biweekly: { label: "Bi-weekly", color: "bg-success-100 text-success-700" },
  monthly: { label: "Monthly", color: "bg-primary-100 text-primary-700" },
  annually: { label: "Annually", color: "bg-danger-100 text-danger-700" },
};

const DEFAULT_FORM: FormState = {
  category: "housing",
  description: "",
  amount: "",
  frequency: "monthly",
  is_recurring: true,
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function toMonthlyAmount(amount: number, frequency: ExpenseFrequency): number {
  switch (frequency) {
    case "weekly":
      return amount * 4;
    case "biweekly":
      return amount * 2;
    case "monthly":
      return amount;
    case "annually":
      return amount / 12;
    case "one_time":
      return 0;
    default:
      return amount;
  }
}

// ─── Page Component ───────────────────────────────────────────────────────────

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [pageLoading, setPageLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Load expenses on mount
  useEffect(() => {
    expensesApi
      .list()
      .then((res) => {
        const data = res.data as unknown as ExpenseResponse[];
        setExpenses(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        setExpenses([]);
      })
      .finally(() => setPageLoading(false));
  }, []);

  // Derived totals
  const totalMonthly = expenses.reduce(
    (sum, e) =>
      sum + toMonthlyAmount(parseFloat(e.amount || "0"), e.frequency),
    0,
  );

  // Group expenses by category, preserving CATEGORY_CONFIG display order
  const grouped = expenses.reduce<Record<string, ExpenseResponse[]>>(
    (acc, e) => {
      const key = e.category ?? "other";
      if (!acc[key]) acc[key] = [];
      acc[key].push(e);
      return acc;
    },
    {},
  );
  const categoriesWithExpenses = (
    Object.keys(CATEGORY_CONFIG) as ExpenseCategory[]
  ).filter((cat) => (grouped[cat]?.length ?? 0) > 0);

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
      const payload = {
        category: form.category,
        description: form.description,
        amount: parseFloat(form.amount).toFixed(2),
        frequency: form.frequency,
        is_recurring:
          form.frequency === "one_time" ? false : form.is_recurring,
      };
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const res = await expensesApi.create(payload as any);
      const newExpense = res.data as unknown as ExpenseResponse;
      setExpenses((prev) => [...prev, newExpense]);
      closeModal();
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: { detail?: unknown } };
      };
      const detail = axiosErr?.response?.data?.detail;
      setFormError(
        typeof detail === "string"
          ? detail
          : detail
            ? JSON.stringify(detail)
            : "Failed to add expense. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Expenses</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track your monthly spending
          </p>
        </div>
        <Button variant="primary" onClick={openModal}>
          <Plus className="h-4 w-4" />
          Add Expense
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-danger-100">
                <DollarSign className="h-5 w-5 text-danger-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Monthly Expenses</p>
                <p className="text-xl font-bold text-gray-900">
                  {pageLoading ? "\u2014" : formatCurrency(totalMonthly)}
                </p>
                {!pageLoading && totalMonthly > 0 && (
                  <p className="text-xs text-gray-400">approximate</p>
                )}
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                <PieChart className="h-5 w-5 text-primary-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Expenses</p>
                <p className="text-xl font-bold text-gray-900">
                  {pageLoading ? "\u2014" : expenses.length}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Expenses by Category */}
      <div className="space-y-4">
        {pageLoading ? (
          <Card>
            <CardBody>
              <div className="flex items-center justify-center py-12">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
              </div>
            </CardBody>
          </Card>
        ) : categoriesWithExpenses.length === 0 ? (
          <Card>
            <CardBody>
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
                  <ShieldCheck className="h-7 w-7 text-gray-400" />
                </div>
                <p className="text-sm font-medium text-gray-900">
                  No expenses yet. Add your first expense to get started.
                </p>
                <Button
                  variant="primary"
                  className="mt-4"
                  onClick={openModal}
                >
                  <Plus className="h-4 w-4" />
                  Add Expense
                </Button>
              </div>
            </CardBody>
          </Card>
        ) : (
          categoriesWithExpenses.map((cat) => {
            const config = CATEGORY_CONFIG[cat];
            const CategoryIcon = config.icon;
            const catExpenses = grouped[cat] ?? [];
            const catMonthly = catExpenses.reduce(
              (sum, e) =>
                sum +
                toMonthlyAmount(parseFloat(e.amount || "0"), e.frequency),
              0,
            );

            return (
              <Card key={cat}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-lg ${config.iconBg}`}
                      >
                        <CategoryIcon
                          className={`h-4 w-4 ${config.iconColor}`}
                        />
                      </div>
                      <h3 className="font-semibold text-gray-900">
                        {config.label}
                      </h3>
                      <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                        {catExpenses.length}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-gray-500">
                      {formatCurrency(catMonthly)}/mo
                    </p>
                  </div>
                </CardHeader>
                <CardBody className="p-0">
                  <ul className="divide-y divide-gray-50">
                    {catExpenses.map((expense) => {
                      const badge =
                        FREQUENCY_BADGE[expense.frequency] ??
                        FREQUENCY_BADGE.monthly;
                      const rawAmount = parseFloat(expense.amount || "0");

                      return (
                        <li
                          key={expense.id}
                          className="flex items-center justify-between px-6 py-3 transition-colors hover:bg-gray-50"
                        >
                          <div className="flex items-center gap-3">
                            <p className="text-sm font-medium text-gray-700">
                              {expense.description}
                            </p>
                            <span
                              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badge.color}`}
                            >
                              {badge.label}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <p className="text-sm font-semibold text-gray-900">
                              {formatCurrency(rawAmount)}
                            </p>
                            <button
                              type="button"
                              className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                            >
                              <MoreVertical className="h-4 w-4" />
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </CardBody>
              </Card>
            );
          })
        )}
      </div>

      {/* Add Expense Modal */}
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
                Add Expense
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
              {/* Category select */}
              <div className="w-full">
                <label
                  htmlFor="expense-category"
                  className="mb-1.5 block text-sm font-medium text-gray-700"
                >
                  Category
                </label>
                <select
                  id="expense-category"
                  required
                  value={form.category}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      category: e.target.value as ExpenseCategory,
                    }))
                  }
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                >
                  {CATEGORY_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description input */}
              <Input
                id="expense-description"
                label="Description"
                type="text"
                required
                placeholder="e.g. Monthly rent"
                value={form.description}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
              />

              {/* Amount input */}
              <Input
                id="expense-amount"
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

              {/* Frequency select */}
              <div className="w-full">
                <label
                  htmlFor="expense-frequency"
                  className="mb-1.5 block text-sm font-medium text-gray-700"
                >
                  Frequency
                </label>
                <select
                  id="expense-frequency"
                  required
                  value={form.frequency}
                  onChange={(e) => {
                    const freq = e.target.value as ExpenseFrequency;
                    setForm((prev) => ({
                      ...prev,
                      frequency: freq,
                      is_recurring:
                        freq === "one_time" ? false : prev.is_recurring,
                    }));
                  }}
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                >
                  {FREQUENCY_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Is Recurring checkbox — hidden when frequency is one_time */}
              {form.frequency !== "one_time" && (
                <label className="flex cursor-pointer items-center gap-3">
                  <input
                    type="checkbox"
                    checked={form.is_recurring}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        is_recurring: e.target.checked,
                      }))
                    }
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Recurring expense
                  </span>
                </label>
              )}

              {/* Inline error */}
              {formError && (
                <div
                  className="rounded-lg bg-danger-50 px-4 py-3 text-sm text-danger-700"
                  role="alert"
                >
                  {formError}
                </div>
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
                  Add Expense
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
