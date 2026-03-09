"""AI advisor service — orchestrates LLM calls with user context."""

from __future__ import annotations

import json
from decimal import Decimal

import structlog

from app.core.config import settings
from app.modules.ai_advisor.llm_client import get_llm_client, LLMError
from app.modules.ai_advisor.prompts import SYSTEM_PROMPT, QUICK_TIPS_PROMPT, build_context_prompt
from app.modules.ai_advisor.schemas import (
    AdvisorContext,
    AdvisorRequest,
    AdvisorResponse,
    QuickTip,
    QuickTipsResponse,
)

logger = structlog.get_logger()

_PLACEHOLDER_KEYS = {"your-llm-api-key", "your-fallback-key", "your-api-key", "sk-xxx", ""}


def _has_valid_api_key() -> bool:
    """Check if a real (non-placeholder) LLM API key is configured."""
    if settings.LLM_PROVIDER == "local":
        return True
    return bool(settings.LLM_API_KEY) and settings.LLM_API_KEY not in _PLACEHOLDER_KEYS


class AIAdvisorService:
    @staticmethod
    async def get_advice(request: AdvisorRequest) -> AdvisorResponse:
        """Get AI-powered financial advice."""
        # Skip LLM call entirely when no valid API key is configured
        if not _has_valid_api_key():
            logger.info("ai_advisor.no_api_key", provider=settings.LLM_PROVIDER)
            return AdvisorResponse(
                advice="AI advisor is not configured yet. Please set up an LLM API key (OpenAI or Anthropic) in the environment to enable AI-powered advice. In the meantime, check out the Strategies page for debt payoff comparisons.",
                suggestions=["Review your debt payoff strategies", "Try the snowball or avalanche method", "Set up a monthly budget"],
                risk_level=_assess_risk(request.context) if request.context else "unknown",
                disclaimer="This is educational guidance, not professional financial advice. Consult a certified financial planner for personalised recommendations.",
            )

        client = get_llm_client()

        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Inject financial context if provided
        if request.context:
            context_text = build_context_prompt(request.context)
            messages.append({"role": "system", "content": context_text})

        # Append conversation history
        for entry in request.conversation_history:
            messages.append(entry)

        messages.append({"role": "user", "content": request.question})

        try:
            raw_response = await client.complete(messages)
        except LLMError:
            logger.exception("ai_advisor.llm_failed")
            return AdvisorResponse(
                advice="I'm sorry, I'm temporarily unable to provide advice. Please try again later.",
                suggestions=["Try rephrasing your question", "Check back in a few minutes"],
                risk_level="unknown",
                disclaimer="This is educational guidance, not professional financial advice. Consult a certified financial planner for personalised recommendations.",
            )

        # Parse the response into structured output
        return AdvisorResponse(
            advice=raw_response,
            suggestions=_extract_suggestions(raw_response),
            risk_level=_assess_risk(request.context) if request.context else "unknown",
            disclaimer="This is educational guidance, not professional financial advice. Consult a certified financial planner for personalised recommendations.",
        )

    @staticmethod
    async def get_quick_tips(context: AdvisorContext) -> QuickTipsResponse:
        """Generate personalized quick tips based on financial profile."""
        # Skip LLM call entirely when no valid API key is configured
        if not _has_valid_api_key():
            logger.info("ai_advisor.quick_tips.no_api_key", provider=settings.LLM_PROVIDER)
            return QuickTipsResponse(tips=[
                QuickTip(tip="Focus on paying off your highest-interest debt first", category="strategy", priority=1),
                QuickTip(tip="Review your subscriptions for any you can cancel", category="budgeting", priority=2),
                QuickTip(tip="Build a small emergency fund to avoid new debt", category="savings", priority=3),
            ])

        client = get_llm_client()
        context_text = build_context_prompt(context)
        prompt = QUICK_TIPS_PROMPT.format(context=context_text)

        messages = [
            {"role": "system", "content": "You are a helpful financial advisor. Respond only with valid JSON."},
            {"role": "user", "content": prompt},
        ]

        try:
            raw = await client.complete(messages)
            tips_data = json.loads(raw)
            tips = [QuickTip(**t) for t in tips_data]
        except (LLMError, json.JSONDecodeError, TypeError):
            logger.exception("ai_advisor.quick_tips_failed")
            tips = [
                QuickTip(tip="Focus on paying off your highest-interest debt first", category="strategy", priority=1),
                QuickTip(tip="Review your subscriptions for any you can cancel", category="budgeting", priority=2),
                QuickTip(tip="Build a small emergency fund to avoid new debt", category="savings", priority=3),
            ]

        return QuickTipsResponse(tips=tips)


def _extract_suggestions(text: str) -> list[str]:
    """Extract actionable suggestions from LLM response text."""
    suggestions: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and (stripped.startswith(("- ", "• ", "* ")) or (stripped[:2].rstrip(".").isdigit())):
            clean = stripped.lstrip("-•* 0123456789.)")
            if clean:
                suggestions.append(clean.strip())
    return suggestions[:5]


def _assess_risk(context: AdvisorContext) -> str:
    """Assess financial risk level based on user context."""
    dti = float(context.debt_to_income_ratio)
    if dti > 0.5:
        return "high"
    if dti > 0.3:
        return "medium"
    return "low"
