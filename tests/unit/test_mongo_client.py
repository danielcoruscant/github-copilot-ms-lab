"""Testes do provider MongoDB usando um cliente fake injetavel."""

from typing import Any

import pytest
from pymongo.errors import DuplicateKeyError, OperationFailure

from app.core.config import Settings
from app.funcionarios.domain.exceptions import DuplicateEmployeeEmailError
from app.funcionarios.infrastructure.mongo_client import (
    MongoClientProvider,
    MongoUnavailableError,
    translate_mongo_errors,
)


class _FakeAdmin:
    def __init__(self) -> None:
        self.commands: list[str] = []

    async def command(self, name: str) -> dict[str, int]:
        self.commands.append(name)
        return {"ok": 1}


class FakeMotorClient:
    def __init__(self, uri: str, **kwargs: Any) -> None:
        self.uri = uri
        self.kwargs = kwargs
        self.admin = _FakeAdmin()
        self.closed = False

    def __getitem__(self, name: str) -> str:
        return f"database:{name}"

    def close(self) -> None:
        self.closed = True


def make_settings(**overrides: Any) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_client_property_raises_before_connect() -> None:
    provider = MongoClientProvider(make_settings(), client_factory=FakeMotorClient)

    with pytest.raises(MongoUnavailableError):
        _ = provider.client


@pytest.mark.asyncio
async def test_connect_creates_client_with_configured_timeouts() -> None:
    provider = MongoClientProvider(make_settings(), client_factory=FakeMotorClient)

    await provider.connect()

    client = provider.client
    assert isinstance(client, FakeMotorClient)
    assert client.kwargs["serverSelectionTimeoutMS"] == 5000
    assert client.kwargs["connectTimeoutMS"] == 5000
    assert client.kwargs["timeoutMS"] == 5000


@pytest.mark.asyncio
async def test_connect_is_idempotent() -> None:
    provider = MongoClientProvider(make_settings(), client_factory=FakeMotorClient)

    await provider.connect()
    first_client = provider.client
    await provider.connect()

    assert provider.client is first_client


@pytest.mark.asyncio
async def test_ping_calls_admin_command() -> None:
    provider = MongoClientProvider(make_settings(), client_factory=FakeMotorClient)
    await provider.connect()

    await provider.ping()

    assert provider.client.admin.commands == ["ping"]


@pytest.mark.asyncio
async def test_close_resets_client_and_is_idempotent() -> None:
    provider = MongoClientProvider(make_settings(), client_factory=FakeMotorClient)
    await provider.connect()
    client = provider.client

    await provider.close()

    assert client.closed is True
    with pytest.raises(MongoUnavailableError):
        _ = provider.client

    await provider.close()


@pytest.mark.asyncio
async def test_database_property_selects_configured_database() -> None:
    provider = MongoClientProvider(
        make_settings(mongo_database="custom_db"), client_factory=FakeMotorClient
    )
    await provider.connect()

    assert provider.database == "database:custom_db"


def test_translate_mongo_errors_converts_duplicate_key() -> None:
    with pytest.raises(DuplicateEmployeeEmailError), translate_mongo_errors():
        raise DuplicateKeyError("E11000 duplicate key")


def test_translate_mongo_errors_converts_generic_pymongo_error() -> None:
    with pytest.raises(MongoUnavailableError), translate_mongo_errors():
        raise OperationFailure("boom")


def test_translate_mongo_errors_passes_through_other_exceptions() -> None:
    with pytest.raises(ValueError), translate_mongo_errors():
        raise ValueError("not a mongo error")
