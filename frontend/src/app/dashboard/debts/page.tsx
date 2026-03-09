"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useDebts } from "@/hooks/useDebts";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { formatCurrency, formatPercent } from "@/lib/utils";
import {
  Plus,
  X,
  CreditCard,
  Building2,
  Car,
  GraduationCap,
  Home,
  Users,
  Landmark,
  Briefcase,
  Coins,
  CircleDollarSign,
  ChevronRight,
  ChevronLeft,
  MoreVertical,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type DebtType =
  | "credit_card"
  | "personal_loan"
  | "gold_loan"
  | "home_loan"
  | "auto_loan"
  | "education_loan"
  | "informal_loan"
  | "money_lender"
  | "business_loan"
  | "chit_fund"
  | "other";

type InterestType =
  | "reducing_balance"
  | "flat_interest"
  | "monthly_interest"
  | "no_interest";

type RepaymentStyle =
  | "emi"
  | "interest_only"
  | "bullet_payment"
  | "flexible";

type PaymentFrequency =
  | "weekly"
  | "monthly"
  | "quarterly"
  | "yearly"
  | "custom";

interface FormState {
  // Step 1
  debt_type: DebtType;
  // Step 2
  name: string;
  lender_name: string;
  principal_amount: string;
  current_balance: string;
  start_date: string;
  end_date: string;
  notes: string;
  // Step 3
  interest_rate: string;
  interest_type: InterestType;
  repayment_style: RepaymentStyle;
  // Step 4
  payment_frequency: PaymentFrequency;
  minimum_payment: string;
  due_day_of_month: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const STEP_LABELS = ["Debt Type", "Loan Details", "Interest Details", "Payment Settings"];

const DEBT_TYPE_OPTIONS: { value: DebtType; label: string; icon: React.ElementType }[] = [
  { value: "credit_card", label: "Credit Card", icon: CreditCard },
  { value: "personal_loan", label: "Personal Loan", icon: Users },
  { value: "gold_loan", label: "Gold Loan", icon: Coins },
  { value: "home_loan", label: "Home Loan", icon: Home },
  { value: "auto_loan", label: "Auto Loan", icon: Car },
  { value: "education_loan", label: "Education Loan", icon: GraduationCap },
  { value: "informal_loan", label: "Informal Loan", icon: Users },
  { value: "money_lender", label: "Money Lender", icon: CircleDollarSign },
  { value: "business_loan", label: "Business Loan", icon: Briefcase },
  { value: "chit_fund", label: "Chit Fund", icon: Landmark },
  { value: "other", label: "Other", icon: Building2 },
];

const INTEREST_TYPE_OPTIONS: { value: InterestType; label: string }[] = [
  { value: "reducing_balance", label: "Reducing Balance" },
  { value: "flat_interest", label: "Flat Interest" },
  { value: "monthly_interest", label: "Monthly Interest" },
  { value: "no_interest", label: "No Interest" },
];

const REPAYMENT_STYLE_OPTIONS: { value: RepaymentStyle; label: string }[] = [
  { value: "emi", label: "EMI" },
  { value: "interest_only", label: "Interest Only" },
  { value: "bullet_payment", label: "Bullet Payment" },
  { value: "flexible", label: "Flexible" },
];

const PAYMENT_FREQUENCY_OPTIONS: { value: PaymentFrequency; label: string }[] = [
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "yearly", label: "Yearly" },
  { value: "custom", label: "Custom" },
];

const typeConfig: Record<
  DebtType,
  { label: string; icon: React.ElementType; color: string }
> = {
  credit_card: {
    label: "Credit Card",
    icon: CreditCard,
    color: "bg-danger-100 text-danger-700",
  },
  personal_loan: {
    label: "Personal Loan",
    icon: Users,
    color: "bg-gray-100 text-gray-700",
  },
  gold_loan: {
    label: "Gold Loan",
    icon: Coins,
    color: "bg-warning-100 text-warning-700",
  },
  home_loan: {
    label: "Home Loan",
    icon: Home,
    color: "bg-success-100 text-success-700",
  },
  auto_loan: {
    label: "Auto Loan",
    icon: Car,
    color: "bg-warning-100 text-warning-700",
  },
  education_loan: {
    label: "Education Loan",
    icon: GraduationCap,
    color: "bg-primary-100 text-primary-700",
  },
  informal_loan: {
    label: "Informal Loan",
    icon: Users,
    color: "bg-purple-100 text-purple-700",
  },
  money_lender: {
    label: "Money Lender",
    icon: CircleDollarSign,
    color: "bg-danger-100 text-danger-700",
  },
  business_loan: {
    label: "Business Loan",
    icon: Briefcase,
    color: "bg-primary-100 text-primary-700",
  },
  chit_fund: {
    label: "Chit Fund",
    icon: Landmark,
    color: "bg-success-100 text-success-700",
  },
  other: {
    label: "Other",
    icon: Building2,
    color: "bg-gray-100 text-gray-600",
  },
};

const REPAYMENT_STYLE_LABELS: Record<RepaymentStyle, string> = {
  emi: "EMI",
  interest_only: "Interest Only",
  bullet_payment: "Bullet",
  flexible: "Flexible",
};

const EMPTY_FORM: FormState = {
  debt_type: "credit_card",
  name: "",
  lender_name: "",
  principal_amount: "",
  current_balance: "",
  start_date: "",
  end_date: "",
  notes: "",
  interest_rate: "",
  interest_type: "reducing_balance",
  repayment_style: "emi",
  payment_frequency: "monthly",
  minimum_payment: "",
  due_day_of_month: "",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getDefaultsForDebtType(
  debtType: DebtType,
): Partial<Pick<FormState, "interest_type" | "repayment_style">> {
  switch (debtType) {
    case "informal_loan":
    case "money_lender":
      return { interest_type: "monthly_interest", repayment_style: "flexible" };
    case "credit_card":
      return { repayment_style: "emi" };
    case "chit_fund":
      return { interest_type: "no_interest" };
    default:
      return {};
  }
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DebtsPage() {
  const router = useRouter();
  const { debts, loading, addDebt } = useDebts();

  const [modalOpen, setModalOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Summary stats -- interest_rate is stored as decimal (0.1999), so multiply by 100 for display
  const totalDebt = debts.reduce(
    (sum, d) => sum + parseFloat(d.current_balance || "0"),
    0,
  );
  const avgInterest =
    debts.length > 0
      ? (debts.reduce(
          (sum, d) => sum + parseFloat(d.interest_rate || "0"),
          0,
        ) /
          debts.length) *
        100
      : 0;
  const totalMinPayments = debts.reduce(
    (sum, d) => sum + parseFloat(d.minimum_payment || "0"),
    0,
  );

  // ── Modal Controls ──────────────────────────────────────────────────────────

  function openModal() {
    setForm(EMPTY_FORM);
    setStep(0);
    setFormError(null);
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setFormError(null);
  }

  function handleFieldChange<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  // When debt type changes on step 1, apply dynamic defaults
  function handleDebtTypeSelect(debtType: DebtType) {
    const defaults = getDefaultsForDebtType(debtType);
    setForm((prev) => ({
      ...prev,
      debt_type: debtType,
      interest_type: defaults.interest_type ?? prev.interest_type,
      repayment_style: defaults.repayment_style ?? prev.repayment_style,
    }));
  }

  function handleNext() {
    setFormError(null);

    // Validate current step before advancing
    if (step === 1) {
      if (!form.name.trim()) {
        setFormError("Name is required.");
        return;
      }
      if (!form.principal_amount || parseFloat(form.principal_amount) <= 0) {
        setFormError("Principal amount must be greater than zero.");
        return;
      }
      if (!form.current_balance || parseFloat(form.current_balance) < 0) {
        setFormError("Current balance is required.");
        return;
      }
      if (!form.start_date) {
        setFormError("Start date is required.");
        return;
      }
    }

    if (step === 2) {
      if (!form.interest_rate && form.interest_type !== "no_interest") {
        setFormError("Interest rate is required.");
        return;
      }
    }

    setStep((s) => Math.min(s + 1, 3));
  }

  function handleBack() {
    setFormError(null);
    setStep((s) => Math.max(s - 1, 0));
  }

  async function handleSubmit() {
    setSubmitting(true);
    setFormError(null);

    try {
      const payload = {
        name: form.name.trim(),
        debt_type: form.debt_type,
        lender_name: form.lender_name.trim() || null,
        principal_amount: form.principal_amount,
        current_balance: form.current_balance,
        // User enters percentage (e.g. 19.99); backend expects decimal (e.g. 0.1999)
        interest_rate: String(parseFloat(form.interest_rate || "0") / 100),
        interest_type: form.interest_type,
        repayment_style: form.repayment_style,
        payment_frequency: form.payment_frequency,
        minimum_payment: form.minimum_payment || "0",
        due_day_of_month: parseInt(form.due_day_of_month || "1", 10),
        start_date: form.start_date,
        end_date: form.end_date || null,
        is_active: true,
        notes: form.notes.trim() || null,
      };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await addDebt(payload as any);
      closeModal();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError("Failed to create debt. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Debts</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track and manage your debt accounts
          </p>
        </div>
        <Button variant="primary" onClick={openModal}>
          <Plus className="h-4 w-4" />
          Add Debt
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-danger-100">
                <CircleDollarSign className="h-5 w-5 text-danger-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Debt</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatCurrency(totalDebt)}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning-100">
                <Landmark className="h-5 w-5 text-warning-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Avg Interest Rate</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatPercent(avgInterest)}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                <Coins className="h-5 w-5 text-primary-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Min. Payments</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatCurrency(totalMinPayments)}/mo
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Debts Table */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-gray-900">
            All Debts ({debts.length})
          </h2>
        </CardHeader>
        <CardBody className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
          ) : debts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
                <CreditCard className="h-7 w-7 text-gray-400" />
              </div>
              <p className="mt-4 text-sm font-medium text-gray-900">
                No debts yet. Add your first debt to get started.
              </p>
              <Button variant="primary" className="mt-4" onClick={openModal}>
                <Plus className="h-4 w-4" />
                Add Debt
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-sm font-medium text-gray-500">
                    <th className="px-6 py-3">Name</th>
                    <th className="px-6 py-3">Type</th>
                    <th className="px-6 py-3">Lender</th>
                    <th className="px-6 py-3 text-right">Balance</th>
                    <th className="px-6 py-3 text-right">APR%</th>
                    <th className="px-6 py-3 text-right">Min Payment</th>
                    <th className="px-6 py-3">Style</th>
                    <th className="px-6 py-3">Progress</th>
                    <th className="px-6 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {debts.map((debt) => {
                    const config =
                      typeConfig[debt.debt_type as DebtType] ?? typeConfig.other;
                    const TypeIcon = config.icon;
                    const principal = parseFloat(
                      debt.principal_amount || "0",
                    );
                    const current = parseFloat(debt.current_balance || "0");
                    const paidPercent =
                      principal > 0
                        ? Math.min(
                            100,
                            Math.round(
                              ((principal - current) / principal) * 100,
                            ),
                          )
                        : 0;
                    const aprPercent =
                      parseFloat(debt.interest_rate || "0") * 100;
                    const styleLabel =
                      REPAYMENT_STYLE_LABELS[
                        debt.repayment_style as RepaymentStyle
                      ] ?? debt.repayment_style;

                    return (
                      <tr
                        key={debt.id}
                        onClick={() =>
                          router.push(`/dashboard/debts/${debt.id}`)
                        }
                        className="cursor-pointer transition-colors hover:bg-gray-50"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100">
                              <TypeIcon className="h-4 w-4 text-gray-600" />
                            </div>
                            <span className="font-medium text-gray-900">
                              {debt.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.color}`}
                          >
                            {config.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {debt.lender_name || "\u2014"}
                        </td>
                        <td className="px-6 py-4 text-right font-semibold text-gray-900">
                          {formatCurrency(current)}
                        </td>
                        <td className="px-6 py-4 text-right text-gray-700">
                          {formatPercent(aprPercent)}
                        </td>
                        <td className="px-6 py-4 text-right text-gray-700">
                          {formatCurrency(
                            parseFloat(debt.minimum_payment || "0"),
                          )}
                          /mo
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                            {styleLabel}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-24 rounded-full bg-gray-200">
                              <div
                                className="h-2 rounded-full bg-success-500 transition-all"
                                style={{ width: `${paidPercent}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-500">
                              {paidPercent}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                            }}
                            className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                          >
                            <MoreVertical className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* ── Add Debt Modal ─────────────────────────────────────────────────────── */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-xl bg-white shadow-xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-900">Add Debt</h2>
              <button
                type="button"
                onClick={closeModal}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Step Indicator */}
            <div className="border-b border-gray-200 px-6 py-4">
              <div className="flex items-center justify-between">
                {STEP_LABELS.map((label, i) => {
                  const isActive = i === step;
                  const isCompleted = i < step;
                  return (
                    <div key={label} className="flex flex-1 items-center">
                      <div className="flex items-center gap-2">
                        <div
                          className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold transition-colors ${
                            isActive
                              ? "bg-primary-600 text-white"
                              : isCompleted
                                ? "bg-primary-100 text-primary-700"
                                : "bg-gray-100 text-gray-400"
                          }`}
                        >
                          {i + 1}
                        </div>
                        <span
                          className={`hidden text-sm font-medium sm:inline ${
                            isActive
                              ? "text-primary-700"
                              : isCompleted
                                ? "text-gray-700"
                                : "text-gray-400"
                          }`}
                        >
                          {label}
                        </span>
                      </div>
                      {i < STEP_LABELS.length - 1 && (
                        <div
                          className={`mx-3 h-px flex-1 ${
                            isCompleted ? "bg-primary-300" : "bg-gray-200"
                          }`}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Modal Body */}
            <div className="max-h-[60vh] overflow-y-auto px-6 py-6">
              {/* Step 1: Debt Type */}
              {step === 0 && (
                <div>
                  <p className="mb-4 text-sm text-gray-600">
                    What type of debt would you like to add?
                  </p>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                    {DEBT_TYPE_OPTIONS.map((opt) => {
                      const Icon = opt.icon;
                      const isSelected = form.debt_type === opt.value;
                      return (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => handleDebtTypeSelect(opt.value)}
                          className={`flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-center transition-all ${
                            isSelected
                              ? "border-primary-500 bg-primary-50 ring-1 ring-primary-500"
                              : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                          }`}
                        >
                          <div
                            className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                              isSelected
                                ? "bg-primary-100 text-primary-600"
                                : "bg-gray-100 text-gray-500"
                            }`}
                          >
                            <Icon className="h-5 w-5" />
                          </div>
                          <span
                            className={`text-sm font-medium ${
                              isSelected ? "text-primary-700" : "text-gray-700"
                            }`}
                          >
                            {opt.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Step 2: Loan Details */}
              {step === 1 && (
                <div className="space-y-4">
                  <Input
                    label="Name"
                    type="text"
                    value={form.name}
                    onChange={(e) => handleFieldChange("name", e.target.value)}
                    placeholder="e.g. HDFC Credit Card"
                    required
                  />
                  <Input
                    label="Lender Name"
                    type="text"
                    value={form.lender_name}
                    onChange={(e) =>
                      handleFieldChange("lender_name", e.target.value)
                    }
                    placeholder="e.g. HDFC Bank (optional)"
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      label="Principal Amount"
                      type="number"
                      value={form.principal_amount}
                      onChange={(e) =>
                        handleFieldChange("principal_amount", e.target.value)
                      }
                      placeholder="0.00"
                      required
                      min="0"
                      step="0.01"
                    />
                    <Input
                      label="Current Balance"
                      type="number"
                      value={form.current_balance}
                      onChange={(e) =>
                        handleFieldChange("current_balance", e.target.value)
                      }
                      placeholder="0.00"
                      required
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      label="Start Date"
                      type="date"
                      value={form.start_date}
                      onChange={(e) =>
                        handleFieldChange("start_date", e.target.value)
                      }
                      required
                    />
                    <Input
                      label="End Date (optional)"
                      type="date"
                      value={form.end_date}
                      onChange={(e) =>
                        handleFieldChange("end_date", e.target.value)
                      }
                    />
                  </div>
                  <div className="w-full">
                    <label className="mb-1.5 block text-sm font-medium text-gray-700">
                      Notes (optional)
                    </label>
                    <textarea
                      value={form.notes}
                      onChange={(e) =>
                        handleFieldChange("notes", e.target.value)
                      }
                      rows={3}
                      placeholder="Any additional notes about this debt..."
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-gray-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    />
                  </div>
                </div>
              )}

              {/* Step 3: Interest Details */}
              {step === 2 && (
                <div className="space-y-4">
                  <Input
                    label="Interest Rate (%)"
                    type="number"
                    value={form.interest_rate}
                    onChange={(e) =>
                      handleFieldChange("interest_rate", e.target.value)
                    }
                    placeholder="e.g. 19.99"
                    min="0"
                    max="100"
                    step="0.01"
                  />
                  <div className="w-full">
                    <label className="mb-1.5 block text-sm font-medium text-gray-700">
                      Interest Type
                    </label>
                    <select
                      value={form.interest_type}
                      onChange={(e) =>
                        handleFieldChange(
                          "interest_type",
                          e.target.value as InterestType,
                        )
                      }
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm transition-colors focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    >
                      {INTEREST_TYPE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="w-full">
                    <label className="mb-1.5 block text-sm font-medium text-gray-700">
                      Repayment Style
                    </label>
                    <select
                      value={form.repayment_style}
                      onChange={(e) =>
                        handleFieldChange(
                          "repayment_style",
                          e.target.value as RepaymentStyle,
                        )
                      }
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm transition-colors focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    >
                      {REPAYMENT_STYLE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Step 4: Payment Settings */}
              {step === 3 && (
                <div className="space-y-4">
                  <div className="w-full">
                    <label className="mb-1.5 block text-sm font-medium text-gray-700">
                      Payment Frequency
                    </label>
                    <select
                      value={form.payment_frequency}
                      onChange={(e) =>
                        handleFieldChange(
                          "payment_frequency",
                          e.target.value as PaymentFrequency,
                        )
                      }
                      className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm transition-colors focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    >
                      {PAYMENT_FREQUENCY_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Input
                    label="Minimum Payment"
                    type="number"
                    value={form.minimum_payment}
                    onChange={(e) =>
                      handleFieldChange("minimum_payment", e.target.value)
                    }
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                  />
                  <Input
                    label="Due Day of Month"
                    type="number"
                    value={form.due_day_of_month}
                    onChange={(e) =>
                      handleFieldChange("due_day_of_month", e.target.value)
                    }
                    placeholder="1-31"
                    min="1"
                    max="31"
                  />
                </div>
              )}

              {/* Error message */}
              {formError && (
                <div className="mt-4 rounded-lg bg-danger-50 px-4 py-3 text-sm text-danger-700">
                  {formError}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between border-t border-gray-200 px-6 py-4">
              <div>
                {step > 0 && (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={handleBack}
                    disabled={submitting}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Back
                  </Button>
                )}
              </div>
              <div className="flex items-center gap-3">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={closeModal}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                {step < 3 ? (
                  <Button type="button" variant="primary" onClick={handleNext}>
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                ) : (
                  <Button
                    type="button"
                    variant="primary"
                    loading={submitting}
                    onClick={handleSubmit}
                  >
                    Create Debt
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
