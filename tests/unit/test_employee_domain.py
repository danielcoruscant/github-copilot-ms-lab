from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.exceptions import (
    ActiveEmployeeDeletionError,
    InvalidEmployeeError,
    StaleEmployeeVersionError,
)
from app.funcionarios.domain.value_objects import Email


def make_employee(**overrides: object) -> Funcionario:
    data: dict[str, object] = {
        "nome_completo": "Ada Lovelace",
        "email": "ADA@example.com",
        "cargo": "Engenheira de Software",
        "data_admissao": date(2026, 1, 15),
        "telefone": "+55 47 99999-9999",
        "departamento": "Tecnologia",
    }
    data.update(overrides)
    return Funcionario.create(**data)  # type: ignore[arg-type]


def test_email_is_normalized_and_immutable() -> None:
    email = Email("  Ada@Example.COM ")

    assert email.value == "ada@example.com"
    with pytest.raises(AttributeError):
        email.value = "other@example.com"  # type: ignore[misc]


@pytest.mark.parametrize("value", ["", "invalid", "missing@domain", "x" * 255 + "@a.com"])
def test_email_rejects_invalid_values(value: str) -> None:
    with pytest.raises(InvalidEmployeeError):
        Email(value)


def test_create_sets_identity_defaults_and_utc_timestamps() -> None:
    employee = make_employee()

    assert employee.id is not None
    assert employee.email.value == "ada@example.com"
    assert employee.ativo is False
    assert employee.version == 1
    assert employee.created_at.tzinfo == UTC
    assert employee.updated_at.tzinfo == UTC


def test_update_changes_allowed_fields_and_increments_version() -> None:
    employee = make_employee()

    updated = employee.update_allowed_fields(
        expected_version=1,
        nome_completo="Ada Byron Lovelace",
        cargo="Staff Engineer",
        telefone=None,
        departamento="Pesquisa",
        ativo=True,
    )

    assert updated.id == employee.id
    assert updated.email == employee.email
    assert updated.data_admissao == employee.data_admissao
    assert updated.nome_completo == "Ada Byron Lovelace"
    assert updated.version == 2
    assert updated.updated_at >= employee.updated_at


def test_update_rejects_stale_version() -> None:
    employee = make_employee()

    with pytest.raises(StaleEmployeeVersionError):
        employee.update_allowed_fields(expected_version=0, cargo="Staff Engineer")


def test_active_employee_cannot_be_deleted() -> None:
    employee = replace(make_employee(), ativo=True)

    assert employee.can_be_deleted() is False
    with pytest.raises(ActiveEmployeeDeletionError):
        employee.ensure_can_be_deleted()


def test_inactive_employee_can_be_deleted() -> None:
    employee = make_employee()

    assert employee.can_be_deleted() is True
    employee.ensure_can_be_deleted()


def test_entity_rejects_naive_timestamps() -> None:
    employee = make_employee()

    with pytest.raises(InvalidEmployeeError):
        Funcionario(
            id=employee.id,
            nome_completo=employee.nome_completo,
            email=employee.email,
            cargo=employee.cargo,
            data_admissao=employee.data_admissao,
            telefone=employee.telefone,
            departamento=employee.departamento,
            ativo=False,
            created_at=datetime.now(),
            updated_at=employee.updated_at,
            version=1,
        )
