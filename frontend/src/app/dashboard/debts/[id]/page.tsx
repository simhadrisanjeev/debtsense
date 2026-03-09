"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { useDebtOverrides } from "@/hooks/useDebts";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { formatCurrency, formatPercent, formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  Plus,
  Trash2,
  Calendar,
  DollarSign,
  Info,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface DebtDetail {
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

interface ScheduleMonth {
  month: string;
  interest: string;
  payment: string;
  principal_paid: string;
  remaining_balance: string;
}

interface ScheduleResponse {
  debt_id: string;
  schedule: ScheduleMonth[];
  total_interest: string;
  total_paid: string;
  payoff_months: number;
}

// ─── Label Maps ───────────────────────────────────────────────────────────────

const DEBT_TYPE_LABELS: Record<string, string> = {
  credit_card: "Credit Card",
  personal_loan: "Personal Loan",
  gold_loan: "Gold Loan",
  home_loan: "Home Loan",
  auto_loan: "Auto Loan",
  education_loan: "Education Loan",
  informal_loan: "Informal Loan",
  money_lender: "Money Lender",
  business_loan: "Business Loan",
  chit_fund: "Chit Fund",
  other: "Other",
};

const INTEREST_TYPE_LABELS: Record<string, string> = {
  reducing_balance: "Reducing Balance",
  flat_interest: "Flat Interest",
  monthly_interest: "Monthly Interest",
  no_interest: "No Interest",
};

const REPAYMENT_STYLE_LABELS: Record<string, string> = {
  emi: "EMI",
  interest_only: "Interest Only",
  bullet_payment: "Bullet Payment",
  flexible: "Flexible",
};

const PAYMENT_FREQUENCY_LABELS: Record<string, string> = {
  weekly: "Weekly",
  monthly: "Monthly",
  quarterly: "Quarterly",
  yearly: "Yearly",
  custom: "Custom",
};

const DEBT_TYPE_COLORS: Record<string, string> = {
  credit_card: "bg-danger-100 text-danger-700",
  personal_loan: "bg-gray-100 text-gray-700",
  gold_loan: "bg-warning-100 text-warning-700",
  home_loan: "bg-success-100 text-success-700",
  auto_loan: "bg-warning-100 text-warning-700",
  education_loan: "bg-primary-100 text-primary-700",
  informal_loan: "bg-purple-100 text-purple-700",
  money_lender: "bg-danger-100 text-danger-700",
  business_loan: "bg-primary-100 text-primary-700",
  chit_fund: "bg-success-100 text-success-700",
  other: "bg-gray-100 text-gray-600",
};

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DebtDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  // ── Debt data ──────────────────────────────────────────────────────────────
  const [debt, setDebt] = useState<DebtDetail | null>(null);
  const [debtLoading, setDebtLoading] = useState(true);
  const [debtError, setDebtError] = useState<string | null>(null);

  // ── Schedule data ──────────────────────────────────────────────────────────
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [scheduleLoading, setScheduleLoading] = useState(true);
  const [scheduleError, setScheduleError] = useState<string | null>(null);

  // ── Overrides ──────────────────────────────────────────────────────────────
  const {
    overrides,
    loading: overridesLoading,
    error: overridesError,
    fetchOverrides,
    addOverride,
    removeOverride,
  } = useDebtOverrides(id);

  // ── Override form state ────────────────────────────────────────────────────
  const [showAddForm, setShowAddForm] = useState(false);
  const [overrideMonth, setOverrideMonth] = useState("");
  const [overrideAmount, setOverrideAmount] = useState("");
  const [overrideNote, setOverrideNote] = useState("");
  const [overrideSubmitting, setOverrideSubmitting] = useState(false);
  const [overrideFormError, setOverrideFormError] = useState<string | null>(
    null,
  );

  // ── Fetch debt detail ──────────────────────────────────────────────────────
  useEffect(() => {
    async function fetchDebt() {
      setDebtLoading(true);
      setDebtError(null);
      try {
        const { data } = await api.get<DebtDetail>(`/debts/${id}`);
        setDebt(data);
      } catch (err: unknown) {
        setDebtError(
          err instanceof Error ? err.message : "Failed to load debt details",
        );
      } finally {
        setDebtLoading(false);
      }
    }
    fetchDebt();
  }, [id]);

  // ── Fetch schedule ─────────────────────────────────────────────────────────
  const fetchSchedule = useCallback(async () => {
    setScheduleLoading(true);
    setScheduleError(null);
    try {
      const { data } = await api.get<ScheduleResponse>(
        `/debts/${id}/schedule?months=24`,
      );
      setSchedule(data);
    } catch (err: unknown) {
      setScheduleError(
        err instanceof Error
          ? err.message
          : "Failed to load payment schedule",
      );
    } finally {
      setScheduleLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchSchedule();
  }, [fetchSchedule]);

  // ── Override months set for highlighting ────────────────────────────────────
  const overrideMonthSet = new Set(overrides.map((o) => o.month_year));

  // ── Add override handler ───────────────────────────────────────────────────
  async function handleAddOverride() {
    setOverrideFormError(null);

    if (!overrideMonth) {
      setOverrideFormError("Month is required.");
      return;
    }
    if (!overrideAmount || parseFloat(overrideAmount) <= 0) {
      setOverrideFormError("Amount must be greater than zero.");
      return;
    }

    setOverrideSubmitting(true);
    try {
      await addOverride({
        month_year: overrideMonth,
        custom_payment_amount: overrideAmount,
        note: overrideNote.trim() || null,
      });
      // Reset form
      setOverrideMonth("");
      setOverrideAmount("");
      setOverrideNote("");
      setShowAddForm(false);
      // Refresh schedule to reflect the override
      await fetchSchedule();
    } catch (err: unknown) {
      setOverrideFormError(
        err instanceof Error ? err.message : "Failed to add override.",
      );
    } finally {
      setOverrideSubmitting(false);
    }
  }

  // ── Delete override handler ────────────────────────────────────────────────
  async function handleDeleteOverride(overrideId: string) {
    try {
      await removeOverride(overrideId);
      // Refresh schedule to reflect the removal
      await fetchSchedule();
    } catch {
      // Error is already handled by the hook
    }
  }

  // ── Loading state ──────────────────────────────────────────────────────────
  if (debtLoading) {
    return (
      <div className="space-y-6">
        <Link
          href="/dashboard/debts"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Debts
        </Link>
        <div className="flex items-center justify-center py-24">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
        </div>
      </div>
    );
  }

  // ── Error state ────────────────────────────────────────────────────────────
  if (debtError || !debt) {
    return (
      <div className="space-y-6">
        <Link
          href="/dashboard/debts"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Debts
        </Link>
        <Card>
          <CardBody>
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-danger-100">
                <Info className="h-7 w-7 text-danger-600" />
              </div>
              <p className="mt-4 text-sm font-medium text-gray-900">
                {debtError || "Debt not found."}
              </p>
              <Button
                variant="secondary"
                className="mt-4"
                onClick={() => router.push("/dashboard/debts")}
              >
                <ArrowLeft className="h-4 w-4" />
                Return to Debts
              </Button>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  // ── Derived values ─────────────────────────────────────────────────────────
  const currentBalance = parseFloat(debt.current_balance || "0");
  const interestRatePercent = parseFloat(debt.interest_rate || "0") * 100;
  const minimumPayment = parseFloat(debt.minimum_payment || "0");
  const debtTypeLabel = DEBT_TYPE_LABELS[debt.debt_type] ?? debt.debt_type;
  const debtTypeColor =
    DEBT_TYPE_COLORS[debt.debt_type] ?? "bg-gray-100 text-gray-600";
  const interestTypeLabel =
    INTEREST_TYPE_LABELS[debt.interest_type] ?? debt.interest_type;
  const repaymentStyleLabel =
    REPAYMENT_STYLE_LABELS[debt.repayment_style] ?? debt.repayment_style;
  const paymentFrequencyLabel =
    PAYMENT_FREQUENCY_LABELS[debt.payment_frequency] ?? debt.payment_frequency;

  return (
    <div className="space-y-6">
      {/* ── Back Button ────────────────────────────────────────────────────────── */}
      <Link
        href="/dashboard/debts"
        className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Debts
      </Link>

      {/* ── Debt Summary Card ──────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-gray-900">{debt.name}</h1>
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${debtTypeColor}`}
              >
                {debtTypeLabel}
              </span>
            </div>
            {debt.lender_name && (
              <span className="text-sm text-gray-500">{debt.lender_name}</span>
            )}
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-6">
            {/* Current Balance - large */}
            <div>
              <p className="text-sm font-medium text-gray-500">
                Current Balance
              </p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {formatCurrency(currentBalance)}
              </p>
            </div>

            {/* Interest & Repayment Badges */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2">
                <span className="text-sm text-gray-500">Interest Rate</span>
                <span className="text-sm font-semibold text-gray-900">
                  {formatPercent(interestRatePercent)}
                </span>
              </div>
              <span className="inline-flex items-center rounded-full bg-primary-50 px-2.5 py-0.5 text-xs font-medium text-primary-700">
                {interestTypeLabel}
              </span>
              <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                {repaymentStyleLabel}
              </span>
            </div>

            {/* Payment Details Grid */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="flex items-center gap-3 rounded-lg border border-gray-200 p-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-100">
                  <DollarSign className="h-4 w-4 text-primary-600" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Minimum Payment</p>
                  <p className="text-sm font-semibold text-gray-900">
                    {formatCurrency(minimumPayment)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-gray-200 p-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-100">
                  <Calendar className="h-4 w-4 text-primary-600" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Payment Frequency</p>
                  <p className="text-sm font-semibold text-gray-900">
                    {paymentFrequencyLabel}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-gray-200 p-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-100">
                  <Calendar className="h-4 w-4 text-primary-600" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Due Day</p>
                  <p className="text-sm font-semibold text-gray-900">
                    {debt.due_day_of_month}
                    {debt.due_day_of_month === 1
                      ? "st"
                      : debt.due_day_of_month === 2
                        ? "nd"
                        : debt.due_day_of_month === 3
                          ? "rd"
                          : "th"}{" "}
                    of month
                  </p>
                </div>
              </div>
            </div>

            {/* Dates */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs text-gray-500">Start Date</p>
                <p className="text-sm font-medium text-gray-900">
                  {formatDate(debt.start_date)}
                </p>
              </div>
              {debt.end_date && (
                <div>
                  <p className="text-xs text-gray-500">End Date</p>
                  <p className="text-sm font-medium text-gray-900">
                    {formatDate(debt.end_date)}
                  </p>
                </div>
              )}
            </div>

            {/* Notes */}
            {debt.notes && (
              <div className="rounded-lg bg-gray-50 p-4">
                <div className="flex items-center gap-2 mb-1">
                  <Info className="h-4 w-4 text-gray-400" />
                  <p className="text-xs font-medium text-gray-500">Notes</p>
                </div>
                <p className="text-sm text-gray-700">{debt.notes}</p>
              </div>
            )}
          </div>
        </CardBody>
      </Card>

      {/* ── Monthly Payment Overrides ──────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              Monthly Payment Overrides
            </h2>
            {!showAddForm && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setShowAddForm(true);
                  setOverrideFormError(null);
                }}
              >
                <Plus className="h-4 w-4" />
                Add Override
              </Button>
            )}
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {/* Add Override Inline Form */}
          {showAddForm && (
            <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
                <Input
                  label="Month"
                  type="month"
                  value={overrideMonth}
                  onChange={(e) => setOverrideMonth(e.target.value)}
                  placeholder="YYYY-MM"
                />
                <Input
                  label="Amount"
                  type="number"
                  value={overrideAmount}
                  onChange={(e) => setOverrideAmount(e.target.value)}
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
                <Input
                  label="Note (optional)"
                  type="text"
                  value={overrideNote}
                  onChange={(e) => setOverrideNote(e.target.value)}
                  placeholder="e.g. Bonus payment"
                />
                <div className="flex items-end gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    loading={overrideSubmitting}
                    onClick={handleAddOverride}
                  >
                    Save
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setShowAddForm(false);
                      setOverrideFormError(null);
                      setOverrideMonth("");
                      setOverrideAmount("");
                      setOverrideNote("");
                    }}
                    disabled={overrideSubmitting}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
              {overrideFormError && (
                <div className="mt-3 rounded-lg bg-danger-50 px-4 py-2 text-sm text-danger-700">
                  {overrideFormError}
                </div>
              )}
            </div>
          )}

          {/* Overrides Table */}
          {overridesLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
          ) : overridesError ? (
            <div className="px-6 py-8 text-center text-sm text-danger-600">
              {overridesError}
            </div>
          ) : overrides.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
                <Calendar className="h-6 w-6 text-gray-400" />
              </div>
              <p className="mt-3 text-sm text-gray-500">
                No payment overrides set. Add one to customize a specific
                month&apos;s payment.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-sm font-medium text-gray-500">
                    <th className="px-6 py-3">Month</th>
                    <th className="px-6 py-3 text-right">Amount</th>
                    <th className="px-6 py-3">Note</th>
                    <th className="px-6 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {overrides.map((override) => (
                    <tr key={override.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">
                        {override.month_year}
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-semibold text-gray-900">
                        {formatCurrency(
                          parseFloat(override.custom_payment_amount),
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {override.note || "\u2014"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleDeleteOverride(override.id)}
                          className="rounded-lg p-1.5 text-gray-400 hover:bg-danger-50 hover:text-danger-600 transition-colors"
                          title="Delete override"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* ── Payment Schedule ───────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-gray-900">
            Payment Schedule (24 months)
          </h2>
        </CardHeader>
        <CardBody className="p-0">
          {scheduleLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
          ) : scheduleError ? (
            <div className="px-6 py-8 text-center text-sm text-danger-600">
              {scheduleError}
            </div>
          ) : !schedule || schedule.schedule.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
                <DollarSign className="h-6 w-6 text-gray-400" />
              </div>
              <p className="mt-3 text-sm text-gray-500">
                No payment schedule available.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-sm font-medium text-gray-500">
                    <th className="px-6 py-3">Month</th>
                    <th className="px-6 py-3 text-right">Interest</th>
                    <th className="px-6 py-3 text-right">Payment</th>
                    <th className="px-6 py-3 text-right">Principal Paid</th>
                    <th className="px-6 py-3 text-right">Remaining Balance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {schedule.schedule.map((row) => {
                    const isOverridden = overrideMonthSet.has(row.month);
                    return (
                      <tr
                        key={row.month}
                        className={
                          isOverridden
                            ? "bg-primary-50 hover:bg-primary-100"
                            : "hover:bg-gray-50"
                        }
                      >
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                          {row.month}
                          {isOverridden && (
                            <span className="ml-2 inline-flex items-center rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700">
                              Override
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right text-sm text-gray-700">
                          {formatCurrency(parseFloat(row.interest))}
                        </td>
                        <td className="px-6 py-4 text-right text-sm font-semibold text-gray-900">
                          {formatCurrency(parseFloat(row.payment))}
                        </td>
                        <td className="px-6 py-4 text-right text-sm text-gray-700">
                          {formatCurrency(parseFloat(row.principal_paid))}
                        </td>
                        <td className="px-6 py-4 text-right text-sm text-gray-900">
                          {formatCurrency(parseFloat(row.remaining_balance))}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                {/* Totals Footer */}
                <tfoot>
                  <tr className="border-t-2 border-gray-300 bg-gray-50 font-semibold">
                    <td className="px-6 py-4 text-sm text-gray-900">Totals</td>
                    <td className="px-6 py-4 text-right text-sm text-gray-900">
                      {formatCurrency(parseFloat(schedule.total_interest))}
                    </td>
                    <td className="px-6 py-4 text-right text-sm text-gray-900">
                      {formatCurrency(parseFloat(schedule.total_paid))}
                    </td>
                    <td className="px-6 py-4 text-right text-sm text-gray-500">
                      &mdash;
                    </td>
                    <td className="px-6 py-4 text-right text-sm text-gray-500">
                      &mdash;
                    </td>
                  </tr>
                  <tr className="bg-gray-50">
                    <td
                      colSpan={5}
                      className="px-6 py-3 text-center text-sm text-gray-600"
                    >
                      Estimated payoff in{" "}
                      <span className="font-bold text-primary-700">
                        {schedule.payoff_months}
                      </span>{" "}
                      months &middot; Total Interest:{" "}
                      <span className="font-bold text-danger-700">
                        {formatCurrency(parseFloat(schedule.total_interest))}
                      </span>{" "}
                      &middot; Total Paid:{" "}
                      <span className="font-bold text-gray-900">
                        {formatCurrency(parseFloat(schedule.total_paid))}
                      </span>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
