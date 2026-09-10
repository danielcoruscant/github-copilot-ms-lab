"""Consultas de aplicacao de funcionarios."""

from dataclasses import dataclass
from uuid import UUID

from app.funcionarios.domain.repositories import (
    Pagination as _Pagination,
)
from app.funcionarios.domain.repositories import (
    RepositoryFilters as _RepositoryFilters,
)
from app.funcionarios.domain.repositories import (
    RepositoryPage as _RepositoryPage,
)

FuncionarioFilters = _RepositoryFilters
FuncionarioPage = _RepositoryPage
Pagination = _Pagination


@dataclass(frozen=True, slots=True)
class FuncionarioIdQuery:
    funcionario_id: UUID
