"""Entidades de dominio de funcionarios."""

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from typing import Self
from uuid import UUID, uuid4

from app.funcionarios.domain.exceptions import (
    ActiveEmployeeDeletionError,
    InvalidEmployeeError,
    StaleEmployeeVersionError,
)
from app.funcionarios.domain.value_objects import Email


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _required_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidEmployeeError(f"{field_name} must not be blank")
    return normalized


@dataclass(frozen=True, slots=True)
class Funcionario:
    """Agregado raiz do bounded context de funcionarios."""

    id: UUID
    nome_completo: str
    email: Email
    cargo: str
    data_admissao: date
    telefone: str | None
    departamento: str | None
    ativo: bool
    created_at: datetime
    updated_at: datetime
    version: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "nome_completo", _required_text(self.nome_completo, "nome_completo")
        )
        object.__setattr__(self, "cargo", _required_text(self.cargo, "cargo"))
        if self.telefone is not None:
            object.__setattr__(self, "telefone", self.telefone.strip() or None)
        if self.departamento is not None:
            object.__setattr__(self, "departamento", self.departamento.strip() or None)
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise InvalidEmployeeError("timestamps must include a timezone")
        if self.version < 1:
            raise InvalidEmployeeError("version must be at least 1")

    @classmethod
    def create(
        cls,
        nome_completo: str,
        email: str,
        cargo: str,
        data_admissao: date,
        telefone: str | None = None,
        departamento: str | None = None,
    ) -> Self:
        now = _utc_now()
        return cls(
            id=uuid4(),
            nome_completo=nome_completo,
            email=Email(email),
            cargo=cargo,
            data_admissao=data_admissao,
            telefone=telefone,
            departamento=departamento,
            ativo=False,
            created_at=now,
            updated_at=now,
            version=1,
        )

    def update_allowed_fields(
        self,
        *,
        expected_version: int,
        nome_completo: str | None = None,
        cargo: str | None = None,
        telefone: str | None = None,
        departamento: str | None = None,
        ativo: bool | None = None,
    ) -> Self:
        if expected_version != self.version:
            raise StaleEmployeeVersionError(
                f"expected version {expected_version}, current version is {self.version}"
            )
        return replace(
            self,
            nome_completo=self.nome_completo if nome_completo is None else nome_completo,
            cargo=self.cargo if cargo is None else cargo,
            telefone=telefone,
            departamento=departamento,
            ativo=self.ativo if ativo is None else ativo,
            updated_at=_utc_now(),
            version=self.version + 1,
        )

    def can_be_deleted(self) -> bool:
        return not self.ativo

    def ensure_can_be_deleted(self) -> None:
        if self.ativo:
            raise ActiveEmployeeDeletionError(
                "employee cannot be deleted while active in a project"
            )
