"""AI advisor API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.modules.ai_advisor.schemas import (
    AdvisorRequest,
    AdvisorResponse,
    AdvisorContext,
    QuickTipsResponse,
)
from app.modules.ai_advisor.service import AIAdvisorService

router = APIRouter()


@router.post("/ask", response_model=AdvisorResponse)
async def ask_advisor(
    request: AdvisorRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AdvisorResponse:
    """Ask the AI advisor a financial question."""
    return await AIAdvisorService.get_advice(request)


@router.post("/quick-tips", response_model=QuickTipsResponse)
async def get_quick_tips(
    context: AdvisorContext,
    current_user: CurrentUser,
    db: DbSession,
) -> QuickTipsResponse:
    """Get personalized quick tips based on financial profile."""
    return await AIAdvisorService.get_quick_tips(context)
