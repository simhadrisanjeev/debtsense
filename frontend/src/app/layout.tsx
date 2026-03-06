import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/providers/QueryProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "DebtSense \u2014 AI-Powered Debt Freedom",
  description:
    "Take control of your finances with AI-driven debt payoff strategies, personalized advice, and real-time progress tracking.",
  keywords: [
    "debt payoff",
    "financial planning",
    "AI advisor",
    "debt freedom",
    "budgeting",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-gray-50 font-sans antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
