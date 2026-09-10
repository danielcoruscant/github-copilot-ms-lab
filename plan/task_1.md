# Task 1 — Inicializar o projeto Python

## Objetivo

Criar a base executável do microserviço, com dependências, configuração de qualidade e estrutura inicial de pacotes.

## Principais entregas

- `pyproject.toml` com Python 3.12+, FastAPI, Pydantic v2, Motor, Uvicorn, Ruff e mypy.
- Pacote `app/` com `__init__.py` e ponto de entrada `app/main.py`.
- Estrutura modular DDD para `core`, `funcionarios` e `health`.
- Camadas `domain`, `application`, `infrastructure` e `interfaces/http` preparadas para evolução incremental.
- Diretórios `tests/unit`, `tests/integration` e `tests/contract` preparados para TDD.
- `.env.example`, `.gitignore` e configuração inicial de logging.
- Comandos documentados para instalação e execução local.
- Testes smoke de configuração, importação da aplicação e health check.

## Critério de pronto

O projeto instala suas dependências em um ambiente virtual, inicia uma aplicação FastAPI mínima e expõe uma rota de health check sem acoplar código de negócio à infraestrutura.

## Estrutura modular DDD

```plaintext
ms-cadastro-funcionario/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── errors.py
│   │   └── logging.py
│   ├── funcionarios/
│   │   ├── domain/
│   │   │   ├── entities.py
│   │   │   ├── value_objects.py
│   │   │   ├── exceptions.py
│   │   │   └── repositories.py
│   │   ├── application/
│   │   │   ├── commands.py
│   │   │   ├── queries.py
│   │   │   └── services.py
│   │   ├── infrastructure/
│   │   │   ├── mongo_client.py
│   │   │   ├── mongo_models.py
│   │   │   └── repositories.py
│   │   └── interfaces/
│   │       └── http/
│   │           ├── routes.py
│   │           ├── schemas.py
│   │           └── dependencies.py
│   └── health/
│       └── routes.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── scripts/
│   └── create_indexes.py
├── Dockerfile
├── Dockerfile.dev
├── compose.yaml
├── pyproject.toml
├── .env.example
└── README.md
```

Nesta etapa, crie os pacotes e arquivos-base necessários para estabelecer essa organização, mesmo que algumas implementações sejam apenas pontos de extensão. O domínio deve permanecer independente de FastAPI, Pydantic, Motor e MongoDB.

## Prompt de execução

Crie a estrutura inicial do microserviço em Python 3.12 dentro de `ms-cadastro-funcionario`, seguindo a árvore modular DDD descrita nesta Task. Configure `pyproject.toml` com FastAPI, Pydantic v2, Motor, Uvicorn, Ruff, pytest, pytest-asyncio, httpx e pytest-cov, mantendo dependências de produção separadas das de desenvolvimento. Crie os pacotes e arquivos-base em `app/core`, `app/funcionarios/domain`, `app/funcionarios/application`, `app/funcionarios/infrastructure`, `app/funcionarios/interfaces/http` e `app/health`, além de `app/main.py`, com `__init__.py` onde aplicável. Prepare também `tests/unit`, `tests/integration`, `tests/contract`, `scripts/create_indexes.py`, `Dockerfile`, `Dockerfile.dev`, `compose.yaml`, `.env.example` e `README.md` como pontos de extensão coerentes com o refinamento. Implemente uma FastAPI mínima com `GET /health`, mantendo a composição inicial simples. Use nomes em snake_case para módulos, classes em PascalCase e funções em snake_case. Centralize configuração por variáveis de ambiente usando Pydantic Settings, sem credenciais hardcoded. Inclua `.gitignore` para `.env`, `.venv`, caches e artefatos, e logging estruturado básico. Crie testes smoke para validar a criação da aplicação, a configuração essencial e a resposta de `GET /health`; mantenha-os independentes de MongoDB. Preserve o desacoplamento: o domínio não pode importar FastAPI, Pydantic, Motor ou MongoDB.