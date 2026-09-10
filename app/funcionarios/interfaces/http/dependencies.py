"""Dependencias FastAPI da interface HTTP de funcionarios."""

from typing import cast

from fastapi import HTTPException, Request, status

from app.funcionarios.application.services import FuncionarioService


def get_funcionario_service(request: Request) -> FuncionarioService:
    """Ponto de composição substituível por dependency override nos testes."""
    service = getattr(request.app.state, "funcionario_service", None)
    if service is not None:
        return cast(FuncionarioService, service)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="employee service is not configured",
    )
