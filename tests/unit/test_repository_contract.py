from dataclasses import replace
from datetime import date
from uuid import UUID, uuid4

import pytest

from app.funcionarios.application.commands import CreateFuncionarioCommand
from app.funcionarios.application.queries import FuncionarioFilters, Pagination
from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.repositories import (
    FuncionarioRepository,
    RepositoryFilters,
    RepositoryPage,
    UpdateRequest,
    UpdateResult,
    UpdateStatus,
)
from app.funcionarios.domain.repositories import (
    Pagination as RepositoryPagination,
)


class FakeFuncionarioRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Funcionario] = {}

    async def create(self, funcionario: Funcionario) -> Funcionario:
        self.items[funcionario.id] = funcionario
        return funcionario

    async def get_by_id(self, funcionario_id: UUID) -> Funcionario | None:
        return self.items.get(funcionario_id)

    async def get_by_email(self, email: str) -> Funcionario | None:
        normalized = email.strip().lower()
        return next(
            (item for item in self.items.values() if item.email.value == normalized),
            None,
        )

    async def list(
        self, filters: RepositoryFilters, pagination: RepositoryPagination
    ) -> RepositoryPage:
        filtered = list(self.items.values())
        if filters.departamento is not None:
            filtered = [item for item in filtered if item.departamento == filters.departamento]
        if filters.cargo is not None:
            filtered = [item for item in filtered if item.cargo == filters.cargo]
        page_items = filtered[pagination.skip : pagination.skip + pagination.page_size]
        return RepositoryPage(
            items=tuple(page_items),
            page=pagination.page,
            page_size=pagination.page_size,
            total=len(filtered),
        )

    async def update_if_version_matches(self, request: UpdateRequest) -> UpdateResult:
        current = self.items.get(request.funcionario_id)
        if current is None:
            return UpdateResult(UpdateStatus.NOT_FOUND)
        if current.version != request.expected_version:
            return UpdateResult(UpdateStatus.VERSION_CONFLICT, current)
        updated = current.update_allowed_fields(
            expected_version=request.expected_version,
            nome_completo=request.nome_completo,
            cargo=request.cargo,
            telefone=request.telefone,
            departamento=request.departamento,
            ativo=request.ativo,
        )
        self.items[updated.id] = updated
        return UpdateResult(UpdateStatus.UPDATED, updated)

    async def delete_if_inactive(self, funcionario_id: UUID) -> bool:
        employee = self.items.get(funcionario_id)
        if employee is None or employee.ativo:
            return False
        del self.items[funcionario_id]
        return True


def make_command(index: int = 1, **overrides: object) -> CreateFuncionarioCommand:
    data: dict[str, object] = {
        "nome_completo": f"Funcionario {index}",
        "email": f"funcionario{index}@example.com",
        "cargo": "Engenheiro",
        "data_admissao": date(2026, 1, index),
        "departamento": "Tecnologia",
    }
    data.update(overrides)
    return CreateFuncionarioCommand(**data)  # type: ignore[arg-type]


def make_employee(command: CreateFuncionarioCommand) -> Funcionario:
    return Funcionario.create(
        nome_completo=command.nome_completo,
        email=command.email,
        cargo=command.cargo,
        data_admissao=command.data_admissao,
        telefone=command.telefone,
        departamento=command.departamento,
    )


def assert_repository_contract(repository: FuncionarioRepository) -> None:
    assert isinstance(repository, FuncionarioRepository)


@pytest.mark.asyncio
async def test_fake_implements_repository_contract() -> None:
    repository = FakeFuncionarioRepository()
    assert_repository_contract(repository)

    first = await repository.create(make_employee(make_command()))
    second = await repository.create(make_employee(make_command(2, cargo="Analista")))

    assert await repository.get_by_id(first.id) == first
    assert await repository.get_by_email(" FUNCIONARIO2@EXAMPLE.COM ") == second


@pytest.mark.asyncio
async def test_list_applies_filters_and_pagination() -> None:
    repository = FakeFuncionarioRepository()
    await repository.create(make_employee(make_command(1)))
    await repository.create(make_employee(make_command(2, departamento="Financeiro")))
    await repository.create(make_employee(make_command(3)))

    result = await repository.list(
        FuncionarioFilters(departamento="Tecnologia"), Pagination(page=1, page_size=1)
    )

    assert result.total == 2
    assert len(result.items) == 1
    assert result.items[0].departamento == "Tecnologia"


@pytest.mark.asyncio
async def test_update_distinguishes_missing_and_stale_versions() -> None:
    repository = FakeFuncionarioRepository()
    employee = await repository.create(make_employee(make_command()))

    missing = await repository.update_if_version_matches(
        UpdateRequest(uuid4(), expected_version=1, cargo="Arquiteto")
    )
    stale = await repository.update_if_version_matches(
        UpdateRequest(employee.id, expected_version=0, cargo="Arquiteto")
    )

    assert missing.status is UpdateStatus.NOT_FOUND
    assert stale.status is UpdateStatus.VERSION_CONFLICT
    assert stale.funcionario == employee


@pytest.mark.asyncio
async def test_update_and_delete_follow_repository_contract() -> None:
    repository = FakeFuncionarioRepository()
    employee = await repository.create(make_employee(make_command()))

    updated = await repository.update_if_version_matches(
        UpdateRequest(employee.id, expected_version=1, cargo="Staff Engineer")
    )
    assert updated.status is UpdateStatus.UPDATED
    assert updated.funcionario is not None
    assert updated.funcionario.version == 2
    assert await repository.delete_if_inactive(employee.id) is True
    assert await repository.get_by_id(employee.id) is None

    active = await repository.create(make_employee(make_command(2)))
    repository.items[active.id] = replace(active, ativo=True)
    assert await repository.delete_if_inactive(active.id) is False


def test_pagination_rejects_invalid_limits() -> None:
    with pytest.raises(ValueError):
        Pagination(page=0)
    with pytest.raises(ValueError):
        Pagination(page_size=101)
