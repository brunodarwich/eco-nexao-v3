# Relatório de Verificação e Evidências — ECO-2605: Generalização da Ingestão Territorial Multirrotas

Data: 2026-09-06  
Status da Tarefa: `CONCLUÍDA LOCAL` — Pipeline generalizado, validações estritas, 16 testes unitários/integração e gate de persistência real executado e homologado contra banco Supabase de teste gerenciado (`xlejwfmpeaubsdctguyx`) com PostgreSQL 17 / PostGIS 3.3.7, RLS, 26 migrations oficiais sincronizadas, rollback atômico e idempotência estrita (zero duplicatas).  
Status de Homologação das Rotas:
- **Rota Pindobal:** `DRAFT TÉCNICO` (permanece em `status: draft`, `is_verified: false` conforme ADR 0006 e fluxo de publicação)  
- **Rota Altamira / Xingu:** `FIXTURE` (permanece em `status: draft`, `is_verified: false`)  
Executor: Antigravity  
Worktree / Branch: `.worktrees/eco-2605` (`eco-2605-multi-route-import`)  
Commit-base: `2028908` (ECO-2604 — padronização do pacote de dados)

---

## 1. Objetivo

A tarefa **ECO-2605** generaliza o pipeline de ingestão do ECOnexão para que múltiplas rotas e regiões possam ser lidas, auditadas, validadas e persistidas a partir dos pacotes padronizados na ECO-2604, sem duplicações, com suporte a transação/rollback e rastreamento completo de proveniência.

Foram produzidos e verificados:
1. **Parser e Validador Estrutural (`backend/app/ingestion/route_package_parser.py`):**
   - Extrai tabelas GFM e blocos YAML da Seção 5 de cada pacote Markdown.
   - Schemas Pydantic v2 fortemente tipados: `RouteMetadataSchema`, `RouteOriginSchema`, `RouteGeometryMetadataSchema`, `RouteActorPackageSchema`, `ActorLocationSchema`, `ActorContactsSchema`, `ActorOperationalSchema`, `ActorProvenanceSchema`.
   - Normaliza `VALOR_AUSENTE` para `None` sem perda de integridade.
   - **Validação Estrita de Geometrias:** Provedor restrito a `{"osrm", "google_routes", "postgis"}`; CRS estritamente `4326`; `bounds` validado com 4 floats em intervalo geográfico e ordem `min_lon < max_lon` / `min_lat < max_lat`; SHA-256 com 64 caracteres hexadecimais; `points_count > 0`; `distance_m >= 0`.
   - **Proveniência Contratual Estrita:** `google_place_id` exige `has_verified_places_source: true`. Place IDs arbitrários rejeitados com `ValidationError`. Ratings/reviews sem Place ID bloqueados. URIs com `cid=` vetadas.
   - **Taxonomia Canônica (ADR 0010 e ADR 0015):** Exige pertencimento a 1 dos 8 grupos protegidos e subtipo válido.
2. **Repositório Atômico e Idempotente (`backend/app/ingestion/route_package_repository.py`):**
   - **Sem Fallbacks de Coordenada Inventados:** Coordenadas hardcoded removidas. Se o pacote não possuir origens verificadas, ingestão é rejeitada com `ValueError`.
   - Persiste atomicamente em transação única (`async with self.session.begin()`): `external_sources` → `ingestion_runs` → `regions` → `routes` → `route_origins` → `route_geometries` → `actors` → `route_actors` → `actor_external_refs` → `field_provenance` → `raw_source_records`.
   - Suporte nativo a `fail_after` para comprovação de rollback integral.
   - Idempotência estrita: reexecuções produzem `created = 0`, `updated = 0`, `unchanged = N`.
3. **Serviço de Dry-Run Honesto (`backend/app/ingestion/route_package_importer.py`):**
   - `run_route_package_dry_run` inspeciona o pacote sem banco e gera relatório JSON com `"is_estimate": true` e nota explicativa.
   - `run_route_package_apply` para aplicação controlada.
4. **CLI com Guardrail de Isolamento (`backend/app/ingestion/seed_route_package.py`):**
   - Padrão: `--dry-run`. A opção `--apply` exige `--env-file` com `APP_ENV=test`.
