from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

import pytest

from app.funcionarios.application.commands import (
    CreateFuncionarioCommand,
    UpdateFuncionarioCommand,
)
from app.funcionarios.application.idempotency import (
    IdempotencyKeyConflictError,
    IdempotencyKeyInProgressError,
    IdempotencyReservation,
    IdempotencyStatus,
)
from app.funcionarios.application.queries import FuncionarioFilters, Pagination
from app.funcionarios.application.services import FuncionarioService
from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.exceptions import (
    ActiveEmployeeDeletionError,
    EmployeeNotFoundError,
    StaleEmployeeVersionError,
)
from app.funcionarios.domain.repositories import (
    RepositoryFilters,
    RepositoryPage,
    UpdateRequest,
    UpdateResult,
    UpdateStatus,
)


class FakeRepository:
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

    async def list(self, filters: RepositoryFilters, pagination: Pagination) -> RepositoryPage:
        items = [
            item
            for item in self.items.values()
            if (filters.departamento is None or item.departamento == filters.departamento)
            and (filters.cargo is None or item.cargo == filters.cargo)
        ]
        return RepositoryPage(
            items=tuple(items[pagination.skip : pagination.skip + pagination.page_size]),
            page=pagination.page,
            page_size=pagination.page_size,
            total=len(items),
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


@dataclass
class IdempotencyRecord:
    fingerprint: str
    employee: Funcionario | None


class FakeIdempotencyStore:
    def __init__(self) -> None:
        self.items: dict[str, IdempotencyRecord] = {}

    async def reserve(self, key: str, fingerprint: str) -> IdempotencyReservation:
        record = self.items.get(key)
        if record is None:
            self.items[key] = IdempotencyRecord(fingerprint, None)
            return IdempotencyReservation(True, IdempotencyStatus.PROCESSING)
        if record.fingerprint != fingerprint:
            raise IdempotencyKeyConflictError("idempotency key payload conflict")
        if record.employee is None:
            raise IdempotencyKeyInProgressError("idempotency key is being processed")
        return IdempotencyReservation(False, IdempotencyStatus.COMPLETED, record.employee)

    async def complete(self, key: str, fingerprint: str, funcionario: Funcionario) -> None:
        self.items[key] = IdempotencyRecord(fingerprint, funcionario)


def command(name: str = "Ada Lovelace") -> CreateFuncionarioCommand:
    return CreateFuncionarioCommand(
        nome_completo=name,
        email="ada@example.com",
        cargo="Engenheira",
        data_admissao=date(2026, 1, 15),
        departamento="Tecnologia",
    )


def service() -> tuple[FuncionarioService, FakeRepository, FakeIdempotencyStore]:
    repository = FakeRepository()
    store = FakeIdempotencyStore()
    return FuncionarioService(repository, store), repository, store


@pytest.mark.asyncio
async def test_create_replays_same_idempotency_key() -> None:
    use_cases, repository, store = service()

    first = await use_cases.create(command(), "create-1")
    repeated = await use_cases.create(command(), "create-1")

    assert repeated == first
    assert len(repository.items) == 1
    assert len(store.items) == 1


@pytest.mark.asyncio
async def test_create_detects_idempotency_payload_conflict() -> None:
    use_cases, _, _ = service()
    await use_cases.create(command(), "create-1")

    with pytest.raises(IdempotencyKeyConflictError):
        await use_cases.create(command("Grace Hopper"), "create-1")


@pytest.mark.asyncio
async def test_list_and_get_delegate_to_repository() -> None:
    use_cases, _, _ = service()
    employee = await use_cases.create(command(), "create-1")

    page = await use_cases.list(FuncionarioFilters(departamento="Tecnologia"), Pagination())
    found = await use_cases.get(employee.id)

    assert page.items == (employee,)
    assert found == employee


@pytest.mark.asyncio
async def test_get_raises_for_missing_employee() -> None:
    use_cases, _, _ = service()

    with pytest.raises(EmployeeNotFoundError):
        await use_cases.get(uuid4())


@pytest.mark.asyncio
async def test_update_returns_new_version_and_maps_stale_version() -> None:
    use_cases, _, _ = service()
    employee = await use_cases.create(command(), "create-1")

    updated = await use_cases.update(
        UpdateFuncionarioCommand(employee.id, 1, cargo="Staff Engineer")
    )
    assert updated.version == 2

    with pytest.raises(StaleEmployeeVersionError):
        await use_cases.update(UpdateFuncionarioCommand(employee.id, 1, cargo="Architect"))


@pytest.mark.asyncio
async def test_delete_blocks_active_and_deletes_inactive() -> None:
    use_cases, repository, _ = service()
    employee = await use_cases.create(command(), "create-1")
    repository.items[employee.id] = employee.update_allowed_fields(expected_version=1, ativo=True)

    with pytest.raises(ActiveEmployeeDeletionError):
        await use_cases.delete(employee.id)

    inactive = await use_cases.create(
        CreateFuncionarioCommand(
            "Grace Hopper",
            "grace@example.com",
            "Engenheira",
            date(2026, 2, 1),
        ),
        "create-2",
    )
    await use_cases.delete(inactive.id)
    assert inactive.id not in repository.items
