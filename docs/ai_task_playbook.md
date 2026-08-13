# Playbook de execução das tasks por IA

## 1. Regra principal

Uma execução trabalha em uma task `ECO-XXXX` desbloqueada. Dependência faltante não pode ser implementada implicitamente se ampliar materialmente o escopo.

## 2. Mini-brief obrigatório antes de editar

Registrar no plano/comentário de trabalho:

```text
Task:
Objetivo observável:
Dependências verificadas:
Documentos lidos:
Arquivos esperados:
Contrato/schema afetado:
Dados e ambiente:
Testes que serão executados:
Fora do escopo:
Riscos/ações que exigem aprovação:
```

Se algum campo essencial for desconhecido e alterar a arquitetura, pare. Se for descobrível por leitura local, investigue sem perguntar.

## 3. Ciclo de execução

1. Confirmar que a task e dependências existem.
2. Ler AGENTS, spec, task, ADR e referência específica.
3. Inspecionar estado atual e alterações do usuário.
4. Produzir mini-brief e plano curto.
5. Implementar o menor incremento vertical completo.
6. Executar testes de baixo custo primeiro; ampliar conforme risco.
7. Para Supabase: testar query/policy, rodar advisors e verificar migration list antes de concluir.
8. Revisar diff/arquivos, segredos, mocks e docs.
9. Atualizar checklist somente se todos os aceites forem verdadeiros.
10. Entregar evidências, riscos e próxima task desbloqueada.

## 4. Pacotes de referência por marco

| Marco | Ler obrigatoriamente | Áreas esperadas | Evidência mínima |
|---|---|---|---|
| 0 | spec, ADRs, índice | `docs/`, OpenAPI | decisão/contrato validado |
| 1 | ADR 0002, DEVELOPMENT, testing | `backend/`, `supabase/` | health, migration list, smoke PostGIS |
| 2 | spec §6, Supabase rules | migrations, models | constraints + matriz RLS |
| 3 | contrato Pindobal | ingestion, fixtures | dry-run, hashes, relatório/contagens |
| 4 | spec §8, políticas Google | connectors/jobs | mocks, retry, orçamento, nenhum segredo |
| 5 | OpenAPI, spec §7 | API/services/repos | contrato e integração |
| 6 | ADR 0002, AC-SEC | auth/profile/favorites | tokens + isolamento A/B |
| 7 | ADR 0001, Expo AGENTS | `src/api`, hooks, state | types, cache, erros |
| 8 | AC-GLOBAL/HOME/ROUTES | tabs/components | fluxo + acessibilidade |
| 9 | ADR 0003, AC-ROUTE/MAP | route/map adapter | três origens + mapa real |
| 10 | AC-CATALOG | catalog/actor | deep link, favorito, contatos |
| 11 | AC-PROFILE | profile/new screens | todos os itens ativos |
| 12 | testing, acceptance | CI/staging/release | matriz completa e auditorias |

## 5. Detalhe mínimo de cada categoria de task

### Schema/migration

- Listar tabelas/colunas/constraints/índices/grants/policies afetados.
- Criar migration pelo Supabase CLI da versão instalada.
- Demonstrar teste positivo e negativo.
- Não editar schemas gerenciados.
- Registrar estratégia de rollback compatível; não prometer downgrade destrutivo automático.

### Endpoint FastAPI

- Atualizar OpenAPI/schema antes ou junto do código.
- Implementar router → service → repository.
- Validar JWT/ownership quando protegido.
- Cobrir erro 401/403/404/422/5xx relevante.
- Não acessar Google/OSRM em request de leitura comum.

### Conector/importador

- Client isolado, timeouts, retries limitados e rate/cost guard.
- Fixtures contratuais e nenhuma rede no CI.
- Dry-run, idempotência, proveniência e relatório.
- Nunca sobrescrever fonte de maior autoridade silenciosamente.

### Frontend/query

- Tipos gerados/validados.
- Query key inclui região/rota/origem/filtros relevantes.
- Loading, vazio, erro, retry e offline.
- Mutation otimista apenas com rollback.
- Testar leitor de tela/foco e alvo independente de botões aninhados.

### Mapa

- Payload e adapter separados.
- Testar câmera/zoom, origem, bounds, pins, filtros e deep-link.
- Evidência visual por plataforma aprovada.

## 6. Arquivos esperados por domínio

Depois do scaffold, usar esta convenção; divergência exige atualização do documento:

```text
backend/app/api/v1/          routers
backend/app/services/        regras de negócio
backend/app/repositories/    persistência
backend/app/connectors/      Google/OSRM/Supabase auxiliares
backend/app/ingestion/       pipeline Pindobal
backend/tests/               testes/fixtures
supabase/migrations/         schema, grants, RLS, policies, funções
econexao-app/src/api/        client HTTP e contratos
econexao-app/src/hooks/      queries/mutations
econexao-app/src/state/      sessão/preferências/UI global
econexao-app/app/            telas/rotas
```

## 7. Formato de entrega

```text
Resultado:
Task concluída: sim/não
Arquivos alterados:
Contratos/migrations:
Testes executados e resultados:
Verificações Supabase/RLS:
Riscos ou limitações:
Próxima task desbloqueada:
```

Não afirmar “concluído” se um teste obrigatório não pôde ser executado; registrar a task como parcial e explicar o bloqueio.

## 8. Divisão de tasks grandes

Tasks `L` devem ser divididas internamente em subtarefas sequenciais, preservando o mesmo ID:

1. contrato/schema.
2. implementação happy path.
3. autorização/erros.
4. testes.
5. integração/aceite/documentação.

Não marque a task principal antes das cinco partes aplicáveis.

## 9. Proibições

- Produção para desenvolvimento/teste.
- Segredos em prompt, log, fixture ou commit.
- Alteração manual de schema sem migration.
- Fallback silencioso para mock.
- Atualizar dependências sem necessidade e verificação.
- Refactor amplo fora da task.
- Repetir chamada externa até “funcionar” sem diagnosticar quota/política.
- Marcar checkbox baseado apenas em código escrito.
