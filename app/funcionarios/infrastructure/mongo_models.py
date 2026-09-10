"""Mapeamentos entre documentos MongoDB e entidades de dominio."""

from datetime import UTC, datetime, time
from typing import Any
from uuid import UUID

from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.value_objects import Email


def funcionario_to_document(funcionario: Funcionario) -> dict[str, Any]:
    """Converte a entidade em um documento BSON persistivel."""
    return {
        "_id": str(funcionario.id),
        "nome_completo": funcionario.nome_completo,
        "email": funcionario.email.value,
        "cargo": funcionario.cargo,
        "data_admissao": datetime.combine(funcionario.data_admissao, time.min, tzinfo=UTC),
        "telefone": funcionario.telefone,
        "departamento": funcionario.departamento,
        "ativo": funcionario.ativo,
        "created_at": funcionario.created_at,
        "updated_at": funcionario.updated_at,
        "version": funcionario.version,
    }


def document_to_funcionario(document: dict[str, Any]) -> Funcionario:
    """Reconstroi a entidade a partir de um documento BSON."""
    return Funcionario(
        id=UUID(document["_id"]),
        nome_completo=document["nome_completo"],
        email=Email(document["email"]),
        cargo=document["cargo"],
        data_admissao=document["data_admissao"].date(),
        telefone=document.get("telefone"),
        departamento=document.get("departamento"),
        ativo=document["ativo"],
        created_at=_as_utc(document["created_at"]),
        updated_at=_as_utc(document["updated_at"]),
        version=document["version"],
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
