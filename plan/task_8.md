# Task 8 — Construir schemas e rotas FastAPI

## Objetivo

Expor o contrato HTTP completo com Pydantic v2, documentação OpenAPI e dependências substituíveis.

## Principais entregas

- Schemas de entrada, saída, filtros e paginação em `interfaces/http/schemas.py`.
- Rotas CRUD em `interfaces/http/routes.py`.
- Header `Idempotency-Key` no cadastro.
- Campo `version` no update e na resposta.
- Status HTTP e códigos de erro documentados.
- Dependencies para obter o serviço de aplicação e o repositório.
- Testes de contrato HTTP e validação dos schemas com `httpx`.

## Critério de pronto

Swagger/ReDoc exibem schemas, headers, parâmetros e respostas; as rotas não acessam collections e podem receber serviços substitutos por dependency override.

## Prompt de execução

Implemente os schemas Pydantic v2 e as rotas FastAPI em `app/funcionarios/interfaces/http`. Use `ConfigDict(extra="forbid")` quando necessário para impedir campos proibidos. Valide nome, cargo, e-mail, data ISO 8601, paginação entre 1 e 100 e atualização sem permitir `email` ou `data_admissao`. Exponha `POST`, `GET` por id, `GET` paginado com filtros, `PATCH` e `DELETE`. Leia `Idempotency-Key` com `Header`, documente sua obrigatoriedade no POST e passe o valor ao caso de uso. Passe `version` no PATCH. Declare `response_model`, `status_code`, `responses` e exemplos para OpenAPI. Use injeção de dependências e conversores próprios para erros; nunca coloque regra de negócio ou acesso Motor nas rotas. Crie testes de contrato HTTP com `httpx.AsyncClient` e dependências substituídas, cobrindo validação, status codes, filtros, header de idempotência e documentação OpenAPI.