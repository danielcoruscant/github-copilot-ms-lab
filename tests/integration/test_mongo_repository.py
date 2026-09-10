from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from pymongo.errors import DuplicateKeyError

from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.exceptions import DuplicateEmployeeEmailError
from app.funcionarios.domain.repositories import (
    Pagination,
    RepositoryFilters,
    UpdateRequest,
    UpdateStatus,
)
from app.funcionarios.infrastructure.repositories import FuncionarioMongoRepository


@dataclass
class FakeCursor:
    documents: list[dict[str, Any]]

    def sort(self, _: list[tuple[str, int]]) -> "FakeCursor":
        self.documents.sort(key=lambda item: item["created_at"], reverse=True)
        return self

    def skip(self, value: int) -> "FakeCursor":
        self.documents = self.documents[value:]
        return self

    def limit(self, value: int) -> "FakeCursor":
        self.documents = self.documents[:value]
        return self

    async def to_list(self, length: int) -> list[dict[str, Any]]:
        return self.documents[:length]


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, Any]] = {}
        self.indexes: list[Any] = []

    async def create_indexes(self, indexes: list[Any]) -> list[str]:
        self.indexes = indexes
        return [index.document["name"] for index in indexes]

    async def insert_one(self, document: dict[str, Any]) -> None:
        if any(item["email"] == document["email"] for item in self.documents.values()):
            raise DuplicateKeyError("duplicate email")
        self.documents[document["_id"]] = dict(document)

    async def find_one(
        self, query: dict[str, Any], projection: dict[str, int] | None = None
    ) -> dict[str, Any] | None:
        for document in self.documents.values():
            if all(document.get(key) == value for key, value in query.items()):
                return dict(document)
        return None

    async def count_documents(self, query: dict[str, Any]) -> int:
        return len([document for document in self.documents.values() if _matches(document, query)])

    def find(self, query: dict[str, Any], projection: dict[str, int] | None = None) -> FakeCursor:
        return FakeCursor(
            [dict(document) for document in self.documents.values() if _matches(document, query)]
        )

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> Any:
        document = await self.find_one(query)
        if document is None:
            return SimpleNamespace(matched_count=0)
        document.update(update["$set"])
        document["version"] += update["$inc"]["version"]
        self.documents[document["_id"]] = document
        return SimpleNamespace(matched_count=1)

    async def delete_one(self, query: dict[str, Any]) -> Any:
        document = await self.find_one(query)
        if document is None:
            return SimpleNamespace(deleted_count=0)
        del self.documents[document["_id"]]
        return SimpleNamespace(deleted_count=1)


class FakeProvider:
    def __init__(self, collection: FakeCollection) -> None:
        self.database = {"funcionarios": collection}


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    return all(document.get(key) == value for key, value in query.items())


def make_employee(
    index: int = 1,
    departamento: str = "Tecnologia",
    email: str | None = None,
) -> Funcionario:
    return Funcionario.create(
        nome_completo=f"Funcionario {index}",
        email=email or f"funcionario{index}@example.com",
        cargo="Engenheiro",
        data_admissao=date(2026, 1, index),
        departamento=departamento,
    )


@pytest.mark.asyncio
async def test_repository_creates_indexes_and_crud() -> None:
    collection = FakeCollection()
    repository = FuncionarioMongoRepository(FakeProvider(collection))  # type: ignore[arg-type]
    employee = make_employee()

    assert await repository.ensure_indexes() == (
        "uq_funcionarios_email",
        "ix_funcionarios_departamento_cargo",
        "ix_funcionarios_created_at",
    )
    assert await repository.create(employee) == employee
    assert await repository.get_by_id(employee.id) == employee
    assert await repository.get_by_email(" FUNCIONARIO1@EXAMPLE.COM ") == employee

    page = await repository.list(RepositoryFilters(departamento="Tecnologia"), Pagination())
    assert page.items == (employee,)
    assert page.total == 1

    assert await repository.delete_if_inactive(employee.id) is True
    assert await repository.get_by_id(employee.id) is None


@pytest.mark.asyncio
async def test_repository_rejects_duplicate_email() -> None:
    collection = FakeCollection()
    repository = FuncionarioMongoRepository(FakeProvider(collection))  # type: ignore[arg-type]
    await repository.create(make_employee())

    with pytest.raises(DuplicateEmployeeEmailError):
        await repository.create(make_employee(2, email="funcionario1@example.com"))


@pytest.mark.asyncio
async def test_update_uses_version_and_increments_it() -> None:
    collection = FakeCollection()
    repository = FuncionarioMongoRepository(FakeProvider(collection))  # type: ignore[arg-type]
    employee = make_employee()
    await repository.create(employee)

    result = await repository.update_if_version_matches(
        UpdateRequest(employee.id, expected_version=1, cargo="Staff Engineer")
    )

    assert result.status is UpdateStatus.UPDATED
    assert result.funcionario is not None
    assert result.funcionario.cargo == "Staff Engineer"
    assert result.funcionario.version == 2

    stale = await repository.update_if_version_matches(
        UpdateRequest(employee.id, expected_version=1, cargo="Architect")
    )
    assert stale.status is UpdateStatus.VERSION_CONFLICT


@pytest.mark.asyncio
async def test_update_and_delete_distinguish_missing_and_active() -> None:
    collection = FakeCollection()
    repository = FuncionarioMongoRepository(FakeProvider(collection))  # type: ignore[arg-type]
    missing_id = UUID("00000000-0000-0000-0000-000000000001")

    result = await repository.update_if_version_matches(
        UpdateRequest(missing_id, expected_version=1, cargo="Architect")
    )
    assert result.status is UpdateStatus.NOT_FOUND
    assert await repository.delete_if_inactive(missing_id) is False

    employee = make_employee()
    await repository.create(employee)
    collection.documents[str(employee.id)]["ativo"] = True
    assert await repository.delete_if_inactive(employee.id) is False
