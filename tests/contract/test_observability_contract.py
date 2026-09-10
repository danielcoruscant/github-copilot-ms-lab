from uuid import UUID

import httpx
import pytest

from app.funcionarios.application.commands import CreateFuncionarioCommand
from app.funcionarios.application.queries import FuncionarioFilters, FuncionarioPage, Pagination
from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.exceptions import EmployeeNotFoundError
from app.funcionarios.interfaces.http.dependencies import get_funcionario_service
from app.main import create_app


class ErrorService:
    async def create(self, command: CreateFuncionarioCommand, key: str) -> Funcionario:
        raise EmployeeNotFoundError("employee not found")

    async def list(self, filters: FuncionarioFilters, pagination: Pagination) -> FuncionarioPage:
        raise NotImplementedError

    async def get(self, employee_id: UUID) -> Funcionario:
        raise EmployeeNotFoundError("employee not found")

    async def update(self, command: object) -> Funcionario:
        raise NotImplementedError

    async def delete(self, employee_id: UUID) -> None:
        raise NotImplementedError


@pytest.fixture
async def client() -> httpx.AsyncClient:
    app = create_app()
    app.dependency_overrides[get_funcionario_service] = lambda: ErrorService()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_and_readiness_expose_distinct_states(
    client: httpx.AsyncClient,
) -> None:
    health = await client.get("/health", headers={"X-Correlation-ID": "trace-123"})
    readiness = await client.get("/ready")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert health.headers["X-Correlation-ID"] == "trace-123"
    assert readiness.status_code == 503
    assert readiness.json()["status"] == "not_ready"


@pytest.mark.asyncio
async def test_validation_error_contains_stable_error_contract(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/funcionarios",
        headers={"Idempotency-Key": "validation-1", "X-Correlation-ID": "trace-456"},
        json={"email": "invalid"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert response.json()["correlation_id"] == "trace-456"
    assert response.headers["X-Correlation-ID"] == "trace-456"


@pytest.mark.asyncio
async def test_domain_error_contains_stable_error_contract(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/funcionarios",
        headers={"Idempotency-Key": "error-1"},
        json={
            "nome_completo": "Ada",
            "email": "ada@example.com",
            "cargo": "Engenheira",
            "data_admissao": "2026-01-15",
        },
    )

    assert response.status_code == 404
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert response.json()["detail"] == "employee not found"
    assert UUID(response.json()["correlation_id"])
    assert response.headers["X-Correlation-ID"] == response.json()["correlation_id"]
