"""Objetos de valor de funcionarios."""

import re
from dataclasses import dataclass

from app.funcionarios.domain.exceptions import InvalidEmployeeError


@dataclass(frozen=True, slots=True)
class Email:
    """E-mail normalizado e validado no limite do dominio."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise InvalidEmployeeError("email must be a valid address")
        if len(normalized) > 254:
            raise InvalidEmployeeError("email must have at most 254 characters")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
