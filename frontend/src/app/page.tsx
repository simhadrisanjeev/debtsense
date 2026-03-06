import Link from "next/link";
import {
  ArrowRight,
  Brain,
  Calculator,
  TrendingUp,
  Shield,
  BarChart3,
  Sparkles,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Advisor",
    description:
      "Get personalized debt payoff recommendations powered by advanced AI that adapts to your unique financial situation.",
  },
  {
    icon: Calculator,
    title: "Strategy Calculator",
    description:
      "Compare avalanche, snowball, and hybrid strategies side-by-side to find the fastest path to debt freedom.",
  },
  {
    icon: TrendingUp,
    title: "Progress Tracking",
    description:
      "Visualize your debt payoff journey with interactive charts and milestone celebrations along the way.",
  },
  {
    icon: Shield,
    title: "Secure & Private",
    description:
      "Your financial data is encrypted and never shared. We take your privacy as seriously as your finances.",
  },
  {
    icon: BarChart3,
    title: "Smart Analytics",
    description:
      "Understand where your money goes with detailed breakdowns of spending, interest saved, and payoff timelines.",
  },
  {
    icon: Sparkles,
    title: "What-If Scenarios",
    description:
      "Simulate changes in income, expenses, or extra payments to see how they affect your debt-free date.",
  },
];

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">DebtSense</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-white">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-primary-50/30" />
        <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl lg:text-6xl">
              Your Path to{" "}
              <span className="gradient-text">Debt Freedom</span>
              <br />
              Starts Here
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600 sm:text-xl">
              DebtSense combines AI-powered insights with proven payoff
              strategies to help you eliminate debt faster, save more on
              interest, and achieve financial independence.
            </p>
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-primary-600/25 hover:bg-primary-700 transition-all hover:shadow-xl hover:shadow-primary-600/30"
              >
                Start Free Today
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-6 py-3 text-base font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Sign In
              </Link>
            </div>
          </div>

          {/* Stats */}
          <div className="mx-auto mt-20 grid max-w-4xl grid-cols-1 gap-8 sm:grid-cols-3">
            {[
              { value: "$12,400", label: "Avg. Interest Saved" },
              { value: "3.2 yrs", label: "Faster Debt Freedom" },
              { value: "10,000+", label: "Users Debt-Free" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold text-primary-600 sm:text-4xl">
                  {stat.value}
                </div>
                <div className="mt-1 text-sm text-gray-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-gray-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything You Need to Crush Your Debt
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Powerful tools and intelligent insights designed to accelerate your
              journey to financial freedom.
            </p>
          </div>
          <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                    <Icon className="h-5 w-5 text-primary-600" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-gray-900">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-gray-600">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 py-16">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Ready to Take Control of Your Finances?
          </h2>
          <p className="mt-4 text-lg text-primary-100">
            Join thousands of users who have already saved money and accelerated
            their path to being debt-free.
          </p>
          <Link
            href="/register"
            className="mt-8 inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-base font-semibold text-primary-600 shadow-lg hover:bg-gray-50 transition-colors"
          >
            Get Started for Free
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary-600">
                <TrendingUp className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold text-gray-900">DebtSense</span>
            </div>
            <p className="text-sm text-gray-500">
              &copy; {new Date().getFullYear()} DebtSense. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
