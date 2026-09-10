"""Portas de persistencia do dominio de funcionarios."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.funcionarios.domain.entities import Funcionario


@dataclass(frozen=True, slots=True)
class RepositoryFilters:
    departamento: str | None = None
    cargo: str | None = None


@dataclass(frozen=True, slots=True)
class Pagination:
    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be at least 1")
        if not 1 <= self.page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True, slots=True)
class RepositoryPage:
    items: tuple[Funcionario, ...]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True, slots=True)
class UpdateRequest:
    funcionario_id: UUID
    expected_version: int
    nome_completo: str | None = None
    cargo: str | None = None
    telefone: str | None = None
    departamento: str | None = None
    ativo: bool | None = None


class UpdateStatus(StrEnum):
    UPDATED = "updated"
    NOT_FOUND = "not_found"
    VERSION_CONFLICT = "version_conflict"


@dataclass(frozen=True, slots=True)
class UpdateResult:
    status: UpdateStatus
    funcionario: Funcionario | None = None


@runtime_checkable
class FuncionarioRepository(Protocol):
    async def create(self, funcionario: Funcionario) -> Funcionario:
        """Persiste e retorna um novo funcionario."""

    async def get_by_id(self, funcionario_id: UUID) -> Funcionario | None:
        """Busca um funcionario pela identidade."""

    async def get_by_email(self, email: str) -> Funcionario | None:
        """Busca um funcionario pelo e-mail normalizado."""

    async def list(self, filters: RepositoryFilters, pagination: Pagination) -> RepositoryPage:
        """Lista funcionarios com filtros e paginação."""

    async def update_if_version_matches(self, request: UpdateRequest) -> UpdateResult:
        """Atualiza somente se a versao esperada ainda for atual."""

    async def delete_if_inactive(self, funcionario_id: UUID) -> bool:
        """Exclui um funcionario inativo e informa se encontrou o registro."""
