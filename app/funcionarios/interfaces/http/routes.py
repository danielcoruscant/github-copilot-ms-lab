"""Rotas HTTP de funcionarios."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status

from app.funcionarios.application.commands import (
    CreateFuncionarioCommand,
    UpdateFuncionarioCommand,
)
from app.funcionarios.application.queries import FuncionarioFilters, Pagination
from app.funcionarios.application.services import FuncionarioService
from app.funcionarios.interfaces.http.dependencies import get_funcionario_service
from app.funcionarios.interfaces.http.schemas import (
    CreateFuncionarioRequest,
    ErrorResponse,
    FuncionarioPageResponse,
    FuncionarioResponse,
    UpdateFuncionarioRequest,
    funcionario_response,
)

router = APIRouter(prefix="/funcionarios", tags=["funcionarios"])
ServiceDependency = Annotated[FuncionarioService, Depends(get_funcionario_service)]


@router.post(
    "",
    response_model=FuncionarioResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Conflict"},
        422: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def create_funcionario(
    request: CreateFuncionarioRequest,
    service: ServiceDependency,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, description="Unique request key")
    ],
) -> FuncionarioResponse:
    employee = await service.create(
        CreateFuncionarioCommand(**request.model_dump()), idempotency_key
    )
    return funcionario_response(employee)


@router.get("", response_model=FuncionarioPageResponse)
async def list_funcionarios(
    service: ServiceDependency,
    departamento: str | None = Query(default=None),
    cargo: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> FuncionarioPageResponse:
    result = await service.list(
        FuncionarioFilters(departamento=departamento, cargo=cargo),
        Pagination(page=page, page_size=page_size),
    )
    return FuncionarioPageResponse(
        items=[funcionario_response(item) for item in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )


@router.get("/{funcionario_id}", response_model=FuncionarioResponse)
async def get_funcionario(funcionario_id: UUID, service: ServiceDependency) -> FuncionarioResponse:
    return funcionario_response(await service.get(funcionario_id))


@router.patch(
    "/{funcionario_id}",
    response_model=FuncionarioResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        409: {"model": ErrorResponse, "description": "Conflict"},
    },
)
async def update_funcionario(
    funcionario_id: UUID,
    request: UpdateFuncionarioRequest,
    service: ServiceDependency,
) -> FuncionarioResponse:
    data = request.model_dump()
    version = data.pop("version")
    return funcionario_response(
        await service.update(
            UpdateFuncionarioCommand(
                funcionario_id=funcionario_id,
                expected_version=version,
                **data,
            )
        )
    )


@router.delete(
    "/{funcionario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        409: {"model": ErrorResponse, "description": "Conflict"},
    },
)
async def delete_funcionario(funcionario_id: UUID, service: ServiceDependency) -> Response:
    await service.delete(funcionario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
