"""Tratamento padronizado de erros HTTP."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.funcionarios.application.idempotency import (
    IdempotencyKeyConflictError,
    IdempotencyKeyInProgressError,
)
from app.funcionarios.domain.exceptions import (
    ActiveEmployeeDeletionError,
    DuplicateEmployeeEmailError,
    StaleEmployeeVersionError,
)

logger = logging.getLogger(__name__)


def correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def error_response(request: Request, status_code: int, detail: str, code: str) -> JSONResponse:
    logger.warning(
        "HTTP request failed",
        extra={
            "correlation_id": correlation_id(request),
            "status_code": status_code,
            "error_code": code,
            "error_detail": detail,
        },
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "detail": detail,
            "correlation_id": correlation_id(request),
        },
        headers={"X-Correlation-ID": correlation_id(request)},
    )


async def handle_validation(request: Request, _: Exception) -> JSONResponse:
    return error_response(request, 422, "request validation failed", "validation_error")


def conflict_handlers() -> tuple[type[Exception], ...]:
    return (
        DuplicateEmployeeEmailError,
        IdempotencyKeyConflictError,
        IdempotencyKeyInProgressError,
        StaleEmployeeVersionError,
        ActiveEmployeeDeletionError,
    )


def not_found_handler(request: Request, exception: Exception) -> JSONResponse:
    return error_response(request, 404, str(exception), "not_found")


def conflict_handler(request: Request, exception: Exception) -> JSONResponse:
    return error_response(request, 409, str(exception), "conflict")


def invalid_handler(request: Request, exception: Exception) -> JSONResponse:
    return error_response(request, 422, str(exception), "domain_validation_error")


async def handle_unexpected(request: Request, exception: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled application exception",
        extra={"correlation_id": correlation_id(request), "status_code": 500},
    )
    return error_response(request, 500, "internal server error", "internal_error")
