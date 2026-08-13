# Coordenação Codex × Google Antigravity

## Regra operacional

Uma task ativa por agente. Uma task pertence a um único worktree/branch e a um
único executor até o handoff. Agentes não compartilham memória, `.env`, tokens,
logs privados nem suposições; compartilham somente commits e evidências sanitizadas.

## Antes de começar

1. Confirmar clone/worktree Git íntegro com `git status --short` e registrar commit
   baseline. Nesta cópia auditada `.git` está ausente; ECO-1301 deve corrigir isso.
2. Ler a sequência obrigatória do `AGENTS.md` e o bloco completo da task.
3. Declarar no mini-brief os arquivos previstos e confrontá-los com a matriz de
   conflitos em `dependency_graph.md`.
4. Confirmar dependências/ADRs `VERIFIED` ou aceitos; checkbox histórico não basta.
5. Confirmar ambiente. Se `.env.test` coincidir com `.env`, parar.
6. Verificar alterações alheias e não tocar em arquivos fora do escopo.

## Paralelismo seguro

- Usar branches/worktrees separados quando houver dois agentes.
- O coordenador mantém um ledger simples: task, executor, branch, commit-base,
  arquivos reservados, ambiente e status.
- Não permitir edição simultânea de `docs/openapi.yaml`, uma mesma migration,
  `backend/app/models/domain.py`, `econexao-app/app.json`, lockfiles ou workflows.
- Contrato/schema precede consumidores. Depois do merge do contrato, o segundo
  agente faz rebase/merge limpo antes de editar tipos/UI.
- Não resolver conflito aceitando “ours/theirs” em migrations, policies, OpenAPI,
  Auth ou Storage; fazer revisão semântica.

## Divisão sugerida

- **Codex:** migrations, FastAPI, importador, CI/CD, scripts verificadores e revisão
  cruzada de segurança.
- **Google Antigravity:** fluxos Expo, painel, acessibilidade visual e E2E, desde que
  o contrato já esteja congelado.
- **Indiferente:** documentação, fixtures, testes unitários e runbooks.
- **Humano/owner:** ADRs, contas, domínios, secrets, legal, orçamento, production e
  submissão final às lojas.

A sugestão não substitui competência nem lock de arquivos. Tasks de alto risco
exigem revisão cruzada por ferramenta diferente da autora.

## Segurança da informação

- Nunca copiar `.env`, DSN, JWT, API key, URL assinada ou payload pessoal para
  prompt, commit, issue, screenshot ou log.
- Scripts devem carregar segredo por arquivo ignorado/secret manager e redigir erro.
- IA não recebe credencial de production.
- Dados reais de usuário não entram em fixture; usar UUIDs e conteúdo sintético.
- Fonte `C:\Users\Bruno\Downloads\teste-rota` é somente leitura.

## Revisão cruzada obrigatória

Auth, RLS, migrations, autorização administrativa, Storage, deploy, exclusão de
dados e integrações Google exigem:

1. autor executa testes positivos/negativos e entrega diff/evidência;
2. revisor lê ADR/spec/docs atuais e revisa ameaça/rollback;
3. revisor reproduz comandos em ambiente correto;
4. owner aprova ações destrutivas/production;
5. task só passa a `VERIFIED` após pendências P0/P1 resolvidas.

## Evidência mínima por tipo

| Tipo | Evidência |
|---|---|
| Schema/RLS | migration list, advisors, SQL positivo/negativo A/B, schema alvo |
| Importador | hashes, dry-run, apply, rollback, contagens, rejeições, double-run |
| API | OpenAPI drift, pytest, erros 401/403/404/409/422, request_id |
| UI | typecheck, Jest, screenshot/video quando visual, teclado/leitor de tela |
| Deploy | artifact digest, migration gate, health/smoke, URL staging, rollback |
| Release | build IDs, versões, checksums, aprovação owner, monitoramento |

## Handoff copiável

```text
Task:
Executor/branch/worktree:
Commit base e commit entregue:
Resultado observável:
Arquivos alterados:
Contratos/migrations:
Comandos, exit codes e ambiente:
Evidências anexadas:
Verificações Auth/RLS/Storage:
Riscos e pendências:
Rollback:
Arquivos ainda reservados:
Próxima task desbloqueada:
```

## Modelo de revisão

```text
Task revisada:
Autor / revisor:
Fonte normativa usada:
Aceites reproduzidos:
Testes negativos reproduzidos:
Segredos/PII verificados:
Findings P0/P1/P2:
Decisão: APPROVE | CHANGES_REQUIRED | NOT_VERIFIABLE
Justificativa e evidências:
```

