"""
FastAPI router for debt CRUD, payment overrides, and schedule endpoints.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.modules.debts.schemas import (
    DebtCreate,
    DebtResponse,
    DebtSummary,
    DebtUpdate,
    PaymentOverrideCreate,
    PaymentOverrideResponse,
    PaymentOverrideUpdate,
    PaymentScheduleResponse,
)
from app.modules.debts.service import DebtService

router = APIRouter()


def _service(db: DbSession) -> DebtService:
    return DebtService(db)


# ---------------------------------------------------------------------------
# Debt CRUD
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[DebtResponse],
    summary="List debts",
)
async def list_debts(
    db: DbSession,
    current_user: CurrentUser,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True),
) -> list[DebtResponse]:
    service = _service(db)
    debts = await service.list_debts(
        current_user.id, offset=offset, limit=limit, active_only=active_only,
    )
    return [DebtResponse.model_validate(d) for d in debts]


@router.post(
    "/",
    response_model=DebtResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a debt",
)
async def create_debt(
    payload: DebtCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> DebtResponse:
    service = _service(db)
    debt = await service.create(current_user.id, payload)
    return DebtResponse.model_validate(debt)


@router.get(
    "/summary",
    response_model=DebtSummary,
    summary="Get debt summary",
)
async def get_debt_summary(
    db: DbSession,
    current_user: CurrentUser,
) -> DebtSummary:
    service = _service(db)
    return await service.get_summary(current_user.id)


@router.get(
    "/{debt_id}",
    response_model=DebtResponse,
    summary="Get a single debt",
)
async def get_debt(
    debt_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> DebtResponse:
    service = _service(db)
    debt = await service.get_by_id(debt_id, current_user.id)
    return DebtResponse.model_validate(debt)


@router.patch(
    "/{debt_id}",
    response_model=DebtResponse,
    summary="Update a debt",
)
async def update_debt(
    debt_id: uuid.UUID,
    payload: DebtUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> DebtResponse:
    service = _service(db)
    debt = await service.update(debt_id, current_user.id, payload)
    return DebtResponse.model_validate(debt)


@router.delete(
    "/{debt_id}",
    response_model=DebtResponse,
    summary="Soft-delete a debt",
)
async def delete_debt(
    debt_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> DebtResponse:
    service = _service(db)
    debt = await service.delete(debt_id, current_user.id)
    return DebtResponse.model_validate(debt)


# ---------------------------------------------------------------------------
# Payment Overrides
# ---------------------------------------------------------------------------

@router.get(
    "/{debt_id}/payment-overrides",
    response_model=list[PaymentOverrideResponse],
    summary="List payment overrides for a debt",
)
async def list_payment_overrides(
    debt_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[PaymentOverrideResponse]:
    service = _service(db)
    overrides = await service.list_overrides(debt_id, current_user.id)
    return [PaymentOverrideResponse.model_validate(o) for o in overrides]


@router.post(
    "/{debt_id}/payment-overrides",
    response_model=PaymentOverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payment override",
)
async def create_payment_override(
    debt_id: uuid.UUID,
    payload: PaymentOverrideCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> PaymentOverrideResponse:
    service = _service(db)
    override = await service.create_override(debt_id, current_user.id, payload)
    return PaymentOverrideResponse.model_validate(override)


@router.put(
    "/payment-overrides/{override_id}",
    response_model=PaymentOverrideResponse,
    summary="Update a payment override",
)
async def update_payment_override(
    override_id: uuid.UUID,
    payload: PaymentOverrideUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> PaymentOverrideResponse:
    service = _service(db)
    override = await service.update_override(override_id, current_user.id, payload)
    return PaymentOverrideResponse.model_validate(override)


@router.delete(
    "/payment-overrides/{override_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a payment override",
)
async def delete_payment_override(
    override_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    service = _service(db)
    await service.delete_override(override_id, current_user.id)


# ---------------------------------------------------------------------------
# Payment Schedule
# ---------------------------------------------------------------------------

@router.get(
    "/{debt_id}/schedule",
    response_model=PaymentScheduleResponse,
    summary="Generate projected payment schedule",
)
async def get_payment_schedule(
    debt_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    months: int = Query(60, ge=1, le=360),
) -> PaymentScheduleResponse:
    service = _service(db)
    return await service.generate_payment_schedule(
        debt_id, current_user.id, months=months,
    )
