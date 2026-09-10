"""Schemas Pydantic do contrato HTTP de funcionarios."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateFuncionarioRequest(StrictSchema):
    nome_completo: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    cargo: str = Field(min_length=1, max_length=120)
    data_admissao: date
    telefone: str | None = Field(default=None, max_length=30)
    departamento: str | None = Field(default=None, max_length=120)

    @field_validator("nome_completo", "cargo", "email")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class UpdateFuncionarioRequest(StrictSchema):
    nome_completo: str | None = Field(default=None, min_length=1, max_length=120)
    cargo: str | None = Field(default=None, min_length=1, max_length=120)
    telefone: str | None = Field(default=None, max_length=30)
    departamento: str | None = Field(default=None, max_length=120)
    ativo: bool | None = None
    version: int = Field(ge=1)


class FuncionarioResponse(StrictSchema):
    id: UUID
    nome_completo: str
    email: str
    cargo: str
    data_admissao: date
    telefone: str | None
    departamento: str | None
    ativo: bool
    created_at: datetime
    updated_at: datetime
    version: int


class FuncionarioPageResponse(StrictSchema):
    items: list[FuncionarioResponse]
    page: int
    page_size: int
    total: int


class ErrorResponse(StrictSchema):
    detail: str


def funcionario_response(employee: object) -> FuncionarioResponse:
    from app.funcionarios.domain.entities import Funcionario

    if not isinstance(employee, Funcionario):
        raise TypeError("expected Funcionario")
    return FuncionarioResponse(
        id=employee.id,
        nome_completo=employee.nome_completo,
        email=employee.email.value,
        cargo=employee.cargo,
        data_admissao=employee.data_admissao,
        telefone=employee.telefone,
        departamento=employee.departamento,
        ativo=employee.ativo,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
        version=employee.version,
    )
