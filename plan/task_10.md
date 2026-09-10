# Task 10 — Containerizar e documentar a base

## Objetivo

Entregar a base executável localmente com Docker Compose, configuração segura e documentação de desenvolvimento.

## Principais entregas

- `Dockerfile` de produção com imagem slim, usuário não-root e comando ASGI.
- `Dockerfile.dev` com volume e reload para desenvolvimento.
- `compose.yaml` com API, MongoDB, volume, rede e healthcheck.
- `.env.example` completo e `.dockerignore`.
- `README.md` com setup, comandos, endpoints e limites conhecidos.
- Script idempotente de criação de índices, quando não executado pelo lifecycle.
- Testes de smoke da imagem e validação do ambiente Compose.

## Critério de pronto

`docker compose up --build` inicia Mongo e API em ordem saudável, a documentação está acessível e nenhuma credencial real ou dependência gerada é versionada.

## Prompt de execução

Crie Dockerfile de produção para Python 3.12 usando imagem slim fixada, instalação sem cache, usuário não-root e `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Crie Dockerfile.dev com volume do código e `--reload`, deixando claro que ele não é para produção. Configure `compose.yaml` com serviços `api` e `mongodb`, volume persistente, rede interna, variáveis via `.env`, healthcheck do Mongo com `mongosh` e `depends_on` condicionado à saúde. Não embuta segredos nas imagens. Adicione `.dockerignore` para `.venv`, caches, `.git` e arquivos locais. Documente setup local e via Compose, Swagger, ReDoc, variáveis, migração de índices, comandos Ruff e limitações do escopo. Organize nomes de serviços, imagens e variáveis de modo consistente. Crie testes de smoke para validar o build, o healthcheck, a disponibilidade da API e a conectividade com Mongo em ambiente Compose; mantenha os testes reproduzíveis e integrados ao comando de CI com cobertura mínima de 90%.