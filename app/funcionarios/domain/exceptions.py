"""Excecoes de dominio de funcionarios."""


class EmployeeDomainError(ValueError):
    """Erro base para violacoes das regras do dominio."""


class InvalidEmployeeError(EmployeeDomainError):
    """Dados invalidos para um funcionario."""


class DuplicateEmployeeEmailError(EmployeeDomainError):
    """E-mail ja associado a outro funcionario."""


class EmployeeNotFoundError(EmployeeDomainError):
    """Funcionario nao encontrado."""


class StaleEmployeeVersionError(EmployeeDomainError):
    """Atualizacao baseada em uma versao obsoleta."""


class ActiveEmployeeDeletionError(EmployeeDomainError):
    """Tentativa de excluir funcionario ativo em projeto."""
