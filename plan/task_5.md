# Task 5 — Implementar repositório MongoDB

## Objetivo

Implementar a porta de persistência de funcionários com consultas eficientes, unicidade e atualização otimista.

## Principais entregas

- `FuncionarioMongoRepository` em `infrastructure/repositories.py`.
- CRUD assíncrono usando Motor e projeções explícitas.
- Índice único para e-mail normalizado.
- Índices para departamento, cargo e data de criação.
- Atualização atômica por `id` e `version` usando `$set` e `$inc`.
- Paginação com limite máximo.
- Testes de integração do repositório contra uma instância MongoDB controlada.

## Critério de pronto

O repositório implementa todos os métodos da porta, nunca retorna consulta ilimitada e não sobrescreve uma atualização quando a versão esperada está obsoleta.

## Prompt de execução

Implemente `FuncionarioMongoRepository` usando Motor e a porta definida na Task 3. Crie uma rotina idempotente de índices: índice único em `email`, índice composto para `departamento` e `cargo`, e índice descendente em `created_at`. Normalize o e-mail antes de persistir e trate `DuplicateKeyError` como conflito de unicidade. Para atualização, use uma única operação MongoDB com filtro por `_id` e `version`, `$set` apenas nos campos permitidos e `$inc` de version. Diferencie documento inexistente de versão obsoleta consultando o estado somente quando necessário. Use projeções, `skip`/`limit` com limite máximo e ordenação estável. Não coloque regras de negócio na query nem deixe a camada HTTP acessar a collection diretamente. Implemente testes de integração para criação, unicidade, filtros, paginação, atualização otimista, incremento de versão e exclusão, usando banco Mongo descartável ou coleção isolada por execução.