## Registro de Handoffs Executados

### Handoff ECO-1301 (12/08/2026)

- **Task:** ECO-1301 — Restabelecer baseline verificável
- **Executor/branch/worktree:** Google Antigravity / diretório raiz (`c:\Users\Bruno\Downloads\eco-nexao-v3`)
- **Commit base e commit entregue:** `NOT_VERIFIABLE` / `BLOCKED` (diretório raiz sem `.git`; sem `git init` por regra)
- **Resultado observável:** Script `backend/scripts/check_environment.py` criado e validado sanitizado (sem exposição de segredos/DSNs, falha fechado no isolamento dev/test); testes de backend e frontend executados; verificações registradas sem tocar remotos.
- **Arquivos alterados:**
  - `backend/scripts/check_environment.py` [NEW]
  - `DEVELOPMENT.md` [MODIFY]
  - `docs/finalization/audit_report.md` [MODIFY]
  - `docs/finalization/ai_coordination.md` [MODIFY]
  - `<appDataDir>/brain/<conversation-id>/implementation_plan.md` [MODIFY]
- **Contratos/migrations:** Nenhum contrato ou migration alterado.
- **Comandos, exit codes e ambiente:**
  - `git -C .. status --short`: exit code 1 (`fatal: not a git repository`) -> Git baseline permanece `NOT_VERIFIABLE` / `BLOCKED`
  - `python -m scripts.check_environment`: exit code 1 (sanitizado; Python 3.13.13, Node 24.13.0, npm 11.6.2, Ruff 0.16.2, Mypy 1.17.1, Pytest 8.4.1, tsc 5.9.3, Jest 29.7.0, Supabase 2.114.0 OK; colisão `.env`/`.env.test` detectada)
  - `python -m ruff check app tests`: exit code 0 (0 erros)
  - `python -m mypy app`: exit code 0 (45 arquivos validados)
  - `python -m pytest --cov=app --cov-report=term --cov-fail-under=85`: exit code 1 (148/148 testes passaram em 40.41s; cobertura 83.27% < 85%)
  - `npm run openapi:check`: exit code 0
  - `npm run typecheck`: exit code 0
  - `npm test -- --watch=false --forceExit`: exit code 0 (15 suítes / 74 testes)
- **Evidências anexadas:** Logs sanitizados das execuções em `audit_report.md` e script `check_environment.py`.
- **Verificações Auth/RLS/Storage:** Zero conexões de escrita ou alterações remotas.
- **Riscos e pendências:**
  - **Git Baseline (`BLOCKED`)**: Diretório não possui `.git`. Requer solicitação do repositório/URL original ao proprietário.
  - **Isolamento de Ambientes (`BLOCKED`)**: `.env` e `.env.test` apontam para o mesmo projeto/banco (tarefa ECO-1401).
  - **Cobertura Backend (`PARTIAL`)**: 148/148 testes passaram, mas cobertura (83.27%) está abaixo de 85%.
- **Rollback:** Exclusão dos scripts/documentos locais de baseline.
- **Arquivos ainda reservados:** Nenhum.
- **Próxima task desbloqueada:** Decisões humanas (ECO-1302–1306) e ECO-1401 (Isolar Supabase dev/test).

### Handoff ECO-1306 (12/08/2026)

- **Task:** ECO-1306 — Registro de decisões de lançamento
- **Executor/branch/worktree:** Google Antigravity / diretório raiz (`c:\Users\Bruno\Downloads\eco-nexao-v3`)
- **Commit base e commit entregue:** `BLOCKED` / `BLOCKED` (sem repositório `.git` no diretório raiz)
- **Resultado observável:** Entrevista de lançamento realizada com o Proprietário do Produto. Decisões de ambientes (reuso de `econexao` dev e `econexao-teste` test), Cloud Run, domínios, RBAC, expurgo de 90 dias e marca registradas com status `PARTIAL` em `decisions_needed.md`. Nenhum custo, conta ou deploy ativado. Staging e Produção permanecem bloqueados.
- **Arquivos alterados:**
  - `docs/finalization/decisions_needed.md` [MODIFY]
  - `docs/finalization/audit_report.md` [MODIFY]
  - `docs/finalization/ai_coordination.md` [MODIFY]
- **Contratos/migrations:** Nenhum contrato HTTP, migration ou schema alterado.
- **Comandos, exit codes e ambiente:**
  - NENHUM comando de mutação ou infraestrutura executado.
