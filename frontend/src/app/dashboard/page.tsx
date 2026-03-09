"use client";

import { useState, useEffect } from "react";
import { useDashboard } from "@/hooks/useDashboard";
import { useDebts } from "@/hooks/useDebts";
import api from "@/lib/api";
import { formatCurrency, formatRelativeTime, capitalize, formatDate } from "@/lib/utils";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import {
  DollarSign,
  CreditCard,
  TrendingUp,
  Calendar,
  Lightbulb,
  Activity,
  Loader2,
  Wallet,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface QuickTip {
  tip: string;
}

interface AnalyticsEvent {
  event_type: string;
  created_at: string;
}

// ─── Static fallback tips ────────────────────────────────────────────────────

const FALLBACK_TIPS: QuickTip[] = [
  { tip: "Focus on paying off high-interest debt first to save the most money over time." },
  { tip: "Consider setting up automatic payments to avoid late fees and stay consistent." },
  { tip: "Even small extra payments each month can significantly reduce your payoff timeline." },
];

// ─── Dashboard Page ──────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { stats, loading: statsLoading, error: statsError } = useDashboard();
  const { debts, loading: debtsLoading } = useDebts();
  const [tips, setTips] = useState<QuickTip[]>([]);
  const [events, setEvents] = useState<AnalyticsEvent[]>([]);

  // Fetch quick tips when stats and debts are available
  useEffect(() => {
    if (!stats || debtsLoading) return;

    const context = {
      total_debt: stats.total_debt,
      total_income: stats.total_income,
      total_expenses: stats.total_expenses,
      debt_count: stats.debt_count,
      highest_rate_debt:
        debts.length > 0
          ? debts.reduce((a, b) =>
              parseFloat(a.interest_rate || "0") > parseFloat(b.interest_rate || "0") ? a : b,
            ).name
          : "N/A",
      debt_to_income_ratio:
        parseFloat(stats.total_income) > 0
          ? (parseFloat(stats.total_debt) / parseFloat(stats.total_income)).toFixed(2)
          : "0",
    };

    api
      .post<QuickTip[]>("/ai-advisor/quick-tips", context)
      .then(({ data }) => setTips(data))
      .catch(() => setTips(FALLBACK_TIPS));
  }, [stats, debts, debtsLoading]);

  // Fetch recent activity events
  useEffect(() => {
    api
      .get<AnalyticsEvent[]>("/analytics/events", { params: { limit: 5 } })
      .then(({ data }) => setEvents(data))
      .catch(() => setEvents([]));
  }, []);

  // ─── Loading State ───────────────────────────────────────────────────────────

  if (statsLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  // ─── Error State ─────────────────────────────────────────────────────────────

  if (statsError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track your debt payoff progress and financial health.
          </p>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {statsError}
        </div>
      </div>
    );
  }

  if (!stats) return null;

  // ─── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Track your debt payoff progress and financial health.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {/* Total Debt */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                <DollarSign className="h-5 w-5 text-primary-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(parseFloat(stats.total_debt))}
              </p>
              <p className="text-sm text-gray-500">Total Debt</p>
            </div>
          </div>
        </Card>

        {/* Income This Month */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-100">
                <Wallet className="h-5 w-5 text-success-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(parseFloat(stats.total_income))}
              </p>
              <p className="text-sm text-gray-500">Income This Month</p>
            </div>
          </div>
        </Card>

        {/* Monthly Payment */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                <CreditCard className="h-5 w-5 text-primary-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(parseFloat(stats.monthly_payment))}
              </p>
              <p className="text-sm text-gray-500">Monthly Payment</p>
            </div>
          </div>
        </Card>

        {/* Payoff Progress */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                <TrendingUp className="h-5 w-5 text-primary-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold text-gray-900">
                {parseFloat(stats.debt_free_progress_pct).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-500">Payoff Progress</p>
            </div>
          </div>
        </Card>

        {/* Debt-Free Date */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                <Calendar className="h-5 w-5 text-primary-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold text-gray-900">
                {stats.estimated_payoff_date
                  ? formatDate(stats.estimated_payoff_date, "MMM yyyy")
                  : "N/A"}
              </p>
              <p className="text-sm text-gray-500">Debt-Free Date</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Debt Payoff Chart - spans 2 columns */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-gray-900">Debt Payoff Chart</h2>
            </CardHeader>
            <CardBody>
              <div className="flex h-64 items-center justify-center">
                <div className="text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
                    <TrendingUp className="h-6 w-6 text-primary-600" />
                  </div>
                  <p className="mt-3 text-sm font-medium text-gray-900">Debt Payoff Chart</p>
                  <p className="mt-1 text-sm text-gray-500">
                    Add your debts to see your payoff projection here.
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Payoff Progress */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900">Payoff Progress</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {debts.length === 0 && (
                <p className="text-sm text-gray-500">No debts added yet.</p>
              )}
              {debts.map((debt) => {
                const principal = parseFloat(debt.principal_amount || "0");
                const current = parseFloat(debt.current_balance || "0");
                const progress =
                  principal > 0 ? Math.round(((principal - current) / principal) * 100) : 0;

                return (
                  <div key={debt.id}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-gray-700">{debt.name}</span>
                      <span className="text-gray-500">
                        {formatCurrency(parseFloat(debt.current_balance))} remaining
                      </span>
                    </div>
                    <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full bg-primary-600 transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Quick Tips */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900">Quick Tips</h2>
          </CardHeader>
          <CardBody>
            <ul className="space-y-3">
              {tips.length === 0 && (
                <li className="text-sm text-gray-500">Loading tips...</li>
              )}
              {tips.map((tip, i) => (
                <li key={i} className="flex gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-warning-100">
                    <Lightbulb className="h-3.5 w-3.5 text-warning-600" />
                  </div>
                  <p className="text-sm text-gray-600">{tip.tip}</p>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
          </CardHeader>
          <CardBody>
            {events.length === 0 ? (
              <p className="text-sm text-gray-500">No recent activity yet.</p>
            ) : (
              <ul className="space-y-4">
                {events.map((event, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-100">
                      <Activity className="h-3.5 w-3.5 text-primary-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {capitalize(event.event_type.replace(/_/g, " "))}
                      </p>
                    </div>
                    <span className="shrink-0 text-xs text-gray-400">
                      {formatRelativeTime(event.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
