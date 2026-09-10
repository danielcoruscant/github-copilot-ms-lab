"""Comandos de aplicacao de funcionarios."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateFuncionarioCommand:
    nome_completo: str
    email: str
    cargo: str
    data_admissao: date
    telefone: str | None = None
    departamento: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateFuncionarioCommand:
    funcionario_id: UUID
    expected_version: int
    nome_completo: str | None = None
    cargo: str | None = None
    telefone: str | None = None
    departamento: str | None = None
    ativo: bool | None = None
