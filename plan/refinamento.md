# Refinamento técnico: microserviço de cadastro de funcionários

## 1. Objetivo e escopo

Construir um microserviço Python para substituir gradualmente o módulo legado de cadastro de funcionários da TechNovaMBA Solutions.

O serviço será responsável por:

- cadastrar funcionários;
- consultar todos os funcionários ou filtrar por departamento e cargo;
- atualizar os campos permitidos;
- excluir funcionários que não estejam ativos em projetos;
- garantir unicidade de e-mail;
- expor uma API HTTP documentada automaticamente;
- persistir os dados em MongoDB;
- ser executado localmente e em ambientes containerizados.

Fora do escopo inicial:

- autenticação e autorização corporativas;
- integração com o monólito legado;
- gestão real de projetos;
- eventos assíncronos e mensageria;
- alteração de e-mail ou data de admissão após o cadastro.

## 2. Decisões técnicas

| Tema | Decisão |
|---|---|
| Linguagem | Python 3.12 ou superior |
| API | FastAPI |
| Validação e documentação | Pydantic v2 e OpenAPI gerado pelo FastAPI |
| Persistência | MongoDB 7 ou superior |
| Driver | PyMongo Async, mantendo acesso assíncrono à base |
| Testes | pytest, pytest-asyncio, httpx e pytest-cov |
| Qualidade | Ruff, mypy opcional e cobertura mínima de 90% |
| Containers | Docker e Docker Compose |
| Arquitetura | DDD leve, Ports and Adapters e separação por responsabilidade |

O domínio não deve importar FastAPI, Pydantic, PyMongo ou código de container. Essa regra mantém as decisões de infraestrutura substituíveis e facilita os testes unitários.

## 3. Modelo de domínio

### 3.1 Entidade `Funcionario`

Campos persistidos:

| Campo | Tipo | Obrigatório | Regra |
|---|---|---:|---|
| `_id` | `ObjectId` | Sim | Identificador técnico do MongoDB |
| `nome_completo` | string | Sim | Não vazio; tamanho máximo definido pelo contrato |
| `email` | string | Sim | Normalizado e único, preferencialmente em minúsculas |
| `cargo` | string | Sim | Não vazio |
| `data_admissao` | datetime UTC | Sim | Data válida de admissão |
| `telefone` | string | Não | Normalizado quando informado |
| `departamento` | string | Não | Normalizado quando informado |
| `ativo` | boolean | Sim | Padrão `false`; impede exclusão quando `true` |
| `created_at` | datetime UTC | Sim | Preenchido no cadastro |
| `updated_at` | datetime UTC | Sim | Atualizado em cada alteração |
| `version` | inteiro | Sim | Controle de concorrência otimista; inicia em `1` |

O domínio deve expor operações como `criar`, `atualizar_dados_permitidos` e `pode_ser_excluido`. A entidade não deve aceitar alteração de `email` nem `data_admissao` depois de criada.

### 3.2 Regras de negócio

1. O e-mail é normalizado com remoção de espaços nas extremidades e conversão para minúsculas.
2. Dois funcionários não podem ter o mesmo e-mail normalizado.
3. `email` e `data_admissao` são imutáveis após o cadastro.
4. Funcionário com `ativo=true` não pode ser excluído.
5. Atualizações devem informar a versão esperada. Versão desatualizada resulta em conflito, sem sobrescrever alterações mais recentes.
6. Listagens devem ter paginação limitada para evitar respostas sem limite.
7. Datas trafegadas pela API devem usar ISO 8601 e timezone UTC.

## 4. Estrutura modular DDD

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

### Responsabilidades

- `domain`: entidades, objetos de valor, regras e portas de repositório.
- `application`: casos de uso e orquestração, sem conhecer detalhes do MongoDB.
- `infrastructure`: conexão, índices, mapeamento BSON e implementação dos repositórios.
- `interfaces/http`: schemas de entrada/saída, rotas, status HTTP e dependências.
- `core`: configuração, logging, tratamento de erros e preocupações transversais.

## 5. Contrato da API

### `POST /funcionarios`

