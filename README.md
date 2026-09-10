# ms-cadastro-funcionario

Microserviço de cadastro de funcionários da TechNovaMBA Solutions, construído em Python com FastAPI, DDD modular, MongoDB e Docker.
Projeto totalmente criado com GitHub Copilot como laboratório de estudos.

## Requisitos

- Python 3.12 ou superior
- Docker Engine e Docker Compose v2 para execução containerizada
- VS Code com a extensão Python para execução/debug local

## Execução local

```bash
cd lab-ms-python/ms-cadastro-funcionario
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
```

Para subir somente o MongoDB localmente:

```bash
docker compose up -d mongodb
```

Para criar/revalidar os índices:

```bash
python scripts/create_indexes.py
```

Para iniciar a API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints de operação:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/ready`

Documentação automática da API:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Especificação OpenAPI JSON: `http://localhost:8000/openapi.json`

## Debug local no VS Code

1. Selecione o interpretador `lab-ms-python/ms-cadastro-funcionario/.venv/bin/python`.
2. Crie `.env` com `cp .env.example .env`.
3. Abra **Run and Debug**.
4. Selecione `Debug FastAPI - Cadastro Funcionarios`.
5. Pressione `F5` e coloque breakpoints nos arquivos Python.

A configuração está em `.vscode/launch.json` e inicia Uvicorn sem `--reload`, evitando processos filhos que dificultam breakpoints.

## Docker Compose

```bash
cd lab-ms-python/ms-cadastro-funcionario
cp .env.example .env
docker compose up --build
```

A API aguarda o healthcheck do MongoDB e fica disponível em `http://localhost:8000`. Para acompanhar:

```bash
docker compose ps
docker compose logs -f api
```

Com a API em execução via Compose, a documentação também fica disponível em:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Especificação OpenAPI JSON: `http://localhost:8000/openapi.json`

Para encerrar sem remover os dados:

```bash
docker compose down
```

Para remover também o volume MongoDB:

```bash
docker compose down -v
```

## Testes e qualidade

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy app
```

Os testes executam cobertura com limite mínimo de 90%, definido no `pyproject.toml`.

## Documentação técnica

Consulte [docs/technical.md](docs/technical.md) para arquitetura, configuração, contrato HTTP, MongoDB, idempotência, troubleshooting e operação.