5. **Fixture de Segunda Rota (`backend/tests/fixtures/route_packages/altamira_xingu_package.md`):**
   - Rota Volta Grande do Xingu, região `xingu-altamira`, 2 origens, 2 geometrias OSRM, 3 atores de grupos distintos.
6. **Protocolo de Publicação (`docs/catalogo_territorial/fluxo_publicacao_primeira_rota.md`):**
   - Máquina de estados `draft` → `review` → `published`, Regra de Ouro da Região e checklist de transição.

---

## 2. Cobertura de Testes Automatizados

Suite dedicada `backend/tests/test_route_package_importer.py` — **16 testes, todos aprovados**:

1. `test_parser_loads_pindobal_package` — leitura completa com 3 origens, 3 geometrias, 5 atores.
2. `test_parser_loads_altamira_fixture_package` — segunda rota com 2 origens, 2 geometrias, 3 atores.
3. `test_reject_invented_google_place_id_with_rating` — rejeição de rating sem Place ID.
4. `test_reject_artificial_cid_urls` — bloqueio de URIs com `cid=`.
5. `test_reject_non_canonical_category` — rejeição de categoria fora dos 8 grupos canônicos.
6. `test_reject_unmatched_geometry_origin_code` — rejeição de geometria com origem inexistente.
7. `test_reject_unverified_google_place_id` — rejeição de Place ID sem `has_verified_places_source: true`.
8. `test_reject_invalid_bounds` — rejeição de bounds com inversão lat/lon.
9. `test_reject_invalid_sha256_hash` — rejeição de hash fora do padrão de 64 hex chars.
10. `test_reject_invalid_provider_and_crs` — rejeição de provedores não homologados e CRS ≠ 4326.
11. `test_reject_region_resolution_without_origins` — rejeição de ingestão sem origens comprovadas.
12. `test_dry_run_pindobal_package` — dry-run honesto com `is_estimate: True`.
13. `test_dry_run_altamira_package` — dry-run honesto para fixture Altamira.
14. `test_persist_adds_complete_package_inside_transaction` — persistência atômica com mock de sessão.
15. `test_induced_failure_triggers_rollback` — rollback com `fail_after="route"` via mock.
16. `test_idempotent_reexecution_produces_zero_duplicates` — idempotência via mock.

> **Nota importante:** Os testes 14, 15 e 16 usam `AsyncMock` de sessão (SQLAlchemy), não banco real. O gate de persistência contra banco real PostgreSQL/PostGIS com schema do projeto ainda não foi executado — ver seção 4.

---

## 3. Evidências dos Comandos e Verificações (2026-09-05)

| Comando | Exit | Resultado |
|---------|------|-----------|
| `python -m pytest tests/test_route_package_importer.py -q` | **0** | 16 passed in 3.48s |
| `python -m pytest tests/test_pindobal_persistence.py tests/test_semtur_persistence.py -q` | **0** | 14 passed in 2.49s |
| `python -m pytest tests/ -q` | **0** | 676 passed, 16 warnings in 34.56s |
| `ruff check .` | **0** | All checks passed! |
| `mypy app/ --ignore-missing-imports` | **0** | Success: no issues found in 99 source files |
| `git diff --check` | **0** | Sem erros de whitespace |
| `python scripts/scan_secrets.py` | **0** | `SECRET_SCAN=OK` |
| `docker ps` | **1** | Docker Desktop não estava rodando |
| `psql --version` / `pg_isready` | **1** | PostgreSQL CLI não encontrado no PATH local |

Versão Python: `3.13.13` | Ruff: `0.16.2` | mypy: `1.17.1`

---

---

## 4. Status do Gate de Persistência Real — CONCLUÍDO (VERIFIED em Banco de Teste Real)

Em 06/09/2026, com GO explícito do proprietário e garantia fail-closed de isolamento (`backend/.env.test` apontando exclusivamente para o projeto de teste Supabase gerenciado `xlejwfmpeaubsdctguyx`), o gate real de persistência foi executado com sucesso:

### Evidências no Projeto Supabase de Teste:
1. **Migrations Aplicadas (26 migrations oficiais sincronizadas):**
   - 25 migrations históricas aplicadas via `npx supabase db push --db-url ...`
   - 1 nova migration oficial versionada: `supabase/migrations/20260906125246_eco_2605_widen_route_metadata_columns.sql` (ampliação dos campos contextuais `best_season`, `connectivity`, `road_access` para `TEXT` em `app_private.routes`).
   - `npx supabase migration list` comprova alinhamento 1:1 estrito entre local e remoto (`upToDate: true`).
   - `npx supabase db advisors` $\rightarrow$ Exit 0, zero issues de segurança ou performance.
