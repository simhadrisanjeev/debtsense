"use client";

import { Card } from "@/components/ui/Card";
import {
  DollarSign,
  TrendingDown,
  Calendar,
  Lightbulb,
  CreditCard,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

function StatCard({
  title,
  value,
  change,
  changeType,
  icon: Icon,
}: {
  title: string;
  value: string;
  change: string;
  changeType: "positive" | "negative" | "neutral";
  icon: React.ElementType;
}) {
  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
            <Icon className="h-5 w-5 text-primary-600" />
          </div>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${
              changeType === "positive"
                ? "bg-success-100 text-success-700"
                : changeType === "negative"
                  ? "bg-danger-100 text-danger-700"
                  : "bg-gray-100 text-gray-600"
            }`}
          >
            {changeType === "positive" ? (
              <ArrowUpRight className="h-3 w-3" />
            ) : changeType === "negative" ? (
              <ArrowDownRight className="h-3 w-3" />
            ) : null}
            {change}
          </span>
        </div>
        <div className="mt-4">
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{title}</p>
        </div>
      </div>
    </Card>
  );
}

export default function DashboardPage() {
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
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Debt"
          value="$24,500"
          change="- $1,200"
          changeType="positive"
          icon={DollarSign}
        />
        <StatCard
          title="Monthly Payment"
          value="$1,850"
          change="On track"
          changeType="neutral"
          icon={CreditCard}
        />
        <StatCard
          title="Interest Saved"
          value="$3,240"
          change="+$180"
          changeType="positive"
          icon={TrendingDown}
        />
        <StatCard
          title="Debt-Free Date"
          value="Mar 2027"
          change="2 mo. faster"
          changeType="positive"
          icon={Calendar}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Debt Overview - spans 2 columns */}
        <div className="lg:col-span-2">
          <Card>
            <div className="border-b border-gray-200 px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Debt Overview
              </h2>
            </div>
            <div className="flex h-64 items-center justify-center p-6">
              <div className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
                  <TrendingDown className="h-6 w-6 text-primary-600" />
                </div>
                <p className="mt-3 text-sm font-medium text-gray-900">
                  Debt Payoff Chart
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Add your debts to see your payoff projection here.
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Payoff Progress */}
        <Card>
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Payoff Progress
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {[
                { name: "Credit Card", progress: 65, amount: "$2,800" },
                { name: "Student Loan", progress: 30, amount: "$12,400" },
                { name: "Car Loan", progress: 45, amount: "$9,300" },
              ].map((debt) => (
                <div key={debt.name}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-gray-700">
                      {debt.name}
                    </span>
                    <span className="text-gray-500">{debt.amount}</span>
                  </div>
                  <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-primary-500 transition-all"
                      style={{ width: `${debt.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Quick Tips */}
        <Card>
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Quick Tips
            </h2>
          </div>
          <div className="p-6">
            <ul className="space-y-3">
              {[
                "Consider switching to the avalanche method to save $420 in interest.",
                "You have $200 in unused budget that could go toward extra payments.",
                "Your credit card rate is high \u2014 look into balance transfer options.",
              ].map((tip, i) => (
                <li key={i} className="flex gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-warning-100">
                    <Lightbulb className="h-3.5 w-3.5 text-warning-600" />
                  </div>
                  <p className="text-sm text-gray-600">{tip}</p>
                </li>
              ))}
            </ul>
          </div>
        </Card>

        {/* Recent Activity */}
        <Card>
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Recent Activity
            </h2>
          </div>
          <div className="p-6">
            <ul className="space-y-4">
              {[
                {
                  action: "Payment made",
                  detail: "Credit Card - $450",
                  time: "2 hours ago",
                },
                {
                  action: "Strategy updated",
                  detail: "Switched to Avalanche method",
                  time: "1 day ago",
                },
                {
                  action: "New debt added",
                  detail: "Medical Bill - $1,200",
                  time: "3 days ago",
                },
                {
                  action: "AI Advisor tip",
                  detail: "Refinance recommendation reviewed",
                  time: "5 days ago",
                },
              ].map((activity, i) => (
                <li key={i} className="flex items-start gap-3">
                  <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary-400" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {activity.action}
                    </p>
                    <p className="text-sm text-gray-500">{activity.detail}</p>
                  </div>
                  <span className="shrink-0 text-xs text-gray-400">
                    {activity.time}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      </div>
    </div>
  );
}