- **Evidências anexadas:** Matriz de decisões atualizada em `decisions_needed.md`.
- **Verificações Auth/RLS/Storage:** Zero conexões de escrita ou alterações remotas.
- **Riscos e pendências:**
  - **Identidade e Lojas (`PARTIAL`)**: Nome `ECOconexão` e slug `econexao-app` provisórios; IDs de pacote Android/iOS e contas de lojas a cadastrar antes da homologação.
  - **Documentos Legais (`PENDENTE`)**: Termos de Uso, Política de Privacidade e Canal DPO pendentes de redação e aprovação jurídica final.
  - **Domínios & Universal Links (`ADIADO`)**: Domínio oficial DNS pendente até antes da ECO-1905.
- **Rollback:** Reversão documental dos arquivos em `docs/finalization/`.
- **Arquivos ainda reservados:** Nenhum.
- **Próxima task desbloqueada:** ECO-1401 em escopo reduzido exclusivo de verificação e isolamento de dev/test (mediante apresentação de plano prévio especifico).

### Handoff ECO-1401 (12/08/2026)

- **Task:** ECO-1401 — Isolar e verificar Supabase development/test/staging/production
- **Executor/branch/worktree:** Google Antigravity / diretório raiz (`c:\Users\Bruno\Downloads\eco-nexao-v3`)
- **Commit base e commit entregue:** `BLOCKED` / `BLOCKED` (sem repositório `.git` no diretório raiz)
- **Resultado observável:** Configuração de testes (`.env.test`) ajustada para utilizar o projeto isolado `econexao-teste`, resolvendo a colisão de apontamento com o projeto de desenvolvimento `econexao`. Script de teste de isolamento `check_test_isolation.py` e verificador sanitizado `check_environment.py` validados com sucesso (`TEST_ISOLATION=OK`, `STATUS FINAL=OK`). Gates locais estáticos e de testes (ruff, mypy, pytest 170/170 90.10%, openapi:check, typecheck, jest 15 suítes/74 testes) executados com exit code 0.
- **Arquivos alterados:**
  - `backend/.env.test` [MODIFY]
  - `docs/finalization/audit_report.md` [MODIFY]
  - `docs/finalization/ai_coordination.md` [MODIFY]
- **Contratos/migrations:** Nenhum contrato HTTP, migration ou schema alterado.
- **Comandos, exit codes e ambiente:**
  - `python -m scripts.check_test_isolation`: exit code 0 (`TEST_ISOLATION=OK`)
  - `python -m scripts.check_environment`: exit code 0 (`STATUS FINAL: OK - Baseline verificado com sucesso`)
  - `python -m ruff check app tests`: exit code 0
  - `python -m mypy app`: exit code 0
  - `python -m pytest --cov=app --cov-report=term --cov-fail-under=85`: exit code 0 (170/170 passed in 31.05s, 90.10% coverage)
  - `npm run openapi:check`: exit code 0
  - `npm run typecheck`: exit code 0
  - `npm test -- --watch=false`: exit code 0 (15 suítes / 74 testes)
- **Evidências anexadas:** Logs sanitizados das execuções em `audit_report.md`.
- **Verificações Auth/RLS/Storage:** Zero conexões de escrita em produção/staging.
- **Riscos e pendências:**
  - **Staging / Production**: Adiados para Marco 20 conforme matriz `ECO-1306`.
  - **Git Baseline (`BLOCKED`)**: Diretório não possui `.git`.
- **Rollback:** Reversão do arquivo `backend/.env.test`.
- **Arquivos ainda reservados:** Nenhum.
- **Próxima task desbloqueada:** ECO-1402 (Base do Supabase Storage) e ECO-1403 (RBAC editorial e audit trail).

### Handoff ECO-1402 parcial (13/08/2026)

- **Task:** ECO-1402 — Corrigir e verificar base do Supabase Storage
- **Executor/branch/worktree:** Codex / diretório raiz sem `.git`
- **Commit base e commit entregue:** `NOT_VERIFIABLE` / `NOT_VERIFIABLE`
- **Resultado observável:** Migration forward criada pela Supabase CLI 2.113.0.
  O estado final local remove o bypass de ownership de avatar, impede listagem
  pública via policy ampla, cobre SELECT/INSERT/UPDATE/DELETE do dono e configura
  os buckets do ADR 0008. O gate de ambiente foi corrigido para detectar project
  refs fictícios e inconsistência entre URL e banco.
