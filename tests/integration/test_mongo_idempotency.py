from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from app.core.config import Settings
from app.funcionarios.application.idempotency import (
    IdempotencyKeyConflictError,
    IdempotencyKeyInProgressError,
    IdempotencyStatus,
)
from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.infrastructure.idempotency import MongoIdempotencyKeyStore


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, Any]] = {}
        self.indexes: list[Any] = []

    async def create_indexes(self, indexes: list[Any]) -> list[str]:
        self.indexes = indexes
        return [index.document["name"] for index in indexes]

    async def find_one_and_update(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        document = self.documents.get(query["key"])
        if document is None and kwargs.get("upsert"):
            document = dict(update["$setOnInsert"])
            self.documents[document["key"]] = document
            return None
        if document is None:
            return None
        if "lease_until" in query and document["lease_until"] > query["lease_until"]["$lte"]:
            return None
        previous = dict(document)
        document.update(update.get("$set", {}))
        return previous if kwargs.get("return_document") == 0 else document

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        document = self.documents.get(query["key"])
        return None if document is None else dict(document)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> Any:
        document = self.documents.get(query["key"])
        if document is None or any(document.get(key) != value for key, value in query.items()):
            return type("Result", (), {"matched_count": 0})()
        document.update(update["$set"])
        return type("Result", (), {"matched_count": 1})()


class FakeProvider:
    def __init__(self, collection: FakeCollection) -> None:
        self.database = {"idempotency_keys": collection}


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        idempotency_retention_seconds=60,
        idempotency_lease_seconds=10,
    )


def make_employee() -> Funcionario:
    return Funcionario.create("Ada Lovelace", "ada@example.com", "Engenheira", date(2026, 1, 15))


@pytest.mark.asyncio
async def test_store_creates_indexes_and_replays_completed_response() -> None:
    collection = FakeCollection()
    store = MongoIdempotencyKeyStore(FakeProvider(collection), make_settings())  # type: ignore[arg-type]

    assert await store.ensure_indexes() == (
        "uq_idempotency_keys_key",
        "ttl_idempotency_keys_expires_at",
    )
    first = await store.reserve("key-1", "fingerprint-1")
    assert first.owner is True

    employee = make_employee()
    await store.complete("key-1", "fingerprint-1", employee)
    replay = await store.reserve("key-1", "fingerprint-1")

    assert replay.owner is False
    assert replay.status is IdempotencyStatus.COMPLETED
    assert replay.response == employee


@pytest.mark.asyncio
async def test_store_rejects_different_fingerprint() -> None:
    store = MongoIdempotencyKeyStore(FakeProvider(FakeCollection()), make_settings())  # type: ignore[arg-type]
    await store.reserve("key-1", "fingerprint-1")

    with pytest.raises(IdempotencyKeyConflictError):
        await store.reserve("key-1", "fingerprint-2")


@pytest.mark.asyncio
async def test_store_reports_processing_key() -> None:
    store = MongoIdempotencyKeyStore(FakeProvider(FakeCollection()), make_settings())  # type: ignore[arg-type]
    await store.reserve("key-1", "fingerprint-1")

    with pytest.raises(IdempotencyKeyInProgressError):
        await store.reserve("key-1", "fingerprint-1")


@pytest.mark.asyncio
async def test_store_reclaims_expired_lease() -> None:
    collection = FakeCollection()
    store = MongoIdempotencyKeyStore(FakeProvider(collection), make_settings())  # type: ignore[arg-type]
    await store.reserve("key-1", "fingerprint-1")
    collection.documents["key-1"]["lease_until"] = datetime.now(UTC) - timedelta(seconds=1)

    reservation = await store.reserve("key-1", "fingerprint-1")

    assert reservation.owner is True
