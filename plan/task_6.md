# Task 6 — Criar casos de uso

## Objetivo

Orquestrar as operações de cadastro, consulta, atualização e exclusão em serviços de aplicação independentes da API e do MongoDB.

## Principais entregas

- Serviço de aplicação com `create`, `list`, `get`, `update` e `delete`.
- Validação das regras por meio da entidade e das portas.
- Bloqueio de exclusão quando `ativo=true`.
- Conversão consistente de conflitos para exceções de aplicação.
- Suporte a `Idempotency-Key` compartilhado entre réplicas por porta própria.
- Testes unitários dos casos de uso com repositórios e stores fake.

## Critério de pronto

Cada caso de uso pode ser instanciado recebendo repositórios e serviços por injeção de dependência, sem depender de FastAPI ou de uma conexão real.

## Prompt de execução

Crie `app/funcionarios/application/services.py` com um serviço de aplicação assíncrono. Injete `FuncionarioRepository` e uma porta `IdempotencyKeyStore`; não instancie Motor dentro do serviço. No cadastro, normalize o comando, gere fingerprint estável do payload e implemente replay da mesma `Idempotency-Key`; reutilização com fingerprint diferente deve gerar conflito. Na atualização, exija `expected_version` e delegue a operação atômica ao repositório. Na exclusão, busque o funcionário e rejeite `ativo=true`. Converta duplicidade, não encontrado e versão obsoleta em exceções nomeadas. Mantenha os métodos pequenos, sem lógica de serialização HTTP. Siga TDD: escreva testes unitários para cada caso de uso, incluindo sucesso, validação, idempotência, conflito de versão e exclusão bloqueada, usando apenas doubles injetados.