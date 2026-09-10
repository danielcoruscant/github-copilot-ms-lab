import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import get_settings
from app.core.errors import (
    conflict_handler,
    conflict_handlers,
    handle_unexpected,
    handle_validation,
    invalid_handler,
    not_found_handler,
)
from app.core.logging import configure_logging
from app.funcionarios.application.services import FuncionarioService
from app.funcionarios.domain.exceptions import (
    EmployeeNotFoundError,
    InvalidEmployeeError,
)
from app.funcionarios.infrastructure.idempotency import MongoIdempotencyKeyStore
from app.funcionarios.infrastructure.mongo_client import MongoClientProvider
from app.funcionarios.infrastructure.repositories import FuncionarioMongoRepository
from app.funcionarios.interfaces.http.routes import router as funcionario_router
from app.health.routes import router as health_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    provider = MongoClientProvider(settings)
    await provider.connect()
    application.state.mongo_provider = provider
    repository = FuncionarioMongoRepository(provider)
    idempotency_store = MongoIdempotencyKeyStore(provider, settings)
    application.state.funcionario_service = FuncionarioService(repository, idempotency_store)
    try:
        await repository.ensure_indexes()
        await idempotency_store.ensure_indexes()
    except Exception:
        import logging

        logging.getLogger(__name__).warning(
            "MongoDB indexes could not be initialized; readiness will remain unavailable"
        )
    try:
        yield
    finally:
        await provider.close()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.include_router(health_router)
    application.include_router(funcionario_router)
    application.add_middleware(CorrelationIdMiddleware)
    _register_exception_handlers(application)
    return application


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        from time import perf_counter

        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            logging.getLogger(__name__).exception(
                "Unhandled request exception",
                extra={
                    "correlation_id": request.state.correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                },
            )
            raise
        finally:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            logging.getLogger(__name__).info(
                "HTTP request completed",
                extra={
                    "correlation_id": request.state.correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        return response


def _register_exception_handlers(application: FastAPI) -> None:
    application.add_exception_handler(RequestValidationError, handle_validation)
    application.add_exception_handler(Exception, handle_unexpected)
    for exception_class in conflict_handlers():
        application.add_exception_handler(exception_class, conflict_handler)
    application.add_exception_handler(EmployeeNotFoundError, not_found_handler)
    application.add_exception_handler(InvalidEmployeeError, invalid_handler)


app = create_app()
