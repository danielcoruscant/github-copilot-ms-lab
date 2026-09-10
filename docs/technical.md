# Documentação técnica

## 1. Visão geral

`ms-cadastro-funcionario` é um microserviço para cadastro de funcionários da TechNovaMBA Solutions. O serviço substitui gradualmente um módulo legado e oferece uma API HTTP para criar, consultar, atualizar e excluir funcionários.

Tecnologias principais:

- Python 3.12+;
- FastAPI e Pydantic v2;
- Motor/PyMongo para acesso assíncrono ao MongoDB;
- MongoDB 7;
- pytest, pytest-cov, Ruff e mypy;
- Docker e Docker Compose.

## 2. Arquitetura

A aplicação usa DDD leve com Ports and Adapters:

```plaintext
app/
├── core/                         # configuração, erros e logging
├── funcionarios/
│   ├── domain/                   # entidade, value objects e portas
│   ├── application/              # comandos, queries e casos de uso
│   ├── infrastructure/           # MongoDB, repositórios e idempotência
│   └── interfaces/http/          # schemas, rotas e dependências FastAPI
├── health/                       # health e readiness
└── main.py                       # composition root e lifecycle
```

Dependências permitidas:

```plaintext
interfaces/http -> application -> domain
infrastructure -> domain
main -> todas as implementações
```

O domínio não importa FastAPI, Pydantic, Motor ou BSON. Isso permite testar as regras com objetos Python puros e trocar adaptadores sem alterar o núcleo.

## 3. Modelo de funcionário

A entidade `Funcionario` possui:

- `id`: UUID técnico;
- `nome_completo`: obrigatório;
- `email`: value object normalizado em minúsculas;
- `cargo`: obrigatório;
- `data_admissao`: data imutável;
- `telefone` e `departamento`: opcionais;
- `ativo`: impede exclusão quando verdadeiro;
- `created_at` e `updated_at`: timestamps UTC;
- `version`: controle otimista, iniciado em 1.

E-mail e data de admissão não podem ser alterados após o cadastro. Atualizações usam a versão esperada e geram conflito quando estão desatualizadas.

## 4. Contrato HTTP

### `POST /funcionarios`

Requer o header:

```http
Idempotency-Key: cadastro-001
```

Exemplo:

```bash
curl -i -X POST http://localhost:8000/funcionarios \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: cadastro-001' \
  -d '{"nome_completo":"Ada Lovelace","email":"ada@example.com","cargo":"Engenheira","data_admissao":"2026-01-15","departamento":"Tecnologia"}'
```

Respostas principais:

- `201`: criado;
- `409`: chave de idempotência conflitante ou e-mail duplicado;
- `422`: payload inválido.

### `GET /funcionarios`

Parâmetros:

- `departamento` opcional;
- `cargo` opcional;
- `page`, mínimo 1;
- `page_size`, entre 1 e 100.

```bash
curl 'http://localhost:8000/funcionarios?departamento=Tecnologia&page=1&page_size=20'
```

### `GET /funcionarios/{id}`

Retorna um funcionário ou `404`.

### `PATCH /funcionarios/{id}`

Atualiza somente `nome_completo`, `cargo`, `telefone`, `departamento` e `ativo`. O campo `version` é obrigatório:

```bash
curl -i -X PATCH http://localhost:8000/funcionarios/UUID \
  -H 'Content-Type: application/json' \
  -d '{"cargo":"Staff Engineer","version":1}'
```

Respostas: `200`, `404`, `409` ou `422`.

### `DELETE /funcionarios/{id}`

Retorna `204` quando remove um funcionário inativo. Retorna `409` se ele estiver ativo em projeto.

### Documentação automática

FastAPI gera automaticamente a documentação OpenAPI a partir dos schemas Pydantic e das declarações das rotas:

- Swagger UI: `http://localhost:8000/docs`;
- ReDoc: `http://localhost:8000/redoc`;
- especificação OpenAPI em JSON: `http://localhost:8000/openapi.json`.

Esses endpoints ficam disponíveis tanto na execução local quanto na execução via Docker Compose, desde que a API esteja acessível na porta `8000`.

## 5. Idempotência distribuída

