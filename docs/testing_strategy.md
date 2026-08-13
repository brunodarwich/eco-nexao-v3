# Estratégia de testes

## Objetivo

Dar a agentes um caminho verificável sem acessar produção ou APIs externas durante testes.

## Ambientes

- Unitários: sem rede e sem Supabase.
- Integração: projeto Supabase `test`, exclusivo e descartável.
- Contrato: servidor HTTP simulado para Google/OSRM e FastAPI real.
- E2E: Supabase `test` ou `staging`, nunca production.

## Backend

### Unitários

- Normalização de nome, telefone, URL, categoria e horário.
- Parsing/coordenadas/LineString.
- Deduplicação determinística e score fuzzy.
- Autorização e mapeamento de erros.

### Integração Supabase/PostGIS

- Aplicação ordenada de migrations.
- Extensão PostGIS e índices espaciais.
- Importador Pindobal idempotente e dry-run.
- Queries de proximidade, posição na linha e bounds.
- RLS por matriz de identidades.
- Storage policies e upsert.

Matriz RLS mínima para cada tabela por usuário:

| Operação | anon sem sessão | usuário A dono | usuário B | backend autorizado |
|---|---:|---:|---:|---:|
| SELECT | negar | permitir | negar | conforme serviço |
| INSERT | negar | permitir com próprio ID | negar ID alheio | conforme serviço |
| UPDATE | negar | permitir próprio | negar | conforme serviço |
| DELETE | negar | permitir próprio | negar | conforme serviço |

Tabelas territoriais públicas terão matriz própria e grants explícitos.

### Conectores

- Fixtures de resposta Places API (New), incluindo paginação, quota, timeout, place movido e campo ausente.
- Fixture OSRM válida/inválida.
- Nenhum teste chama endpoint externo real.

## Frontend

- Componentes: estados e acessibilidade.
- Hooks/client: cache, invalidação, refresh e erros.
- Integração: busca com debounce, filtros e mutations otimistas.
- E2E: cenários de `docs/acceptance_criteria.md`.
- Mapa: teste lógico do adapter + verificação visual por plataforma.

## Comandos normativos

Os comandos do backend abaixo foram materializados e verificados na
ECO-0104. Os comandos do frontend e Supabase permanecem planejados até as
tasks correspondentes.

```powershell
# Backend
cd backend
python -m pytest
python -m pytest --cov=app --cov-report=term
python -m ruff check .
python -m mypy app

# Frontend
cd econexao-app
npm test
npm run typecheck
npm run openapi:check

# Supabase (planejado; descobrir flags na versão instalada)
supabase --version
supabase db --help
supabase migration --help
supabase db advisors
```

Não declarar um comando como aprovado enquanto o script não existir e tiver sido executado.

## Evidência por task

- Comando exato.
- Código de saída.
- Resumo dos testes.
- Ambiente utilizado sem credenciais.
- Screenshot somente quando layout/mapa for parte do aceite.
- Queries de verificação para migrations, sem dados pessoais.

## Gates

- PR/task de schema: migrations + advisors + RLS + smoke query.
- PR/task de API: unitário + integração + contrato OpenAPI.
- PR/task de UI: typecheck + componentes + fluxo relevante.
- Mapa: Android, iOS e web conforme ADR.
- Release: todos os ACs P0, auditoria de segredo e ausência de mock de produção.
