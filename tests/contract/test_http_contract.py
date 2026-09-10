from datetime import date
from uuid import UUID

import httpx
import pytest

from app.funcionarios.application.commands import (
    CreateFuncionarioCommand,
    UpdateFuncionarioCommand,
)
from app.funcionarios.application.queries import FuncionarioFilters, FuncionarioPage, Pagination
from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.exceptions import (
    EmployeeNotFoundError,
    StaleEmployeeVersionError,
)
from app.funcionarios.domain.repositories import RepositoryPage
from app.funcionarios.interfaces.http.dependencies import get_funcionario_service
from app.main import create_app


class FakeHttpService:
    def __init__(self) -> None:
        self.employee = Funcionario.create(
            "Ada Lovelace", "ada@example.com", "Engenheira", date(2026, 1, 15)
        )

    async def create(self, command: CreateFuncionarioCommand, key: str) -> Funcionario:
        return self.employee

    async def list(self, filters: FuncionarioFilters, pagination: Pagination) -> RepositoryPage:
        return FuncionarioPage((self.employee,), pagination.page, pagination.page_size, 1)

    async def get(self, employee_id: UUID) -> Funcionario:
        if employee_id != self.employee.id:
            raise EmployeeNotFoundError("employee not found")
        return self.employee

    async def update(self, command: UpdateFuncionarioCommand) -> Funcionario:
        if command.expected_version != self.employee.version:
            raise StaleEmployeeVersionError("employee version is stale")
        return self.employee.update_allowed_fields(
            expected_version=command.expected_version,
            nome_completo=command.nome_completo,
            cargo=command.cargo,
            telefone=command.telefone,
            departamento=command.departamento,
            ativo=command.ativo,
        )

    async def delete(self, employee_id: UUID) -> None:
        if employee_id != self.employee.id:
            raise EmployeeNotFoundError("employee not found")


@pytest.fixture
async def client() -> httpx.AsyncClient:
    app = create_app()
    service = FakeHttpService()
    app.dependency_overrides[get_funcionario_service] = lambda: service
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_post_requires_idempotency_key(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/funcionarios",
        json={
            "nome_completo": "Ada",
            "email": "ada@example.com",
            "cargo": "Engenheira",
            "data_admissao": "2026-01-15",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_returns_employee_and_accepts_idempotency_key(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/funcionarios",
        headers={"Idempotency-Key": "http-1"},
        json={
            "nome_completo": "Ada",
            "email": "ada@example.com",
            "cargo": "Engenheira",
            "data_admissao": "2026-01-15",
        },
    )

    assert response.status_code == 201
    assert response.json()["version"] == 1
    assert response.json()["email"] == "ada@example.com"


@pytest.mark.asyncio
async def test_list_get_patch_delete_and_openapi(client: httpx.AsyncClient) -> None:
    listed = await client.get("/funcionarios?departamento=Tecnologia&page=1&page_size=10")
    employee_id = listed.json()["items"][0]["id"]
    fetched = await client.get(f"/funcionarios/{employee_id}")
    updated = await client.patch(
        f"/funcionarios/{employee_id}",
        json={"cargo": "Staff Engineer", "version": 1},
    )
    deleted = await client.delete(f"/funcionarios/{employee_id}")
    openapi = await client.get("/openapi.json")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert fetched.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert deleted.status_code == 204
    assert "Idempotency-Key" in str(openapi.json())
    assert "/funcionarios" in openapi.json()["paths"]


@pytest.mark.asyncio
async def test_update_rejects_forbidden_fields_and_stale_version(
    client: httpx.AsyncClient,
) -> None:
    listed = await client.get("/funcionarios")
    employee_id = listed.json()["items"][0]["id"]
    forbidden = await client.patch(
        f"/funcionarios/{employee_id}",
        json={"email": "other@example.com", "version": 1},
    )
    stale = await client.patch(
        f"/funcionarios/{employee_id}",
        json={"cargo": "Staff Engineer", "version": 2},
    )

    assert forbidden.status_code == 422
    assert stale.status_code == 409
