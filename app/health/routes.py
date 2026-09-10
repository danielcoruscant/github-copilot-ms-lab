from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health", summary="Verifica se a aplicacao esta ativa")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=None, summary="Verifica se as dependencias estao prontas")
async def readiness_check(request: Request) -> dict[str, str] | JSONResponse:
    provider = getattr(request.app.state, "mongo_provider", None)
    if provider is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "detail": "MongoDB is not configured"},
        )
    try:
        await provider.ping()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "detail": "MongoDB is unavailable"},
        )
    return {"status": "ready"}
