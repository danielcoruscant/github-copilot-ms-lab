"""Implementacao MongoDB da porta de funcionarios."""

from typing import Any
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.domain.repositories import (
    FuncionarioRepository,
    Pagination,
    RepositoryFilters,
    RepositoryPage,
    UpdateRequest,
    UpdateResult,
    UpdateStatus,
)
from app.funcionarios.infrastructure.mongo_client import (
    MongoClientProvider,
    translate_mongo_errors,
)
from app.funcionarios.infrastructure.mongo_models import (
    document_to_funcionario,
    funcionario_to_document,
)


class FuncionarioMongoRepository(FuncionarioRepository):
    """Repositorio assíncrono com consultas limitadas e atualização otimista."""

    def __init__(
        self,
        provider: MongoClientProvider,
        collection_name: str = "funcionarios",
    ) -> None:
        self._collection: AsyncIOMotorCollection[dict[str, Any]] = provider.database[
            collection_name
        ]

    async def ensure_indexes(self) -> tuple[str, ...]:
        """Cria índices necessários de forma idempotente."""
        with translate_mongo_errors():
            names = await self._collection.create_indexes(
                [
                    IndexModel(
                        [("email", ASCENDING)],
                        name="uq_funcionarios_email",
                        unique=True,
                    ),
                    IndexModel(
                        [("departamento", ASCENDING), ("cargo", ASCENDING)],
                        name="ix_funcionarios_departamento_cargo",
                    ),
                    IndexModel(
                        [("created_at", DESCENDING)],
                        name="ix_funcionarios_created_at",
                    ),
                ]
            )
        return tuple(names)

    async def create(self, funcionario: Funcionario) -> Funcionario:
        document = funcionario_to_document(funcionario)
        with translate_mongo_errors():
            await self._collection.insert_one(document)
        return funcionario

    async def get_by_id(self, funcionario_id: UUID) -> Funcionario | None:
        with translate_mongo_errors():
            document = await self._collection.find_one(
                {"_id": str(funcionario_id)}, projection={"_id": 1, **_projection()}
            )
        return None if document is None else document_to_funcionario(document)

    async def get_by_email(self, email: str) -> Funcionario | None:
        normalized_email = email.strip().lower()
        with translate_mongo_errors():
            document = await self._collection.find_one(
                {"email": normalized_email}, projection={"_id": 1, **_projection()}
            )
        return None if document is None else document_to_funcionario(document)

    async def list(self, filters: RepositoryFilters, pagination: Pagination) -> RepositoryPage:
        query: dict[str, Any] = {}
        if filters.departamento is not None:
            query["departamento"] = filters.departamento.strip()
        if filters.cargo is not None:
            query["cargo"] = filters.cargo.strip()

        with translate_mongo_errors():
            total = await self._collection.count_documents(query)
            cursor = (
                self._collection.find(query, projection={"_id": 1, **_projection()})
                .sort([("created_at", -1), ("_id", 1)])
                .skip(pagination.skip)
                .limit(pagination.page_size)
            )
            documents = await cursor.to_list(length=pagination.page_size)

        return RepositoryPage(
            items=tuple(document_to_funcionario(document) for document in documents),
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )

    async def update_if_version_matches(self, request: UpdateRequest) -> UpdateResult:
        changes = {
            key: value
            for key, value in {
                "nome_completo": request.nome_completo,
                "cargo": request.cargo,
                "telefone": request.telefone,
                "departamento": request.departamento,
                "ativo": request.ativo,
            }.items()
            if value is not None
        }
        changes["updated_at"] = _utc_now()

        with translate_mongo_errors():
            result = await self._collection.update_one(
                {"_id": str(request.funcionario_id), "version": request.expected_version},
                {"$set": changes, "$inc": {"version": 1}},
            )

            if result.matched_count == 0:
                current = await self._collection.find_one(
                    {"_id": str(request.funcionario_id)},
                    projection={"_id": 1, **_projection()},
                )
                if current is None:
                    return UpdateResult(UpdateStatus.NOT_FOUND)
                return UpdateResult(
                    UpdateStatus.VERSION_CONFLICT,
                    document_to_funcionario(current),
                )

            updated = await self._collection.find_one(
                {"_id": str(request.funcionario_id)},
                projection={"_id": 1, **_projection()},
            )

        if updated is None:
            return UpdateResult(UpdateStatus.NOT_FOUND)
        return UpdateResult(UpdateStatus.UPDATED, document_to_funcionario(updated))

    async def delete_if_inactive(self, funcionario_id: UUID) -> bool:
        with translate_mongo_errors():
            result = await self._collection.delete_one({"_id": str(funcionario_id), "ativo": False})
        return result.deleted_count == 1


def _projection() -> dict[str, int]:
    return {
        "nome_completo": 1,
        "email": 1,
        "cargo": 1,
        "data_admissao": 1,
        "telefone": 1,
        "departamento": 1,
        "ativo": 1,
        "created_at": 1,
        "updated_at": 1,
        "version": 1,
    }


def _utc_now() -> Any:
    from datetime import UTC, datetime

    return datetime.now(UTC)
