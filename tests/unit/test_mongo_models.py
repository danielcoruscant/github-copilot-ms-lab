"""Testes de round-trip entre Funcionario e documentos MongoDB."""

from datetime import UTC, date, datetime

from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.infrastructure.mongo_models import (
    document_to_funcionario,
    funcionario_to_document,
)


def make_employee() -> Funcionario:
    return Funcionario.create(
        nome_completo="Ada Lovelace",
        email="ADA@example.com",
        cargo="Engenheira de Software",
        data_admissao=date(2026, 1, 15),
        telefone="+55 47 99999-9999",
        departamento="Tecnologia",
    )


def test_funcionario_to_document_maps_all_fields() -> None:
    employee = make_employee()

    document = funcionario_to_document(employee)

    assert document["_id"] == str(employee.id)
    assert document["email"] == "ada@example.com"
    assert document["data_admissao"].date() == employee.data_admissao
    assert document["version"] == 1


def test_document_to_funcionario_round_trips() -> None:
    employee = make_employee()

    document = funcionario_to_document(employee)
    restored = document_to_funcionario(document)

    assert restored == employee


def test_document_to_funcionario_handles_optional_fields() -> None:
    employee = make_employee()
    document = funcionario_to_document(employee)
    document["telefone"] = None
    document["departamento"] = None

    restored = document_to_funcionario(document)

    assert restored.telefone is None
    assert restored.departamento is None


def test_document_to_funcionario_normalizes_legacy_naive_timestamps() -> None:
    document = funcionario_to_document(make_employee())
    document["created_at"] = datetime(2026, 1, 15)
    document["updated_at"] = datetime(2026, 1, 15)

    restored = document_to_funcionario(document)

    assert restored.created_at.tzinfo == UTC
    assert restored.updated_at.tzinfo == UTC
