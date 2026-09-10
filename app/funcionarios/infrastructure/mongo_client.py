"""Cliente MongoDB assincrono e ciclo de vida da conexao."""

import logging
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.config import Settings
from app.funcionarios.domain.exceptions import DuplicateEmployeeEmailError

logger = logging.getLogger(__name__)


class MongoUnavailableError(RuntimeError):
    """Falha de infraestrutura ao comunicar com o MongoDB."""


class MongoClientProvider:
    """Mantem uma unica instancia de AsyncIOMotorClient por processo."""

    def __init__(
        self,
        settings: Settings,
        client_factory: Callable[..., AsyncIOMotorClient[dict[str, Any]]] = AsyncIOMotorClient,
    ) -> None:
        self._settings = settings
        self._client_factory = client_factory
        self._client: AsyncIOMotorClient[dict[str, Any]] | None = None

    @property
    def client(self) -> AsyncIOMotorClient[dict[str, Any]]:
        if self._client is None:
            raise MongoUnavailableError("MongoDB client is not connected")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase[dict[str, Any]]:
        return self.client[self._settings.mongo_database]

    async def connect(self) -> None:
        if self._client is not None:
            return
        logger.info("Connecting to MongoDB database=%s", self._settings.mongo_database)
        self._client = self._client_factory(
            self._settings.mongo_uri,
            tz_aware=True,
            serverSelectionTimeoutMS=self._settings.mongo_server_selection_timeout_ms,
            connectTimeoutMS=self._settings.mongo_connect_timeout_ms,
            timeoutMS=self._settings.mongo_operation_timeout_ms,
        )

    async def ping(self) -> None:
        await self.client.admin.command("ping")

    async def close(self) -> None:
        if self._client is None:
            return
        logger.info("Closing MongoDB connection")
        self._client.close()
        self._client = None


@contextmanager
def translate_mongo_errors() -> Any:
    """Converte falhas do driver Mongo em excecoes de dominio/infraestrutura."""
    try:
        yield
    except DuplicateKeyError as exc:
        raise DuplicateEmployeeEmailError("email is already registered") from exc
    except PyMongoError as exc:
        logger.error("MongoDB operation failed: %s", type(exc).__name__)
        raise MongoUnavailableError("MongoDB operation failed") from exc
