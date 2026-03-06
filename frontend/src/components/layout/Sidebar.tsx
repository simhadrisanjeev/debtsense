"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  CreditCard,
  Wallet,
  Receipt,
  GitCompareArrows,
  Brain,
  Settings,
  TrendingUp,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/debts", label: "Debts", icon: CreditCard },
  { href: "/dashboard/income", label: "Income", icon: Wallet },
  { href: "/dashboard/expenses", label: "Expenses", icon: Receipt },
  { href: "/dashboard/strategies", label: "Strategies", icon: GitCompareArrows },
  { href: "/dashboard/advisor", label: "AI Advisor", icon: Brain },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 border-r border-gray-200 bg-white lg:block">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
            <TrendingUp className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold text-gray-900">DebtSense</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary-50 text-primary-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                )}
              >
                <Icon
                  className={cn(
                    "h-5 w-5 shrink-0",
                    isActive ? "text-primary-600" : "text-gray-400",
                  )}
                />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4">
          <div className="rounded-lg bg-primary-50 p-3">
            <p className="text-xs font-medium text-primary-800">
              Need help?
            </p>
            <p className="mt-1 text-xs text-primary-600">
              Ask our AI Advisor for personalized debt strategies.
            </p>
            <Link
              href="/dashboard/advisor"
              className="mt-2 inline-flex items-center text-xs font-medium text-primary-700 hover:text-primary-800"
            >
              Get Advice &rarr;
            </Link>
          </div>
        </div>
      </div>
    </aside>
  );
}
