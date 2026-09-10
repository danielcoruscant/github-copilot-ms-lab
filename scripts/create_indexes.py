"""Cria os indices MongoDB de forma idempotente."""

import asyncio

from app.core.config import get_settings
from app.funcionarios.infrastructure.idempotency import MongoIdempotencyKeyStore
from app.funcionarios.infrastructure.mongo_client import MongoClientProvider
from app.funcionarios.infrastructure.repositories import FuncionarioMongoRepository


async def create_indexes() -> None:
    settings = get_settings()
    provider = MongoClientProvider(settings)
    await provider.connect()
    try:
        await FuncionarioMongoRepository(provider).ensure_indexes()
        await MongoIdempotencyKeyStore(provider, settings).ensure_indexes()
    finally:
        await provider.close()


def main() -> None:
    asyncio.run(create_indexes())


if __name__ == "__main__":
    main()
