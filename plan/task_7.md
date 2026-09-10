# Task 7 — Implementar armazenamento de idempotência

## Objetivo

Persistir chaves de idempotência no MongoDB para que o comportamento funcione corretamente com múltiplos pods.

## Principais entregas

- Coleção `idempotency_keys` com documento de chave, fingerprint, status, resposta e timestamps.
- Índice único na chave.
- Expiração configurável por TTL.
- Reserva atômica de chave e leitura de resposta concluída.
- Tratamento de replay, conflito de payload e operações em andamento.
- Testes de concorrência e de estados da chave com store isolado e Mongo controlado.

## Critério de pronto

Uma mesma chave pode ser processada por apenas uma operação distribuída; reenvios reproduzem a resposta armazenada e não criam funcionários duplicados.

## Prompt de execução

Implemente a porta e o adaptador MongoDB de `IdempotencyKeyStore` em `app/core` ou `app/funcionarios/infrastructure`, usando Motor. Crie índice único em `key` e índice TTL em `expires_at`, com retenção configurável. Use operação atômica de reserva, como `find_one_and_update` com `upsert`, para evitar a janela entre verificar e inserir. Armazene fingerprint do payload, estado `processing`/`completed`/`failed`, status HTTP e corpo serializável da resposta. Se a chave existir com fingerprint diferente, gere conflito. Se estiver `completed`, devolva a resposta sem repetir o caso de uso. Defina política clara para chave presa em `processing`, usando expiração/lease. Mantenha o serviço de aplicação dependente apenas da porta. Crie testes para replay, fingerprint divergente, expiração, operação em andamento e concorrência, usando doubles para o serviço e Mongo controlado para validar atomicidade.