Cria um funcionário.

Entrada:

```json
{
  "nome_completo": "Ada Lovelace",
  "email": "ada.lovelace@technova.example",
  "cargo": "Engenheira de Software",
  "data_admissao": "2026-01-15",
  "telefone": "+55 47 99999-9999",
  "departamento": "Tecnologia"
}
```

Respostas:

- `201 Created`: funcionário criado.
- `409 Conflict`: e-mail já cadastrado.
- `422 Unprocessable Entity`: payload inválido.

### `GET /funcionarios`

Consulta paginada. Query parameters sugeridos:

```json
departamento=Tecnologia
cargo=Engenheira de Software
page=1
page_size=20
```

`page_size` deve ser limitado, por exemplo, entre `1` e `100`. A resposta deve conter `items`, `page`, `page_size` e `total` quando o custo da contagem for aceitável; caso contrário, pode usar paginação por cursor.

### `GET /funcionarios/{id}`

Retorna um funcionário ou `404 Not Found`.

### `PATCH /funcionarios/{id}`

Atualiza somente `nome_completo`, `cargo`, `telefone`, `departamento` e `ativo`. O schema não deve aceitar `email` nem `data_admissao`.

Entrada sugerida:

```json
{
  "cargo": "Staff Engineer",
  "version": 1
}
```

Respostas:

- `200 OK`: atualização concluída e versão incrementada.
- `404 Not Found`: funcionário inexistente.
- `409 Conflict`: versão obsoleta ou e-mail conflitante.
- `422 Unprocessable Entity`: payload inválido.

### `DELETE /funcionarios/{id}`

- `204 No Content`: funcionário removido.
- `404 Not Found`: funcionário inexistente.
- `409 Conflict`: funcionário está ativo em projetos.

## 6. Concorrência e idempotência

Para evitar sobrescrita perdida em vários containers, o repositório deve atualizar usando a versão esperada:

```python
result = await collection.update_one(
    {"_id": employee_id, "version": expected_version},
    {
        "$set": update_fields | {"updated_at": now},
        "$inc": {"version": 1},
    },
)
```

Se `matched_count == 0`, o caso de uso deve distinguir recurso inexistente de versão obsoleta e retornar `409 Conflict` para concorrência.

Para operações de criação que possam ser repetidas por timeout de rede, aceitar o header `Idempotency-Key`. A chave deve ser armazenada em uma coleção própria com índice único, fingerprint do payload, status e resposta. A mesma chave com payload diferente deve retornar `409 Conflict`; a mesma chave com o mesmo fingerprint deve devolver a resposta armazenada.

Em múltiplas réplicas, essa informação precisa ficar no MongoDB ou em outro armazenamento compartilhado. Um dicionário em memória e locks Python protegem somente um processo.

## 7. Boas práticas para MongoDB

1. Criar um banco por ambiente e obter a URI via variável de ambiente, nunca por hardcode.
2. Criar índices explicitamente no startup controlado ou em script idempotente, sem depender de criação implícita.
3. Criar índice único para o e-mail normalizado:

```javascript
db.funcionarios.createIndex(
  { email: 1 },
  { unique: true, name: "uq_funcionarios_email" }
)
```

4. Criar índices para os filtros mais usados, por exemplo:

```javascript
db.funcionarios.createIndex({ departamento: 1, cargo: 1 })
db.funcionarios.createIndex({ created_at: -1 })
```

5. Usar projeções e `limit` nas consultas; nunca retornar documentos sem limite.
6. Usar `ObjectId` internamente e serializar para string apenas no schema HTTP.
7. Usar UTC em todos os timestamps e configurar timeouts de conexão, seleção de servidor e operações.
8. Reutilizar um único `MongoClient` por processo e fechá-lo no shutdown da aplicação.
9. Validar o schema no Pydantic e, quando apropriado, adicionar validação JSON Schema no MongoDB.
10. Capturar `DuplicateKeyError` e convertê-lo para `409 Conflict`.
11. Evitar transações para uma única coleção; quando forem necessárias, usar replica set e medir o custo operacional.
12. Não expor stack traces, credenciais ou a URI de conexão nos logs.
13. Monitorar latência, erros, pool de conexões, uso de índices e tamanho das coleções.
14. Definir política de backup, restauração e retenção antes de produção.

