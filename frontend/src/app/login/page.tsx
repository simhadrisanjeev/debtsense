"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { TrendingUp, Mail, Lock } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardBody } from "@/components/ui/Card";
import { authApi } from "@/lib/api";
import { setAuthTokens, setStoredUser } from "@/lib/auth";
import type { AxiosError } from "axios";
import type { ApiError } from "@/types";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { data } = await authApi.login({ email, password });

      setAuthTokens({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      });

      setStoredUser({
        id: data.user.id,
        email: data.user.email,
        first_name: data.user.first_name,
        last_name: data.user.last_name,
      });

      router.push("/dashboard");
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      setError(
        axiosError.response?.data?.detail ||
          "Invalid email or password. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {/* Logo & Heading */}
        <div className="flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-600">
            <TrendingUp className="h-7 w-7 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-gray-900">
            Sign in to DebtSense
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Welcome back! Enter your credentials to continue.
          </p>
        </div>

        {/* Login Card */}
        <Card>
          <CardBody className="space-y-6">
            {error && (
              <div className="rounded-lg border border-danger-200 bg-danger-50 px-4 py-3 text-sm text-danger-700">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="Email address"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                leftIcon={<Mail className="h-4 w-4" />}
                required
                autoComplete="email"
              />

              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                leftIcon={<Lock className="h-4 w-4" />}
                required
                autoComplete="current-password"
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={loading}
                className="w-full"
              >
                Sign In
              </Button>
            </form>
          </CardBody>
        </Card>

        {/* Register Link */}
        <p className="text-center text-sm text-gray-600">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-semibold text-primary-600 hover:text-primary-700 transition-colors"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
