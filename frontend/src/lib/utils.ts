import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow, parseISO } from "date-fns";

/**
 * Merge class names with Tailwind CSS conflict resolution.
 * Combines clsx (conditional classes) with tailwind-merge (deduplication).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as USD currency.
 *
 * @example formatCurrency(1234.5) => "$1,234.50"
 * @example formatCurrency(-500) => "-$500.00"
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format a decimal rate as a percentage string.
 *
 * @example formatPercent(0.195)  => "19.50%"
 * @example formatPercent(5.5)    => "5.50%"  (when already a percentage value)
 */
export function formatPercent(rate: number, alreadyPercent = true): string {
  const value = alreadyPercent ? rate : rate * 100;
  return `${value.toFixed(2)}%`;
}

/**
 * Format an ISO date string into a human-readable format.
 *
 * @example formatDate("2025-03-15T00:00:00Z")       => "Mar 15, 2025"
 * @example formatDate("2025-03-15", "MM/dd/yyyy")    => "03/15/2025"
 */
export function formatDate(
  date: string | Date,
  pattern: string = "MMM d, yyyy",
): string {
  const parsed = typeof date === "string" ? parseISO(date) : date;
  return format(parsed, pattern);
}

/**
 * Truncate a string to a maximum length with an ellipsis.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 1)}\u2026`;
}

/**
 * Capitalize the first letter of a string.
 */
export function capitalize(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Sleep for a given number of milliseconds. Useful for debouncing or testing.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Format a date string as a relative time (e.g. "2 hours ago").
 */
export function formatRelativeTime(dateStr: string): string {
  return formatDistanceToNow(parseISO(dateStr), { addSuffix: true });
}