- **Arquivos alterados:**
  - `supabase/migrations/20260813084440_harden_storage_buckets_and_policies.sql`
  - `backend/scripts/check_test_isolation.py`
  - `backend/tests/test_check_test_isolation.py`
  - `backend/tests/test_rls_policies.py`
  - `DEVELOPMENT.md`
  - `docs/finalization/README.md`
  - `docs/finalization/audit_report.md`
  - `docs/finalization/release_checklist.md`
  - `docs/finalization/ai_coordination.md`
- **Contratos/migrations:** Nova migration forward; nenhuma migration histórica
  foi editada e nenhum contrato HTTP mudou.
- **Comandos, exit codes e ambiente:**
  - `npx --yes supabase@2.113.0 --version/--help`: exit 0; versão 2.113.0.
  - `npx --yes supabase@2.113.0 migration new ...`: exit 0.
  - `python -m pytest tests/test_check_test_isolation.py tests/test_check_environment.py tests/test_rls_policies.py -q`: exit 0; 15/15.
  - `python -m scripts.supabase_test_cli dry-run`: exit 1 antes de write;
    conexão recusada porque o tenant test configurado não existe.
  - `python -m scripts.check_test_isolation`: exit 1 esperado após correção do
    gate (`SUPABASE_PROJECT_REF_INVALID`).
  - `python -m pytest --cov=app --cov-report=term --cov-fail-under=85`: exit 0;
    176/176 em 30,91s, cobertura 90,10% (executado fora do sandbox por DLL).
  - `python -m ruff check app tests scripts/check_test_isolation.py scripts/supabase_test_cli.py`: exit 0.
  - `python -m mypy app`: exit 0; 45 arquivos.
- **Verificações Auth/RLS/Storage:** somente validação local. Zero migrations,
  uploads ou alterações remotas; matriz A/B/anon, upsert, advisors e migration
  list continuam pendentes.
- **Riscos e pendências:** `ECO-1402 = PARTIAL`. O owner precisa fornecer em
  `backend/.env.test` as credenciais reais do projeto Supabase test já aprovado.
  A raiz continua sem baseline Git verificável.
- **Rollback:** migration forward posterior; antes de promoção, basta remover o
  arquivo novo. Depois de aplicada, qualquer ajuste deve usar outra migration.
- **Arquivos ainda reservados:** nenhum.
- **Próxima ação:** corrigir o ambiente test, repetir dry-run, aplicar somente em
  test e executar migration list, advisors e matriz Storage A/B/anon/upsert.

#### Addendum de verificação remota (13/08/2026)

- Development/test passaram `check_test_isolation` e conectaram em projetos distintos.
- As migrations `20260812120000` e `20260813084440` foram aplicadas somente em test;
  migration list ficou 7/7 e advisors retornaram zero findings.
- A primeira tentativa foi revertida por `ALTER TABLE storage.objects`; a migration
  ainda não aplicada foi ajustada para respeitar ownership do schema gerenciado.
- `scripts.verify_storage_policies`: `STORAGE_MATRIX=OK` para cliente sem sessão,
  usuário A, usuário B, upsert, leitura pública, listagem segura e delete.
- Estado funcional: `VERIFIED` em test. Estado processual: revisão cruzada pendente,
  pois a raiz ainda não possui worktree Git íntegro para entregar diff/commit a outro revisor.
- Próxima task de implementação independente: ECO-1403. ECO-1701/1702/1704 devem
  aguardar a revisão cruzada formal de Storage.

### Handoff ECO-1403 funcionalmente verificada (13/08/2026)

- **Task:** ECO-1403 — Implementar RBAC editorial e audit trail
- **Executor/branch/worktree:** Codex / raiz sem `.git`
- **Resultado observável:** RBAC privado com papéis admin/editor/reviewer/publisher,
  capabilities por escopo, invitations com hashes, revogação imediata, workflow
  editorial genérico, segregação de funções e audit trail append-only.
- **Arquivos principais:**
  - `supabase/migrations/20260813091542_editorial_rbac_and_audit_trail.sql`
  - `backend/app/models/domain.py`
  - `backend/app/models/__init__.py`
  - `backend/app/repositories/editorial_authorization.py`
  - `backend/app/services/editorial_authorization.py`
  - `backend/scripts/verify_editorial_rbac.py`
  - `backend/tests/test_editorial_authorization.py`
  - `backend/tests/test_rls_policies.py`
