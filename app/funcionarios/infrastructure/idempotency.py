"""Adaptador MongoDB para idempotencia distribuida."""

from datetime import UTC, datetime, timedelta
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, IndexModel, ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.config import Settings
from app.funcionarios.application.idempotency import (
    IdempotencyKeyConflictError,
    IdempotencyKeyInProgressError,
    IdempotencyKeyStore,
    IdempotencyReservation,
    IdempotencyStatus,
)
from app.funcionarios.domain.entities import Funcionario
from app.funcionarios.infrastructure.mongo_client import (
    MongoClientProvider,
    translate_mongo_errors,
)
from app.funcionarios.infrastructure.mongo_models import (
    document_to_funcionario,
    funcionario_to_document,
)


class MongoIdempotencyKeyStore(IdempotencyKeyStore):
    """Store compartilhado para replay idempotente entre processos e pods."""

    def __init__(
        self,
        provider: MongoClientProvider,
        settings: Settings,
        collection_name: str = "idempotency_keys",
    ) -> None:
        self._settings = settings
        self._collection: AsyncIOMotorCollection[dict[str, Any]] = provider.database[
            collection_name
        ]

    async def ensure_indexes(self) -> tuple[str, ...]:
        with translate_mongo_errors():
            return tuple(
                await self._collection.create_indexes(
                    [
                        IndexModel(
                            [("key", ASCENDING)],
                            name="uq_idempotency_keys_key",
                            unique=True,
                        ),
                        IndexModel(
                            [("expires_at", ASCENDING)],
                            name="ttl_idempotency_keys_expires_at",
                            expireAfterSeconds=0,
                        ),
                    ]
                )
            )

    async def reserve(self, key: str, fingerprint: str) -> IdempotencyReservation:
        now = _utc_now()
        expires_at = now + timedelta(seconds=self._settings.idempotency_retention_seconds)
        lease_until = now + timedelta(seconds=self._settings.idempotency_lease_seconds)
        inserted = {
            "key": key,
            "fingerprint": fingerprint,
            "status": IdempotencyStatus.PROCESSING.value,
            "response": None,
            "created_at": now,
            "updated_at": now,
            "lease_until": lease_until,
            "expires_at": expires_at,
        }

        existing: dict[str, Any] | None
        try:
            with translate_mongo_errors():
                existing = await self._collection.find_one_and_update(
                    {"key": key},
                    {"$setOnInsert": inserted},
                    upsert=True,
                    return_document=ReturnDocument.BEFORE,
                )
        except DuplicateKeyError:
            existing = await self._collection.find_one({"key": key})

        if existing is None:
            return IdempotencyReservation(True, IdempotencyStatus.PROCESSING)
        if existing["fingerprint"] != fingerprint:
            raise IdempotencyKeyConflictError("idempotency key was reused with a different payload")
        if existing["status"] == IdempotencyStatus.COMPLETED.value:
            response = existing.get("response")
            if response is None:
                raise IdempotencyKeyInProgressError("completed key has no response")
            return IdempotencyReservation(
                False,
                IdempotencyStatus.COMPLETED,
                document_to_funcionario(response),
            )
        if existing.get("lease_until", now) <= now:
            reclaimed = await self._collection.find_one_and_update(
                {
                    "key": key,
                    "fingerprint": fingerprint,
                    "status": IdempotencyStatus.PROCESSING.value,
                    "lease_until": {"$lte": now},
                },
                {"$set": {"lease_until": lease_until, "updated_at": now}},
                return_document=ReturnDocument.BEFORE,
            )
            if reclaimed is not None:
                return IdempotencyReservation(True, IdempotencyStatus.PROCESSING)
        raise IdempotencyKeyInProgressError("idempotency key is being processed")

    async def complete(self, key: str, fingerprint: str, funcionario: Funcionario) -> None:
        now = _utc_now()
        with translate_mongo_errors():
            result = await self._collection.update_one(
                {
                    "key": key,
                    "fingerprint": fingerprint,
                    "status": IdempotencyStatus.PROCESSING.value,
                },
                {
                    "$set": {
                        "status": IdempotencyStatus.COMPLETED.value,
                        "response": funcionario_to_document(funcionario),
                        "updated_at": now,
                    }
                },
            )
        if result.matched_count != 1:
            raise IdempotencyKeyInProgressError("idempotency key could not be completed")


def _utc_now() -> datetime:
    return datetime.now(UTC)
