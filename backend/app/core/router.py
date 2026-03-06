"""
Central API router — mounts all module routers.
"""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.debts.router import router as debts_router
from app.modules.income.router import router as income_router
from app.modules.expenses.router import router as expenses_router
from app.modules.financial_engine.router import router as financial_engine_router
from app.modules.simulation_engine.router import router as simulation_router
from app.modules.ai_advisor.router import router as ai_advisor_router
from app.modules.analytics.router import router as analytics_router
from app.modules.notifications.router import router as notifications_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(debts_router, prefix="/debts", tags=["debts"])
api_router.include_router(income_router, prefix="/income", tags=["income"])
api_router.include_router(expenses_router, prefix="/expenses", tags=["expenses"])
api_router.include_router(financial_engine_router, prefix="/financial-engine", tags=["financial-engine"])
api_router.include_router(simulation_router, prefix="/simulations", tags=["simulations"])
api_router.include_router(ai_advisor_router, prefix="/ai-advisor", tags=["ai-advisor"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