A coleção `idempotency_keys` é compartilhada entre pods. A reserva é feita atomicamente por `find_one_and_update` com `upsert`.

Estados:

- `processing`: uma requisição possui o lease;
- `completed`: a resposta está armazenada e pode ser reproduzida.

A mesma chave com fingerprint diferente retorna `409`. Um lease expirado pode ser recuperado por outra requisição. O índice único em `key` impede reservas duplicadas e o índice TTL em `expires_at` limpa registros antigos.

## 6. MongoDB

Coleções:

- `funcionarios`;
- `idempotency_keys`.

Índices de funcionários:

- `uq_funcionarios_email`: único;
- `ix_funcionarios_departamento_cargo`;
- `ix_funcionarios_created_at`.

Índices de idempotência:

- `uq_idempotency_keys_key`: único;
- `ttl_idempotency_keys_expires_at`: TTL.

Os índices são criados pelo lifecycle da aplicação ou manualmente com:

```bash
python scripts/create_indexes.py
```

A conexão usa um único `AsyncIOMotorClient` por processo, com URI e timeouts em variáveis de ambiente. A aplicação não loga a URI nem credenciais.

## 7. Configuração

Copie `.env.example` para `.env`:

```env
APP_NAME=ms-cadastro-funcionario
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=technova_funcionarios
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000
MONGO_CONNECT_TIMEOUT_MS=5000
MONGO_OPERATION_TIMEOUT_MS=5000
IDEMPOTENCY_RETENTION_SECONDS=86400
IDEMPOTENCY_LEASE_SECONDS=300
```

Nunca versione `.env` real.

## 8. Execução local

```bash
cd lab-ms-python/ms-cadastro-funcionario
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d mongodb
python scripts/create_indexes.py
uvicorn app.main:app --reload --port 8000
```

`/health` verifica apenas o processo. `/ready` verifica a disponibilidade do MongoDB.

## 9. Debug local

No VS Code:

1. Selecione `.venv/bin/python` com `Python: Select Interpreter`.
2. Abra **Run and Debug**.
3. Escolha `Debug FastAPI - Cadastro Funcionarios`.
4. Pressione `F5`.
5. Adicione breakpoints no editor.

O launch usa o módulo `uvicorn` sem `--reload` para manter o processo de debug único.

## 10. Docker Compose

```bash
cd lab-ms-python/ms-cadastro-funcionario
cp .env.example .env
docker compose up --build
```

Serviços:

- `mongodb`: MongoDB 7 com volume `mongodb_data` e healthcheck;
- `api`: FastAPI com Dockerfile de desenvolvimento, volume de código e reload.

A API só é iniciada após o Mongo passar no healthcheck. Para observar:

```bash
docker compose ps
docker compose logs -f api mongodb
```

Para limpar dados:

```bash
docker compose down -v
```

Para produção, use o `Dockerfile`, uma imagem versionada, secrets externos, usuário não-root e um MongoDB gerenciado ou cluster com backup.

## 11. Testes e qualidade

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy app
```

A suíte exige cobertura mínima de 90%. Para relatório HTML/XML:

```bash
.venv/bin/python -m pytest \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov \
  --cov-fail-under=90
```

## 12. Troubleshooting

### Porta 8000 ocupada

```bash
uvicorn app.main:app --reload --port 8001
```

### Mongo indisponível

```bash
docker compose ps
docker compose logs mongodb
curl -i http://localhost:8000/ready
```

O processo pode estar vivo em `/health` mesmo quando `/ready` retorna `503`.

### Testes não descobertos

Execute a partir do diretório do microserviço e use o interpretador do `.venv`:

```bash
cd lab-ms-python/ms-cadastro-funcionario
.venv/bin/python -m pytest
```

Evite executar `pytest` na raiz geral do workspace, que contém outro projeto Python.

## 13. Definition of Done

A base está pronta quando:

- `docker compose up --build` sobe Mongo e API;
- `/health`, `/ready`, `/docs` e `/redoc` estão disponíveis;
- índices são criados idempotentemente;
- idempotência e versionamento são persistidos por adaptadores apropriados;
- testes, lint, formatação e mypy passam;
- cobertura permanece acima de 90%;
- nenhum segredo é versionado;
- este README e esta documentação técnica refletem o setup atual.
