"""
Application-wide exception definitions and handlers.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


class DebtSenseError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(DebtSenseError):
    def __init__(self, resource: str, resource_id: str | int):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            code="NOT_FOUND",
            status_code=404,
        )


class ConflictError(DebtSenseError):
    def __init__(self, message: str):
        super().__init__(message=message, code="CONFLICT", status_code=409)


class ValidationError(DebtSenseError):
    def __init__(self, message: str):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422)


class AuthenticationError(DebtSenseError):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401)


class AuthorizationError(DebtSenseError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


class RateLimitExceededError(DebtSenseError):
    def __init__(self) -> None:
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(DebtSenseError)
    async def debtsense_error_handler(_request: Request, exc: DebtSenseError) -> JSONResponse:
        logger.warning("application_error", code=exc.code, message=exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
        )
