"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useDebts } from "@/hooks/useDebts";
import api from "@/lib/api";
import { Card, CardHeader, CardBody, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { formatCurrency, capitalize } from "@/lib/utils";
import {
  TrendingDown,
  Snowflake,
  Scale,
  Loader2,
  AlertCircle,
  Star,
  ArrowRight,
} from "lucide-react";

// ─── Interfaces ──────────────────────────────────────────────────────────────

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

interface SimResultItem {
  scenario_type: string;
  description: string;
  original_payoff_months: number;
  new_payoff_months: number;
  original_total_interest: string;
  new_total_interest: string;
  monthly_savings: string;
  total_savings: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const STRATEGY_ICONS: Record<string, React.ElementType> = {
  avalanche: TrendingDown,
  snowball: Snowflake,
  hybrid: Scale,
};

function formatDebtFreeDate(yyyyMM: string): string {
  const [year, month] = yyyyMM.split("-");
  const monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];
  const idx = parseInt(month ?? "0", 10) - 1;
  return `${monthNames[idx] ?? month} ${year}`;
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function StrategiesPage() {
  const { debts, loading: debtsLoading } = useDebts();

  const [comparison, setComparison] = useState<StrategyComparisonResponse | null>(null);
  const [compLoading, setCompLoading] = useState(false);
  const [compError, setCompError] = useState<string | null>(null);
  const [extraPayment, setExtraPayment] = useState("0");
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);

  const [simResult, setSimResult] = useState<SimResultItem | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);

  // Build engine-format inputs from debts
  const debtInputs = debts.map((d) => ({
    name: d.name,
    balance: d.current_balance,
    interest_rate: d.interest_rate,
    minimum_payment: d.minimum_payment,
  }));

  // Fetch strategy comparison from the financial engine
  const fetchComparison = async () => {
    setCompLoading(true);
    setCompError(null);
    try {
      const { data } = await api.post<StrategyComparisonResponse>(
        "/financial-engine/compare",
        { debts: debtInputs, extra_payment: extraPayment },
      );
      setComparison(data);
      setSelectedStrategy(data.recommended);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to load strategy comparison";
      setCompError(message);
    } finally {
      setCompLoading(false);
    }
  };

  // Auto-fetch on mount when debts are available
  useEffect(() => {
    if (debts.length > 0) {
      fetchComparison();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debts]);

  // Run a what-if simulation
  const runSimulation = async (
    scenarioType: string,
    parameters: Record<string, string>,
  ) => {
    setSimLoading(true);
    setSimError(null);
    setSimResult(null);
    try {
      const { data } = await api.post<{ results: SimResultItem[] }>(
        "/simulations/run",
        {
          base_debts: debtInputs,
          base_extra_payment: extraPayment,
          scenarios: [{ scenario_type: scenarioType, parameters }],
        },
      );
      if (data.results && data.results.length > 0) {
        setSimResult(data.results[0] ?? null);
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Simulation failed";
      setSimError(message);
    } finally {
      setSimLoading(false);
    }
  };

  // ─── Loading state ──────────────────────────────────────────────────────────

  if (debtsLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  // ─── Empty state ────────────────────────────────────────────────────────────

  if (debts.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Payoff Strategies</h1>
          <p className="mt-1 text-sm text-gray-500">
            Compare different debt payoff approaches and find the best plan for you.
          </p>
        </div>

        <Card>
          <CardBody className="flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle className="h-12 w-12 text-gray-300" />
            <h3 className="mt-4 text-lg font-semibold text-gray-900">
              No debts to analyze
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Add your debts first to compare strategies.
            </p>
            <Link href="/dashboard/debts">
              <Button variant="primary" size="sm" className="mt-4">
                Go to Debts
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardBody>
        </Card>
      </div>
    );
  }

  // ─── Main content ───────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Payoff Strategies</h1>
        <p className="mt-1 text-sm text-gray-500">
          Compare different debt payoff approaches and find the best plan for you.
        </p>
      </div>

      {/* Extra Payment Input */}
      <Card>
        <CardBody>
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label
                htmlFor="extra-payment"
                className="block text-sm font-medium text-gray-700"
              >
                Extra Monthly Payment
              </label>
              <div className="relative mt-1">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                  $
                </span>
                <input
                  id="extra-payment"
                  type="number"
                  min="0"
                  step="50"
                  value={extraPayment}
                  onChange={(e) => setExtraPayment(e.target.value)}
                  className="block w-40 rounded-lg border border-gray-300 py-2 pl-7 pr-3 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
            </div>
            <Button
              variant="primary"
              size="md"
              onClick={fetchComparison}
              loading={compLoading}
            >
              Compare
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Error state */}
      {compError && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {compError}
        </div>
      )}

      {/* Comparison loading */}
      {compLoading && (
        <div className="flex min-h-[200px] items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
        </div>
      )}

      {/* Strategy Cards Grid */}
      {comparison && !compLoading && (
        <>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {comparison.strategies.map((strategy) => {
              const Icon = STRATEGY_ICONS[strategy.strategy] ?? Scale;
              const isRecommended = strategy.strategy === comparison.recommended;
              const isSelected = selectedStrategy === strategy.strategy;

              return (
                <Card
                  key={strategy.strategy}
                  className={`relative cursor-pointer transition-all hover:shadow-md ${
                    isSelected
                      ? "border-2 border-primary-600"
                      : "hover:border-gray-300"
                  }`}
                  onClick={() => setSelectedStrategy(strategy.strategy)}
                >
                  {isRecommended && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="inline-flex items-center gap-1 rounded-full bg-primary-600 px-3 py-1 text-xs font-medium text-white shadow-sm">
                        <Star className="h-3 w-3" />
                        Recommended
                      </span>
                    </div>
                  )}

                  <CardHeader className={isRecommended ? "pt-6" : ""}>
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                          isRecommended ? "bg-primary-100" : "bg-gray-100"
                        }`}
                      >
                        <Icon
                          className={`h-5 w-5 ${
                            isRecommended ? "text-primary-600" : "text-gray-600"
                          }`}
                        />
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {capitalize(strategy.strategy)}
                      </h3>
                    </div>
                  </CardHeader>

                  <CardBody>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">Debt-Free Date</span>
                        <span className="text-sm font-semibold text-gray-900">
                          {formatDebtFreeDate(strategy.debt_free_date)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">Total Interest</span>
                        <span className="text-sm font-semibold text-gray-900">
                          {formatCurrency(parseFloat(strategy.total_interest_paid))}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">Total Paid</span>
                        <span className="text-sm font-semibold text-gray-900">
                          {formatCurrency(parseFloat(strategy.total_paid))}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">Months to Freedom</span>
                        <span className="text-sm font-semibold text-gray-900">
                          {strategy.total_months}
                        </span>
                      </div>

                      <div className="border-t border-gray-100 pt-3">
                        <span className="text-xs font-medium text-gray-500">
                          Payoff Order
                        </span>
                        <p className="mt-1 text-sm text-gray-700">
                          {strategy.payoff_order.join(" \u2192 ")}
                        </p>
                      </div>
                    </div>
                  </CardBody>

                  <CardFooter>
                    <Button
                      variant={isSelected ? "primary" : "secondary"}
                      size="sm"
                      className="w-full"
                    >
                      {isSelected ? "Selected" : "Select Strategy"}
                    </Button>
                  </CardFooter>
                </Card>
              );
            })}
          </div>

          {/* Comparison Summary Table */}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-gray-900">
                Comparison Summary
              </h2>
            </CardHeader>
            <CardBody>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left text-gray-500">
                      <th className="pb-3 pr-6 font-medium">Strategy</th>
                      <th className="pb-3 pr-6 font-medium">Debt-Free Date</th>
                      <th className="pb-3 pr-6 font-medium">Total Interest</th>
                      <th className="pb-3 pr-6 font-medium">Total Paid</th>
                      <th className="pb-3 font-medium">Months</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {comparison.strategies.map((strategy) => {
                      const isRecommended =
                        strategy.strategy === comparison.recommended;
                      return (
                        <tr
                          key={strategy.strategy}
                          className={isRecommended ? "bg-primary-50" : ""}
                        >
                          <td className="py-3 pr-6">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900">
                                {capitalize(strategy.strategy)}
                              </span>
                              {isRecommended && (
                                <Star className="h-3.5 w-3.5 text-primary-500" />
                              )}
                            </div>
                          </td>
                          <td className="py-3 pr-6 text-gray-700">
                            {formatDebtFreeDate(strategy.debt_free_date)}
                          </td>
                          <td className="py-3 pr-6 text-gray-700">
                            {formatCurrency(parseFloat(strategy.total_interest_paid))}
                          </td>
                          <td className="py-3 pr-6 font-medium text-gray-900">
                            {formatCurrency(parseFloat(strategy.total_paid))}
                          </td>
                          <td className="py-3 text-gray-700">
                            {strategy.total_months}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>

          {/* Recommendation Callout */}
          <div className="rounded-lg bg-primary-50 p-4">
            <div className="flex items-start gap-3">
              <Star className="mt-0.5 h-5 w-5 shrink-0 text-primary-600" />
              <div>
                <p className="text-sm font-medium text-primary-900">
                  The {capitalize(comparison.recommended)} method saves you the most
                  money on interest.
                </p>
                <p className="mt-1 text-sm text-primary-700">
                  Interest saved vs. minimum payments:{" "}
                  <span className="font-semibold">
                    {formatCurrency(
                      parseFloat(comparison.interest_savings_vs_minimum),
                    )}
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* What-If Simulation Section */}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-gray-900">
                What-If Scenarios
              </h2>
            </CardHeader>
            <CardBody>
              <div className="flex flex-wrap gap-3">
                <Button
                  variant="secondary"
                  size="sm"
                  loading={simLoading}
                  onClick={() =>
                    runSimulation("extra_payment", { additional_payment: "100" })
                  }
                >
                  Extra $100/month
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  loading={simLoading}
                  onClick={() =>
                    runSimulation("extra_payment", { additional_payment: "500" })
                  }
                >
                  Extra $500/month
                </Button>
                {debts.length > 0 && (
                  <Button
                    variant="secondary"
                    size="sm"
                    loading={simLoading}
                    onClick={() => {
                      const firstName = debts[0]?.name;
                      if (firstName) {
                        runSimulation("lump_sum", {
                          debt_name: firstName,
                          amount: "1000",
                        });
                      }
                    }}
                  >
                    Lump Sum $1000
                  </Button>
                )}
              </div>

              {simError && (
                <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {simError}
                </div>
              )}

              {simResult && (
                <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <p className="text-sm font-medium text-gray-900">
                    {simResult.description}
                  </p>
                  <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <span className="text-xs font-medium text-gray-500">
                        Months Saved
                      </span>
                      <p className="mt-0.5 text-lg font-semibold text-primary-600">
                        {simResult.original_payoff_months -
                          simResult.new_payoff_months}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs font-medium text-gray-500">
                        Interest Saved
                      </span>
                      <p className="mt-0.5 text-lg font-semibold text-green-600">
                        {formatCurrency(parseFloat(simResult.total_savings))}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}
