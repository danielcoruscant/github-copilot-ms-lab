# Task 9 — Centralizar erros, observabilidade e lifecycle

## Objetivo

Finalizar a composição da aplicação com tratamento consistente de erros, health checks, logging e ciclo de vida.

## Principais entregas

- Handlers globais para validação, não encontrado, duplicidade, conflito de versão e idempotência.
- Resposta de erro padronizada com código, mensagem e correlation id.
- `GET /health` e, se necessário, `GET /ready` verificando dependências.
- Logging estruturado sem dados pessoais ou segredos.
- `app/main.py` compondo routers, middleware e lifecycle Mongo.
- Testes dos handlers, health checks, correlation id e lifecycle com dependências controladas.

## Critério de pronto

Falhas conhecidas retornam códigos HTTP previsíveis, o health check distingue processo vivo de Mongo pronto e o lifecycle não deixa clientes abertos.

## Prompt de execução

Implemente `app/core/errors.py`, logging e health routes. Crie handlers FastAPI para erro de validação Pydantic, funcionário não encontrado, e-mail duplicado, exclusão bloqueada, conflito de versão e conflito de `Idempotency-Key`. Use um schema de erro estável e não exponha stack trace em produção. Adicione middleware ou dependency para correlation id, incluindo-o nos logs e na resposta. Configure logging estruturado com nível por ambiente, removendo e-mail, telefone, tokens e URI de banco. Diferencie `/health` (processo vivo) de `/ready` (Mongo disponível). Componha tudo em `app/main.py` usando lifespan para criar/fechar Motor e registrar índices. Mantenha erros de domínio independentes do framework. Crie testes para cada handler, para os estados de health/readiness, propagação do correlation id e fechamento do lifecycle, substituindo Mongo e logger por doubles quando apropriado.