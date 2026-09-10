# Task 4 — Configurar conexão e mapeamento MongoDB

## Objetivo

Implementar a infraestrutura de acesso ao MongoDB com Motor, ciclo de vida assíncrono e mapeamento explícito entre BSON e domínio.

## Principais entregas

- Cliente Motor criado uma única vez por processo.
- Configuração de URI, database e timeouts por ambiente.
- Lifecycle de conexão no startup/shutdown do FastAPI.
- Mapeadores entre documento MongoDB e entidade `Funcionario`.
- Tratamento controlado de `DuplicateKeyError` e erros de conexão.
- Testes unitários dos mapeadores e testes de infraestrutura com cliente substituível.

## Critério de pronto

O aplicativo abre e encerra corretamente o cliente MongoDB, sem criar conexão por requisição, e o domínio permanece independente de BSON.

## Prompt de execução

Implemente `app/funcionarios/infrastructure/mongo_client.py` usando Motor AsyncIOMotorClient, com uma instância por processo, `serverSelectionTimeoutMS`, `connectTimeoutMS` e `timeoutMS` configuráveis. Crie funções de lifecycle para conectar, executar ping e fechar o cliente com segurança. Implemente `mongo_models.py` para converter `Funcionario` em documento BSON e documento em entidade, convertendo `ObjectId` para o identificador de domínio apropriado. Encapsule dependências do Motor atrás de uma factory ou provider. Não espalhe chamadas ao Mongo pelo projeto. Capture `DuplicateKeyError` na infraestrutura e traduza para uma exceção de domínio/aplicação apropriada. Use logging sem credenciais ou URI completa. Escreva testes para round-trip dos mapeadores, configuração de timeouts, lifecycle e tradução de erros usando doubles, sem depender de um Mongo real nos testes unitários.