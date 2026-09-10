"""Casos de uso de funcionarios."""

import hashlib
import json
from uuid import UUID

from app.funcionarios.application.commands import (
    CreateFuncionarioCommand,
    UpdateFuncionarioCommand,
)
from app.funcionarios.application.idempotency import (
    IdempotencyKeyInProgressError,
    IdempotencyKeyStore,
)
from app.funcionarios.application.queries import (
    FuncionarioFilters,
    FuncionarioPage,
    Pagination,
)
from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.exceptions import (
    ActiveEmployeeDeletionError,
    EmployeeNotFoundError,
    InvalidEmployeeError,
    StaleEmployeeVersionError,
)
from app.funcionarios.domain.repositories import (
    FuncionarioRepository,
    RepositoryFilters,
    UpdateRequest,
    UpdateStatus,
)


class FuncionarioService:
    """Orquestra casos de uso sem conhecer HTTP ou MongoDB."""

    def __init__(
        self,
        repository: FuncionarioRepository,
        idempotency_keys: IdempotencyKeyStore,
    ) -> None:
        self._repository = repository
        self._idempotency_keys = idempotency_keys

    async def create(self, command: CreateFuncionarioCommand, idempotency_key: str) -> Funcionario:
        if not idempotency_key.strip():
            raise InvalidEmployeeError("Idempotency-Key must not be blank")

        fingerprint = _fingerprint(command)
        reservation = await self._idempotency_keys.reserve(idempotency_key, fingerprint)
        if not reservation.owner:
            if reservation.response is not None:
                return reservation.response
            raise IdempotencyKeyInProgressError("idempotency key is being processed")

        employee = Funcionario.create(
            nome_completo=command.nome_completo,
            email=command.email,
            cargo=command.cargo,
            data_admissao=command.data_admissao,
            telefone=command.telefone,
            departamento=command.departamento,
        )
        created = await self._repository.create(employee)
        await self._idempotency_keys.complete(idempotency_key, fingerprint, created)
        return created

    async def list(self, filters: FuncionarioFilters, pagination: Pagination) -> FuncionarioPage:
        return await self._repository.list(
            RepositoryFilters(
                departamento=filters.departamento,
                cargo=filters.cargo,
            ),
            pagination,
        )

    async def get(self, funcionario_id: UUID) -> Funcionario:
        employee = await self._repository.get_by_id(funcionario_id)
        if employee is None:
            raise EmployeeNotFoundError("employee not found")
        return employee

    async def update(self, command: UpdateFuncionarioCommand) -> Funcionario:
        result = await self._repository.update_if_version_matches(
            request=command_to_update_request(command)
        )
        if result.status is UpdateStatus.NOT_FOUND:
            raise EmployeeNotFoundError("employee not found")
        if result.status is UpdateStatus.VERSION_CONFLICT:
            raise StaleEmployeeVersionError("employee version is stale")
        if result.funcionario is None:
            raise InvalidEmployeeError("repository returned an empty update result")
        return result.funcionario

    async def delete(self, funcionario_id: UUID) -> None:
        employee = await self.get(funcionario_id)
        try:
            employee.ensure_can_be_deleted()
        except ActiveEmployeeDeletionError:
            raise
        deleted = await self._repository.delete_if_inactive(funcionario_id)
        if not deleted:
            raise EmployeeNotFoundError("employee could not be deleted")


def command_to_update_request(command: UpdateFuncionarioCommand) -> UpdateRequest:
    return UpdateRequest(
        funcionario_id=command.funcionario_id,
        expected_version=command.expected_version,
        nome_completo=command.nome_completo,
        cargo=command.cargo,
        telefone=command.telefone,
        departamento=command.departamento,
        ativo=command.ativo,
    )


def _fingerprint(command: CreateFuncionarioCommand) -> str:
    payload = {
        "nome_completo": command.nome_completo.strip(),
        "email": command.email.strip().lower(),
        "cargo": command.cargo.strip(),
        "data_admissao": command.data_admissao.isoformat(),
        "telefone": command.telefone,
        "departamento": command.departamento,
    }
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
