"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Bot, User, Send, Loader2, Lightbulb, AlertTriangle } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "advisor";
  content: string;
  timestamp: string;
  suggestions?: string[];
}

interface DashboardStatsData {
  total_debt: string;
  total_income: string;
  total_expenses: string;
  debt_count: number;
  monthly_payment: string;
  estimated_payoff_date: string | null;
  debt_free_progress_pct: string;
}

interface DebtItem {
  name: string;
  interest_rate: string;
}

interface AdvisorResponseData {
  advice: string;
  suggestions: string[];
  risk_level: string;
  disclaimer: string;
}

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "advisor",
  content:
    "Hello! I'm your AI Financial Advisor. I can help you with debt payoff strategies, budgeting tips, and personalized financial guidance. What would you like to know?",
  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
};

const SUGGESTED_QUESTIONS = [
  "How can I pay off debt faster?",
  "Which debt should I pay first?",
  "What's the best strategy for me?",
  "How much should I budget for savings?",
];

export default function AdvisorPage() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<
    Array<{ role: string; content: string }>
  >([]);
  const [stats, setStats] = useState<DashboardStatsData | null>(null);
  const [debts, setDebts] = useState<DebtItem[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .get<DashboardStatsData>("/analytics/dashboard")
      .then(({ data }) => setStats(data))
      .catch(() => {});
    api
      .get<DebtItem[]>("/debts/")
      .then(({ data }) => setDebts(data))
      .catch(() => {});
  }, []);

  const buildContext = useCallback(() => {
    if (!stats) return undefined;
    return {
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
  }, [stats, debts]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isTyping) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const { data } = await api.post<AdvisorResponseData>("/ai-advisor/ask", {
        question: text.trim(),
        context: buildContext(),
        conversation_history: conversationHistory,
      }, { timeout: 120_000 });

      const advisorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "advisor",
        content: data.advice,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        suggestions: data.suggestions.length > 0 ? data.suggestions : undefined,
      };
      setMessages((prev) => [...prev, advisorMsg]);
      setConversationHistory((prev) => [
        ...prev,
        { role: "user", content: text.trim() },
        { role: "assistant", content: data.advice },
      ]);
    } catch {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "advisor",
        content: "I'm sorry, I encountered an error. Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      {/* Page Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">AI Financial Advisor</h1>
        <p className="mt-1 text-sm text-gray-500">
          Get personalized financial advice powered by AI
        </p>
      </div>

      {/* Chat Interface */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        {/* Messages Area */}
        <CardBody className="flex-1 overflow-y-auto space-y-4 p-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  message.role === "advisor" ? "bg-primary-100" : "bg-gray-200"
                }`}
              >
                {message.role === "advisor" ? (
                  <Bot className="h-4 w-4 text-primary-600" />
                ) : (
                  <User className="h-4 w-4 text-gray-600" />
                )}
              </div>
              <div
                className={`max-w-[70%] ${
                  message.role === "user" ? "ml-auto" : ""
                }`}
              >
                <div
                  className={`rounded-lg p-4 ${
                    message.role === "advisor"
                      ? "bg-gray-100 text-gray-800"
                      : "bg-primary-600 text-white"
                  }`}
                >
                  <p className="whitespace-pre-line text-sm">{message.content}</p>
                </div>
                {message.suggestions && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {message.suggestions.map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => sendMessage(suggestion)}
                        disabled={isTyping}
                        className="bg-primary-50 rounded-full px-3 py-1 text-xs font-medium text-primary-700 hover:bg-primary-100 transition-colors disabled:opacity-50"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-400 mt-1">{message.timestamp}</p>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-100">
                <Bot className="h-4 w-4 text-primary-600" />
              </div>
              <div className="rounded-lg bg-gray-100 p-4">
                <div className="flex items-center gap-1">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                    style={{ animationDelay: "0.1s" }}
                  />
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                    style={{ animationDelay: "0.2s" }}
                  />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardBody>

        {/* Bottom Area */}
        <div className="border-t border-gray-200 p-4">
          {/* Suggested Questions */}
          <div className="flex flex-wrap gap-2 mb-3">
            {SUGGESTED_QUESTIONS.map((question) => (
              <button
                key={question}
                onClick={() => sendMessage(question)}
                disabled={isTyping}
                className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors disabled:opacity-50"
              >
                {question}
              </button>
            ))}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Ask your financial advisor..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isTyping}
            />
            <Button type="submit" disabled={!input.trim() || isTyping}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>

      {/* Disclaimer */}
      <div className="mt-4 flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 p-3">
        <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-700">
          AI advice is for educational purposes only. Consult a licensed financial professional
          before making important financial decisions.
        </p>
      </div>
    </div>
  );
}