2. **PostGIS e Schemas Homologados:**
   - PostGIS 3.3.7 ativo em `extensions`.
   - Schemas `app_private` e `extensions` ativos com isolamento RLS e sem exposição direta ao PostgREST.
   - 33 tabelas de domínio criadas e validadas.
3. **Rollback Transacional Comprovado em Banco Real:**
   - Execução com falha induzida (`--fail-after route`) via `seed_route_package` na fixture Altamira/Xingu $\rightarrow$ Exit 1 com erro esperado.
   - Consulta SQL direta independente comprova contagens zero para a rota e região após o rollback (`XINGU_ROUTES_AFTER_ROLLBACK: 0`, `XINGU_REGIONS_AFTER_ROLLBACK: 0`).
   - Execução de `verify_pindobal_transaction.py` $\rightarrow$ `PINDOBAL_TRANSACTION=OK` (zero resíduos parciais).
4. **Aplicação Real do Pacote Pindobal (Run 1):**
   - Comando: `python -m app.ingestion.seed_route_package --package-file ../docs/data/pindobal_route_package.md --apply --env-file .env.test`
   - Exit 0.
   - Ingestion Run ID: `8c653270-9c04-412c-a88d-90822b37ea20`
   - Contagens: `read: 5`, `created: 5`, `updated: 0`, `unchanged: 0`, `rejected: 0`, `candidates: 0` (`reconciled: true`).
   - Territorial: `region_created: 1`, `route_created: 1`, `origins_created: 3`, `geometries_created: 3`, `route_actors_created: 5`.
5. **Idempotência Estrita Comprovada em Banco Real (Run 2):**
   - Reexecução do mesmo comando sobre o banco de teste $\rightarrow$ Exit 0.
   - Ingestion Run ID: `506c1125-b9dd-4a67-9cae-f9ac705025eb`
   - Contagens: `read: 5`, `created: 0`, `updated: 0`, `unchanged: 5`, `rejected: 0`, `candidates: 0` (`reconciled: true`).
   - Territorial: `region_created: 0`, `route_created: 0`, `origins_created: 0`, `origins_unchanged: 3`, `geometries_created: 0`, `geometries_unchanged: 3`, `route_actors_created: 0`, `route_actors_unchanged: 5`.
   - Consulta SQL direta confirma ausência absoluta de duplicações.
6. **Estado de Publicação Preservado:**
   - Rota `rota-pindobal`: `status: draft`, `is_verified: false` (em total conformidade com `fluxo_publicacao_primeira_rota.md` e ADR 0006).
   - Staging e Production permaneceram rigorosamente intocados.

---

## 5. Worktree e Arquivos Alterados (ECO-2605)

| Arquivo | Ação |
|---------|------|
| `backend/app/ingestion/route_package_parser.py` | Adicionados validadores estritados de geometria, CRS, bounds, SHA-256, proveniência Google |
| `backend/app/ingestion/route_package_repository.py` | Removidos fallbacks de coordenadas inventadas; rejeição explícita sem origens |
| `backend/app/ingestion/route_package_importer.py` | Dry-run reporta `is_estimate: True` com nota explicativa |
| `backend/app/ingestion/seed_route_package.py` | CLI com guardrail `APP_ENV=test` |
| `backend/tests/test_route_package_importer.py` | 16 testes completos incluindo negativos |
| `backend/tests/fixtures/route_packages/altamira_xingu_package.md` | Fixture de segunda rota |
| `backend/pyproject.toml` | Adicionado `types-PyYAML` em dev (typing PyYAML) |
| `docs/catalogo_territorial/eco_2605_generalizacao_importacao_rotas.md` | Este relatório |
| `docs/catalogo_territorial/fluxo_publicacao_primeira_rota.md` | Protocolo de publicação |
| `docs/project_status.md` | Status atualizado para PARTIAL |

**Estado do worktree:** Sem artefatos temporários, sem arquivos `.env.*` locais, sem modificações no checkout principal. Todos os arquivos da tarefa permanecem no worktree `.worktrees/eco-2605` aguardando a execução do gate real de persistência antes de qualquer commit.

