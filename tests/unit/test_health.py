import asyncio
from types import SimpleNamespace
from typing import Any, cast

from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.types import Scope

from app.health.routes import health_check, readiness_check


def make_request(state: object) -> Request:
    request_app = SimpleNamespace(state=state)
    scope: Scope = {
        "type": "http",
        "method": "GET",
        "path": "/ready",
        "headers": [],
        "query_string": b"",
        "scheme": "http",
        "app": cast(Any, request_app),
    }
    return Request(scope)


class Provider:
    async def ping(self) -> None:
        return None


class UnavailableProvider:
    async def ping(self) -> None:
        raise RuntimeError("connection failed")


def test_health_check_returns_ok() -> None:
    assert health_check() == {"status": "ok"}


def test_readiness_check_returns_not_ready_when_mongo_is_not_configured() -> None:
    response = asyncio.run(readiness_check(make_request(SimpleNamespace())))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 503
    assert response.body == b'{"status":"not_ready","detail":"MongoDB is not configured"}'


def test_readiness_check_returns_ready_when_mongo_is_available() -> None:
    response = asyncio.run(
        readiness_check(make_request(SimpleNamespace(mongo_provider=Provider())))
    )

    assert response == {"status": "ready"}


def test_readiness_check_returns_not_ready_when_mongo_is_unavailable() -> None:
    response = asyncio.run(
        readiness_check(make_request(SimpleNamespace(mongo_provider=UnavailableProvider())))
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 503
    assert response.body == b'{"status":"not_ready","detail":"MongoDB is unavailable"}'