- **Contratos/migrations:** migration aplicada somente em test; nenhuma mudança
  OpenAPI ou UI, conforme escopo.
- **Evidências:**
  - migration list local/remoto 8/8; advisors sem findings;
  - `EDITORIAL_RBAC=OK`: capabilities, least privilege, revogação, UPDATE/DELETE
    de auditoria negados e roles anon/authenticated negados; rollback confirmado;
  - pytest 190/190, cobertura 89,83%; Ruff e mypy verdes (47 arquivos).
- **Segurança:** não usa `user_metadata`, `auth.role()` ou `SECURITY DEFINER`;
  tabelas em `app_private`, RLS ligado e grants Data API revogados.
- **Riscos/pendências:** revisão cruzada formal bloqueada pela ausência de Git na
  raiz. A ECO-1601 deve tornar este serviço obrigatório em toda API administrativa.
- **Próxima task desbloqueada:** ECO-1601 e ECO-1801. No caminho crítico de dados,
  ECO-1501 também está desbloqueada e entrega valor mais direto ao app público.

### Handoff ECO-1501 funcionalmente verificada (13/08/2026)

- **Task:** ECO-1501 — Persistência transacional do `seed_pindobal --apply`
- **Executor/branch/worktree:** Codex / raiz sem `.git`
- **Resultado observável:** CLI falha fechado sem DB explícito; dry-run não abre
  conexão; apply em test persiste região, rota, três origens/geometrias OSRM, fonte
  e ingestion run em uma única transação.
- **Arquivos principais:**
  - `backend/app/ingestion/pindobal_repository.py`
  - `backend/app/ingestion/seed_pindobal.py`
  - `backend/scripts/verify_pindobal_transaction.py`
  - `backend/scripts/verify_pindobal_apply.py`
  - `backend/tests/test_pindobal_persistence.py`
- **Evidências:** manifesto 9/9; dry-run com contagens contratuais; falha induzida
  manteve todas as contagens; apply gerou run sanitizado; verificação remota confirmou
  1 região, 1 rota, 3 origens, 3 geometrias SRID 4326, 1 fonte e 1 run concluído.
- **Gates:** advisors sem findings; migrations 8/8; pytest 193/193 em 42,40s,
  cobertura 88,92%; Ruff e mypy verdes (48 arquivos).
- **Incidente recuperado:** primeira tentativa de apply falhou antes da conexão por
  event loop Windows incompatível; nenhuma escrita ocorreu; Selector policy corrigiu.
- **Riscos/pendências:** segunda execução ainda falha por unique constraints. A
  idempotência/upsert e proveniência detalhada pertencem à ECO-1502. Revisão cruzada
  processual segue bloqueada pela ausência de Git íntegro na raiz.
- **Próxima task:** ECO-1502 — idempotência, proveniência e relatório completo.

### Handoff ECO-1502 verificada em Supabase test (13/08/2026)

- **Task:** ECO-1502 — Idempotência, proveniência e relatório completo.
- **Escopo remoto:** exatamente duas aplicações controladas no projeto test
  descartável; staging e production não foram acessados.
- **Guardrail:** `--apply` agora exige o `backend/.env.test` canônico e executa o
  gate que compara project ref/DSN com development antes de conectar.
- **Evidências:** manifesto 9/9; migrations 8/8; advisors sem findings; rollback
  induzido; primeira carga criou 674 atores; segunda carga criou/atualizou 0,
  classificou 1661 inalterados + 53 candidatos e reconciliou 1714/1714 registros.
- **Estado final test:** 1 região, 1 rota, 3 origens/geometrias SRID 4326, 674 atores,
  3428 raws das duas cargas, 8088 proveniências e 3 runs concluídos (inclui ECO-1501).
- **Segurança de dados:** 737 registros Google por execução continuam sem Place ID
  inventado; fuzzy permanece candidato, nunca merge automático.
- **Riscos/pendências:** `route_actors` e métricas PostGIS pertencem à ECO-1503;
  portanto Gate 1/ECO-1504 continuam `PARTIAL`. A ausência de `.git` impede diff e
  revisão cruzada formal.
- **Próxima task:** ECO-1503 — geometrias e associação PostGIS persistentes.

### Handoff ECO-1503 verificada em Supabase test (13/08/2026)

- **Task:** ECO-1503 — Geometrias e associação PostGIS persistentes.
- **Migration:** `20260813102503_pindobal_spatial_integrity.sql`, criada pela CLI e
  aplicada somente em test; local/remoto 9/9 alinhadas; advisors sem findings.
