# Task 3 — Definir portas e contratos de aplicação

## Objetivo

Criar interfaces que desacoplem os casos de uso do MongoDB e organizem comandos, consultas e resultados.

## Principais entregas

- Porta assíncrona `FuncionarioRepository` em `domain/repositories.py`.
- Contratos para criar, buscar, listar, atualizar por versão e excluir.
- DTOs internos de comandos e filtros na camada `application`.
- Tipos de resultado e paginação sem dependência de schemas HTTP.
- Dependências expressas por Protocols ou classes abstratas.
- Testes de contrato das portas usando implementações fake locais.

## Critério de pronto

Os casos de uso conseguem depender de uma abstração de repositório, e nenhuma interface de domínio conhece detalhes de Motor ou MongoDB.

## Prompt de execução

Crie `app/funcionarios/domain/repositories.py` com uma porta assíncrona para operações de funcionário: `create`, `get_by_id`, `get_by_email`, `list`, `update_if_version_matches` e `delete_if_inactive`. Modele filtros por departamento e cargo, paginação limitada e resultado paginado em `app/funcionarios/application/queries.py`. Crie comandos para criação e atualização em `application/commands.py`. Use Protocols ou ABCs, type hints completos e `datetime` com timezone. O método de atualização deve receber `expected_version` e retornar resultado que permita distinguir recurso inexistente de versão obsoleta. Não importe Motor, FastAPI ou Pydantic nesses contratos; a camada HTTP fará o mapeamento. Escreva testes de contrato com implementações fake em memória para verificar assinaturas, filtros, paginação e distinção entre recurso inexistente e versão obsoleta.