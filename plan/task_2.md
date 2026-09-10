# Task 2 — Modelar o domínio de funcionários

## Objetivo

Implementar a entidade `Funcionario`, objetos de valor e exceções de domínio sem dependência de FastAPI, Pydantic, Motor ou MongoDB.

## Principais entregas

- Entidade com `nome_completo`, `email`, `cargo`, `data_admissao`, campos opcionais, `ativo`, timestamps e `version`.
- Normalização e validação de e-mail em objeto de valor.
- Regras de imutabilidade de e-mail e data de admissão.
- Regra que bloqueia exclusão de funcionário ativo.
- Exceções de domínio para validação, duplicidade, recurso inexistente e conflito de versão.
- Testes unitários do objeto de valor, entidade e regras de negócio.

## Critério de pronto

Todas as regras de negócio podem ser exercitadas chamando objetos Python puros, sem inicializar framework, banco ou servidor HTTP.

## Prompt de execução

Implemente o domínio em `app/funcionarios/domain`. Crie `entities.py`, `value_objects.py` e `exceptions.py`. Modele `Funcionario` como entidade Python com identidade própria, `version` iniciando em 1 e timestamps em UTC. Crie um objeto de valor para e-mail que remova espaços externos, normalize para minúsculas e rejeite formato inválido. Permita atualização somente de nome, cargo, telefone, departamento e ativo; e-mail e data de admissão devem permanecer imutáveis. Adicione um método explícito para verificar se a exclusão é permitida. Use dataclasses ou classes imutáveis quando isso tornar as invariantes claras. Não importe FastAPI, Pydantic, Motor ou BSON no domínio. Use exceções específicas, nomes em inglês no código e mensagens adequadas para tradução na camada HTTP. Antes de implementar cada regra, escreva testes unitários que falhem; depois implemente o mínimo e refatore mantendo os testes verdes.