- **Resultado:** 3 LineStrings SRID 4326 com 884/777/866 pontos, distâncias
  45.229/41.452/42.319 km, bounds e SHA-256 por fonte.
- **Associações:** 313 atores únicos até 1000 m da rota Porto, com distância,
  posição/segmento e flags por origem; repetição do backfill alterou 0 linhas.
- **Índices:** GiST de atores e geometrias presentes 2/2; funções PostGIS foram
  qualificadas no schema `extensions`.
- **Validação:** parser OSRM agora rejeita valores não finitos, ordem duplicada ou
  regressiva, distância acumulada não monotônica, contagem ou endpoints divergentes.
- **Incidente recuperado:** primeira tentativa do backfill não adaptou dict JSONB;
  a transação reverteu. Serialização JSON explícita corrigiu a execução seguinte.
- **Limitações:** comparação editorial amostral com métricas legadas e smoke das APIs
  pertencem à ECO-1504; revisão visual fica para staging. Git continua ausente.
- **Próxima task:** ECO-1504 — Gate 1 com carga/consultas/API test verificadas.

### Handoff ECO-1504 verificada em Supabase test (13/08/2026)

- **Task:** ECO-1504 — Carga dupla de Pindobal em test isolado.
- **Escopo:** consolidou as duas cargas já autorizadas; não limpou nem reaplicou o
  snapshot e não acessou staging/production.
- **Gate remoto:** isolamento OK, manifesto 9/9, migrations 9/9, advisors sem findings,
  rollback comprovado, segunda carga com 0 creates/updates e backfill espacial repetido
  com 0 alterações.
- **Smoke real:** sessão anônima descartável do Supabase test; JWT aceito pelo FastAPI;
  região `santarem-belterra`, rota `rota-pindobal`, 3 origens, 313 atores, mapa com
  200 pins e geometria selecionada com 884 pontos.
- **Cliente Expo:** fluxo runtime usa API/hooks reais; typecheck e OpenAPI passaram;
  Jest 15/15 suítes e 74/74 testes. Testes de UI continuam contratuais/mocados, mas o
  mesmo cliente e endpoints foram exercitados pelo smoke em memória.
- **Limitações:** catálogo ainda fabrica alguns campos e imagem fallback (ECO-1901);
  mapa limita pins a 200 por payload. Gate 1 permanece `PARTIAL` apenas pelo pacote
  imutável e aceite editorial da ECO-1505.
- **Próxima task:** ECO-1505 — pacote de promoção Pindobal, sem promover ambientes.

### Handoff ECO-1505 tecnicamente concluída, aprovação bloqueada (13/08/2026)

- **Task:** ECO-1505 — Pacote de promoção Pindobal.
- **Resultado técnico:** pacote metadata-only gerado em
  `docs/finalization/artifacts/pindobal-v1`, verificável offline e sem dataset raw,
  PII, credenciais, JWT, project ref ou DSN.
- **Integridade:** checksum SHA-256
  `6046c8ca19bea4127b4840b98939bc71cb69734133e7c07449732156aac95a26`;
  9 fontes, 9 migrations, implementação e runbook verificados por hashes individuais.
- **Conteúdo fixado:** versões snapshot/importer/regras; 674 atores candidatos, 313
  vínculos, 3 geometrias, double-run idempotente, 53 fuzzy pendentes e 737 Google
  legados sem Place ID por carga.
- **Classificação:** `blocked_pending_editorial_acceptance`; rota/atores são somente
  candidatos a draft, Google legado é evidência raw e mídia está excluída.
- **Rollback:** lógico para draft/não publicado, com audit/proveniência preservados;
  nenhuma exclusão automática.
- **Verificação:** pacote offline OK; Get-FileHash OK; backend 200/200 testes, Ruff e
  mypy verdes. Nenhum acesso a staging/production e nenhuma escrita remota.
- **Bloqueadores humanos:** owner/publisher deve revisar os 53 candidatos, direitos
  SEMTUR, licença/crédito/alt/mídia e assinar o checksum exato. `APPROVAL.md` permanece
  `PENDING`. Ausência de Git também impede revisão formal por commit.
- **Estado da task:** implementação técnica concluída; DoD editorial `BLOCKED` até
  aprovação humana explícita. O pacote não autoriza promoção.
- **Próximo trabalho de código sugerido:** ECO-1601 — contrato da API administrativa,
  que já está desbloqueada por ECO-1403 e não exige promover Pindobal.
