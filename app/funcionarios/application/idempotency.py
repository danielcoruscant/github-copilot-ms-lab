"""Porta de armazenamento de respostas idempotentes."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.funcionarios.domain.entities import Funcionario


class IdempotencyKeyConflictError(ValueError):
    """A chave foi reutilizada com um payload diferente."""


class IdempotencyKeyInProgressError(RuntimeError):
    """A chave esta sendo processada por outra requisicao."""


class IdempotencyStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class IdempotencyReservation:
    owner: bool
    status: IdempotencyStatus
    response: Funcionario | None = None


class IdempotencyKeyStore(Protocol):
    async def reserve(self, key: str, fingerprint: str) -> IdempotencyReservation:
        """Reserva a chave atomicamente ou retorna seu estado atual."""

    async def complete(self, key: str, fingerprint: str, funcionario: Funcionario) -> None:
        """Marca a chave como concluida e armazena a resposta."""