## 8. Estratégia TDD e cobertura mínima

O ciclo de desenvolvimento deve ser:

1. Escrever um teste que falha para uma regra.
2. Implementar o mínimo para fazê-lo passar.
3. Refatorar mantendo os testes verdes.
4. Repetir para o próximo comportamento.

### Ordem recomendada

1. Testar `Email` e demais objetos de valor.
2. Testar criação e atualização da entidade.
3. Testar exclusão bloqueada quando `ativo=true`.
4. Testar casos de uso usando repositórios fake/in-memory.
5. Testar unicidade e versionamento no repositório Mongo com banco de teste.
6. Testar rotas com `httpx.AsyncClient` e `app.dependency_overrides`.
7. Testar contrato OpenAPI e códigos HTTP.

Configuração sugerida no `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--strict-markers --cov=app --cov-report=term-missing --cov-fail-under=90"
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

O pipeline deve falhar quando a cobertura total ficar abaixo de 90%. Além da média global, priorizar cobertura de todas as regras de negócio e dos caminhos de erro. Não contar somente testes de integração lentos como estratégia de cobertura.

## 9. Docker e Docker Compose

### Dockerfile de produção

Boas práticas:

- imagem base slim e versão fixada;
- usuário sem privilégios;
- dependências instaladas sem cache;
- processo iniciado diretamente pelo servidor ASGI;
- healthcheck separado da lógica da aplicação;
- nenhum segredo embutido na imagem.

Comando de execução esperado:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Dockerfile de desenvolvimento

Deve montar o código como volume e executar o Uvicorn com `--reload`, sem ser usado em produção.

### Compose local

O `compose.yaml` deve conter:

- serviço `api`;
- serviço `mongodb` com volume nomeado;
- rede interna;
- variáveis via `.env` ou `env_file`;
- `healthcheck` do MongoDB;
- dependência da API condicionada à saúde do Mongo;
- portas explicitamente documentadas.

Exemplo de variáveis:

```env
MONGO_URI=mongodb://mongodb:27017
MONGO_DATABASE=technova_funcionarios
API_PORT=8000
```

O `.env` real deve estar no `.gitignore`; versionar apenas `.env.example` sem segredos.

## 10. Setup inicial

Executar na raiz `lab-ms-python/ms-cadastro-funcionario`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d mongodb
pytest
ruff check .
```

Depois iniciar a API:

```bash
uvicorn app.main:app --reload --port 8000
```

Documentação automática:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI: `http://localhost:8000/openapi.json`

Alternativamente, executar todo o ambiente:

```bash
docker compose up --build
```

## 11. Pipeline de desenvolvimento limpo

Antes de abrir um pull request:

```bash
ruff format --check .
ruff check .
mypy app
pytest
```

O pipeline CI deve executar, nesta ordem:

1. instalação limpa das dependências;
2. lint e formatação;
3. testes unitários;
4. testes de integração com MongoDB descartável;
5. cobertura com `--cov-fail-under=90`;
6. build da imagem Docker;
7. verificação de vulnerabilidades das dependências e da imagem;
8. publicação somente após todos os gates passarem.

Commits devem ser pequenos e descrever uma mudança de comportamento. Cada caso de uso novo deve chegar acompanhado de testes e atualização do contrato OpenAPI.

## 12. Definition of Done

Uma entrega está pronta quando:

- todas as regras da história possuem testes;
- cobertura total é igual ou superior a 90%;
- testes unitários não dependem de MongoDB;
- testes de integração validam índices, unicidade e versionamento;
- API documenta schemas e respostas de erro;
- e-mail e datas são normalizados conforme definido;
- exclusão de funcionário ativo é bloqueada;
- Docker Compose sobe a API e o Mongo com healthchecks;
- logs não expõem dados sensíveis;
- lint, testes, cobertura e build Docker passam no CI;
- README documenta setup, comandos e variáveis de ambiente.