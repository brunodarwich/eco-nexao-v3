# Registro histórico de tasks de finalização

Status: `SUPERSEDED` como backlog ativo. A fonte ativa local de estado e trabalho
aberto é [`../project_status.md`](../project_status.md). Este arquivo preserva os
aceites, dependências e evidências históricas para reconciliação.

Convenções: `P0/P1/P2`; tamanho `S/M/L`; estados conforme `README.md`. Todas as
tasks exigem `git status`, mini-brief, preservação de alterações alheias, nenhum
segredo em output e handoff de `ai_coordination.md`. Comandos Supabase devem ser
descobertos com `supabase --help`; production nunca é usada sem aprovação.

## Marco 13 — Baseline e decisões

### ECO-1301 — Restabelecer baseline verificável

- **Resultado de negócio / prioridade / tamanho / executor:** fonte de verdade
  confiável para toda execução; P0; M; Codex.
- **Dependências / ADRs:** nenhuma; não decide arquitetura.
- **Contexto e leitura:** `AGENTS.md`, `finalization/*`, backlog/progresso arquivados,
  playbook. Inspecionar raiz, `.git`, `.env*` sem imprimir valores e workflows.
- **Arquivos esperados:** metadados Git fora do commit; scripts/docs de baseline,
  `DEVELOPMENT.md`, `audit_report.md`. Preservar todo código do usuário.
- **Permitido / proibido:** restaurar ou obter clone íntegro e corrigir comandos de
  verificação; não alterar features, dependencies, remotos ou secrets.
- **Passos:** registrar commit-base; provar worktree; separar definição nominal de
  ambientes; reproduzir pytest em runtime limpo; rerodar Ruff/mypy/OpenAPI/TS/Jest;
  registrar divergências sem editar história.
- **Aceite / testes / comandos:** `git status --short`; `git rev-parse --show-toplevel`;
  `cd backend; python -m pytest --cov=app --cov-report=term --cov-fail-under=85; python -m ruff check app tests; python -m mypy app`; `cd ../econexao-app; npm run openapi:check; npm run typecheck; npm test -- --watch=false --forceExit`. Todos com exit code e versões.
- **Evidência / riscos / rollback / DoD:** commit-base, outputs sanitizados e causa da
  DLL resolvida; risco de trabalhar sobre cópia sem Git ou ambiente colidente;
  rollback documental/ambiente local; DoD só com testes reproduzíveis e audit update.
- **Prompt de execução:**
  ```text
  Execute somente ECO-1301. Leia AGENTS.md, docs/finalization/README.md, esta task e
  o playbook. Restaure um worktree Git íntegro, prove o baseline e reproduza todos
  os gates locais sem tocar remotos. Preserve alterações alheias. Pare se precisar
  sobrescrever trabalho. Não conclua sem comandos, exit codes e handoff completo.
  ```
- **Entrega final:** usar o modelo de handoff; próxima task: ECO-1302–ECO-1306 e ECO-1401.

### ECO-1302 — ADR do provedor e topologia FastAPI

- **Resultado / prioridade / tamanho / executor:** provedor executável escolhido;
  P0; S; humano/owner com apoio Codex.
- **Dependências / ADRs:** ECO-1301; cria novo ADR e complementa ADR 0004.
- **Contexto/leitura:** ADRs, spec §§4/14, `decisions_needed.md`, requisitos de
  staging/production. Inspecionar config backend; nenhum código de deploy.
- **Arquivos:** novo `docs/adr/0005-*.md`, índice e decisão; não alterar ADR 0004
  retroativamente.
- **Permitido/proibido:** pesquisa/comparação e registro; não contratar, deployar,
  criar projeto pago ou inserir segredo sem autorização separada.
- **Passos:** comparar ao menos três opções em região, custo, egress Supabase,
  container, health, jobs, secrets, logs, domínio, rollback e SLA; owner decide.
- **Aceite/testes/comandos:** ADR `Status: aceito`, provedor/região/plano, startup e
  rollback definidos; `rg -n "Status: aceito|Provedor|Rollback" docs/adr/0005-*.md`.
- **Evidência/riscos/rollback/DoD:** matriz e aceite do owner; risco de custo/lock-in;
  rollback é ADR supersessor; DoD quando não restar “contêiner gerenciado” genérico.
- **Prompt de execução:**
  ```text
  Execute ECO-1302 como decisão assistida. Não escolha pelo proprietário. Produza
  comparação verificável e registre somente a opção explicitamente aprovada. Não
  crie infraestrutura. Entregue ADR, fontes, consequências e handoff.
  ```
- **Entrega:** handoff; desbloqueia ECO-2001.

### ECO-1303 — ADR de operação editorial, RBAC e publicação

- **Resultado / prioridade / tamanho / executor:** processo seguro de conteúdo; P0;
  M; humano/owner.
- **Dependências/ADRs:** ECO-1301; novo ADR obrigatório.
- **Contexto/leitura:** spec §§6/12/15, audit B, `decisions_needed.md`; inspecionar
  migrations/models/API, sem alterá-los.
- **Arquivos:** `docs/adr/0006-*.md`, matriz de capabilities e state machine.
- **Permitido/proibido:** documentar admin/editor/reviewer/publisher, MFA, convite,
  remoção e break-glass; não implementar roles/policies/painel.
- **Passos:** decidir segregação, transições draft→review→published→archived,
  publish guard, auditoria, reconciliação e ferramenta/painel.
- **Aceite/testes/comandos:** tabela papel×ação×recurso e transições válidas/inválidas;
  `rg -n "admin|editor|reviewer|publisher|draft|published|archived" docs/adr/0006-*.md`.
- **Evidência/riscos/rollback/DoD:** aprovação owner; risco de privilégio excessivo;
  superseder por ADR; DoD com critérios objetivos e política de emergência.
- **Prompt de execução:**
  ```text
  Execute apenas ECO-1303. Facilite a decisão humana e registre papéis, capabilities,
  transições, auditoria e publish guard. Não escreva migration/API/UI. Pare sem
  aprovação explícita. Entregue ADR aceito e handoff.
  ```
- **Entrega:** desbloqueia ECO-1403/ECO-1601/ECO-1801.

### ECO-1304 — ADR de identidade, linking e sessão Web

- **Resultado / prioridade / tamanho / executor:** continuidade segura guest→conta;
  P0; M; humano/owner.
- **Dependências/ADRs:** ECO-1301; complementa ADR 0004.
- **Contexto/leitura:** spec §§7.1/12, Auth atual, docs Supabase Anonymous Sign-Ins,
  audit A/G; inspecionar `src/auth/*`.
- **Arquivos:** `docs/adr/0007-*.md`; sem código Auth.
- **Permitido/proibido:** decidir email/magic link/OAuth, conflito, recuperação,
  logout, web persistence e exclusão; não ativar provider nem usar credenciais.
- **Passos:** modelar fluxos e ameaça; decidir BFF/cookie vs política web alternativa;
  incluir CAPTCHA, cleanup e efeito de tokens já emitidos.
- **Aceite/testes/comandos:** diagramas/cenários guest perdido, email existente,
  refresh/logout/delete; `rg -n "conflito|recuperação|Web|CAPTCHA|exclusão" docs/adr/0007-*.md`.
- **Evidência/riscos/rollback/DoD:** aceite owner; risco de perda/takeover; ADR
  supersessor; DoD com comportamento por plataforma e base LGPD.
- **Prompt de execução:**
  ```text
  Execute ECO-1304 como ADR. Consulte docs atuais do Supabase, não implemente Auth e
  não exponha segredo. Exija decisão humana para provider e persistência Web.
  Registre cenários de falha, segurança, rollback e handoff.
  ```
- **Entrega:** desbloqueia ECO-1902.

### ECO-1305 — ADR de mídia, licença e privacidade

- **Resultado / prioridade / tamanho / executor:** política de mídia publicável; P0;
  M; humano/owner.
- **Dependências/ADRs:** ECO-1301; novo ADR.
- **Contexto/leitura:** spec §8.5/12, audit D, docs Storage atuais e contrato Pindobal.
- **Arquivos:** `docs/adr/0008-*.md`, matriz mídia×visibilidade×retenção.
- **Permitido/proibido:** decidir bucket público/privado, derivados, EXIF, alt,
  crédito, licença, substituição, órfãos e Google; não aplicar migration/upload.
- **Passos:** classificar avatar/editorial/Google; definir limites, formatos,
  responsáveis, cache/versionamento e exclusão.
- **Aceite/testes/comandos:** cada classe tem owner, base/licença, visibilidade, TTL,
  delete e fallback; `rg -n "avatar|editorial|Google|EXIF|alt|licença|órf" docs/adr/0008-*.md`.
- **Evidência/riscos/rollback/DoD:** aceite jurídico/editorial; risco LGPD/copyright;
  superseder via ADR; DoD sem default silencioso.
- **Prompt de execução:**
  ```text
  Execute apenas ECO-1305. Produza decisão humana de mídia baseada em docs atuais do
  Supabase e políticas/licenças aplicáveis. Não altere Storage. Pare se licença ou
  visibilidade não forem aprovadas. Entregue ADR e handoff.
  ```
- **Entrega:** desbloqueia ECO-1402/ECO-1701–1704.

### ECO-1306 — Registro de decisões de lançamento

- **Resultado / prioridade / tamanho / executor:** donos, contas e aprovações
  explícitas; P0; M; humano/owner.
- **Dependências/ADRs:** ECO-1301; referencia ADRs 0005–0008.
- **Contexto/leitura:** `decisions_needed.md`, audit G–I e release checklist.
- **Arquivos:** registro não secreto em `docs/finalization/decisions_needed.md` ou
  artefato aprovado; não guardar IDs sensíveis desnecessários.
- **Permitido/proibido:** confirmar domínios, lojas, marca, legal, admins, staging,
  Google budget e production; não criar contas/infra nem compartilhar secrets.
- **Passos:** atribuir owner/data/status/evidência para cada item; registrar limites
  de custo e processo de aprovação.
- **Aceite/testes/comandos:** nenhum item P0 sem owner/status; `rg -n "BLOCKED|owner|aprov" docs/finalization/decisions_needed.md` e revisão humana.
- **Evidência/riscos/rollback/DoD:** aceite assinado; risco de falsa autorização;
  revogação registrada; DoD com production ainda bloqueada até ECO-2201.
- **Prompt de execução:**
  ```text
  Execute ECO-1306 com o proprietário. Registre apenas decisões e referências não
  secretas. Não crie contas, projetos, chaves, domínio ou deploy. Trate silêncio como
  não aprovação. Entregue matriz atualizada e handoff.
  ```
- **Entrega:** desbloqueia provisionamento e release config.

## Marco 14 — Ambientes e segurança editorial

### ECO-1401 — Isolar e verificar Supabase development/test/staging/production

- **Resultado / prioridade / tamanho / executor:** quatro ambientes sem contaminação;
  P0; L; Codex.
- **Dependências/ADRs:** ECO-1301, ECO-1306; ADR 0002.
- **Contexto/leitura:** regras Supabase, `DEVELOPMENT.md`, scripts `backend/scripts/*`,
  docs/changelog atuais. Inspecionar `.env*` sem imprimir.
- **Arquivos:** scripts de fingerprint/isolamento, exemplos, DEVELOPMENT, relatório;
  secrets ficam fora do Git.
- **Permitido/proibido:** owner cria projetos; agente usa dev/test e leitura staging
  aprovada; não acessar production/aplicar migrations nesta task.
- **Passos:** registrar refs não secretas; corrigir colisão dev/test; validar PG17,
  PostGIS e empty/known state; fazer scripts falharem fechado.
- **Aceite/testes/comandos:** `python -m scripts.check_test_isolation`; smoke read-only
  por ambiente autorizado; `npx --yes supabase@<pin> --help`; fingerprints distintos.
- **Evidência/riscos/rollback/DoD:** refs/region/plan sem secrets, outputs redigidos;
  risco de apontar test a production; rollback de arquivos locais; DoD com matriz
  4-way e production inacessível à IA.
- **Prompt de execução:**
  ```text
  Execute ECO-1401. Leia as regras Supabase e descubra a CLI por --help. Nunca exiba
  env/DSN e não aplique migration. Corrija a colisão dev/test, verifique fingerprints
  e pare antes de production. Exija evidência e revisão cruzada.
  ```
- **Entrega:** desbloqueia ECO-1402–1504.

### ECO-1402 — Corrigir e verificar base do Supabase Storage

- **Resultado / prioridade / tamanho / executor:** buckets/policies seguros; P0; L;
  Codex.
- **Dependências/ADRs:** ECO-1305, ECO-1401; ADR 0008.
- **Contexto/leitura:** migration Storage atual, testes, docs oficiais de RLS/upsert.
- **Arquivos:** nova migration criada pela CLI, testes Storage e relatório; nunca
  editar migration já aplicada onde houver histórico.
- **Permitido/proibido:** corrigir INSERT ownership, visibilidade/limites aprovados;
  não aplicar staging/production nem criar objeto custom em schemas gerenciados.
- **Passos:** usar `supabase migration new`; remover bypass `OR`; modelar policies
  SELECT/INSERT/UPDATE/DELETE; verificar grants e anonymous user.
- **Aceite/testes/comandos:** `supabase --help`, `supabase migration --help`, comando
  oficial de criação; aplicar somente test isolado; matriz usuário A/B/anon; advisors
  e migration list; upsert exige INSERT+SELECT+UPDATE.
- **Evidência/riscos/rollback/DoD:** SQL/resultados; risco BOLA/public listing;
  rollback por migration forward segura; DoD após revisão cruzada e remoto test.
- **Prompt de execução:**
  ```text
  Execute ECO-1402 somente em test isolado. Consulte changelog/docs Supabase atuais,
  crie migration pela CLI e prove matriz Storage A/B/anon incluindo upsert. Não use
  auth.role(), SECURITY DEFINER ou Dashboard. Não conclua sem advisors e revisão.
  ```
- **Entrega:** desbloqueia ECO-1701/1702/1704.

### ECO-1403 — Implementar RBAC editorial e audit trail

- **Resultado / prioridade / tamanho / executor:** autorização administrativa
  auditável; P0; L; Codex.
- **Dependências/ADRs:** ECO-1303, ECO-1401; ADR 0006.
- **Contexto/leitura:** spec, OpenAPI, models/migrations/Auth e regras Supabase.
- **Arquivos:** migration CLI, models/repositories/security/tests/OpenAPI se mínimo
  necessário; não tocar UI.
- **Permitido/proibido:** tabelas em `app_private`, app_metadata apenas se ADR exigir;
  não usar user_metadata/auth.role/SECURITY DEFINER para contornar policy.
- **Passos:** memberships/capabilities, estados editoriais, audit append-only,
  convite/revogação e checks FastAPI; preservar schema gerenciado.
- **Aceite/testes/comandos:** pytest de admin/editor/reviewer/publisher/anonymous,
  revogação e objeto; Ruff/mypy/OpenAPI; migration list/advisors em test.
- **Evidência/riscos/rollback/DoD:** matriz e logs sem PII; risco elevação/JWT stale;
  rollback forward/revogação; DoD com revisão cruzada.
- **Prompt de execução:**
  ```text
  Execute ECO-1403 conforme ADR 0006. Implemente o menor RBAC/audit trail completo
  em schema privado, com deny-by-default e testes de identidade cruzada. Pare se o
  ADR não estiver aceito. Não implemente CRUD/painel. Registre toda evidência.
  ```
- **Entrega:** desbloqueia ECO-1601/ECO-1801.

### ECO-1404 — Secrets, backups e recuperação por ambiente

- **Resultado / prioridade / tamanho / executor:** operação recuperável; P0; M;
  humano/owner + Codex.
- **Dependências/ADRs:** ECO-1401, ECO-1302, ECO-1306.
- **Contexto/leitura:** docs atuais Supabase backups/PITR, audit F/H/I e provedor.
- **Arquivos:** runbooks, exemplos de secret manager, CI scan config; sem secrets.
- **Permitido/proibido:** definir RPO/RTO, DB+Storage backup, restore drill, rotação,
  break-glass; não restaurar/apagar remoto nesta task.
- **Passos:** escolher plano/PITR; lembrar que backup DB não restaura objetos Storage;
  adicionar scanners reais e inventário de owners.
- **Aceite/testes/comandos:** scanner executável (`gitleaks`/equivalente aprovado),
  dependency audits; checklist de restore tabletop; comandos descobertos/documentados,
  não executados contra production.
- **Evidência/riscos/rollback/DoD:** política aprovada/custos; risco perda de Storage;
  rollback de config; DoD com restore drill agendado e segredo fora de logs.
- **Prompt de execução:**
  ```text
  Execute ECO-1404 sem acessar production e sem restaurar dados. Consulte docs atuais,
  documente RPO/RTO, banco+Storage, rotação e scanners reais. Exija decisão de custo
  do owner. Não registre secrets. Entregue runbooks e handoff revisado.
  ```
- **Entrega:** alimenta Gates 6–7.

## Marco 15 — Importador persistente e conteúdo Pindobal

### ECO-1501 — Persistência transacional do `seed_pindobal --apply`

- **Resultado / prioridade / tamanho / executor:** comando que realmente grava ou
  falha fechado; P0; L; Codex.
- **Dependências/ADRs:** ECO-1401, ECO-1403; contrato Pindobal.
- **Contexto/leitura:** `seed_pindobal.py`, importers, models/repos, migrations,
  testing strategy. Inspecionar fonte externa sem alterá-la.
- **Arquivos:** ingestion service/UoW/repositories/CLI/testes; não alterar UI/Google.
- **Permitido/proibido:** persistir em test com transações; não staging/production,
  não ler CSV em request, não inventar Place ID.
- **Passos:** `--apply` exige DB explícito; registrar run; persistir região/rota/
  origens/geometrias/fontes; rollback total em falha; status/exit code honestos.
- **Aceite/testes/comandos:** dry-run zero writes; apply controlado; falha induzida
  deixa zero publicação parcial; `python -m app.ingestion.seed_pindobal --help` e
  comandos test documentados; pytest/Ruff/mypy.
- **Evidência/riscos/rollback/DoD:** run ID/contagens/rollback; risco duplicação;
  transação + cleanup apenas em test; DoD sem `pass` e revisão cruzada.
- **Prompt de execução:**
  ```text
  Execute somente ECO-1501 em test isolado. Implemente persistência transacional do
  seed sem ampliar normalização. A fonte teste-rota é somente leitura. Dry-run deve
  escrever zero e --apply sem DB deve falhar. Não conclua sem rollback provado.
  ```
- **Entrega:** desbloqueia ECO-1502.

### ECO-1502 — Idempotência, proveniência e relatório completo

- **Resultado / prioridade / tamanho / executor:** carga repetível e explicável; P0;
  L; Codex.
- **Dependências/ADRs:** ECO-1501.
- **Contexto/leitura:** contrato Pindobal §§2–13, importers/fixtures/reconciler.
- **Arquivos:** importers, fixtures, relatório schema/tests; não painel/API admin.
- **Permitido/proibido:** upsert por chaves confiáveis, raw/provenance/rejections;
  fuzzy nunca merge automático; não chamar Google/OSRM externo.
- **Passos:** revalidar hashes; versionar regras; reconciliar soma; persistir refs/
  raw/field provenance; unchanged não atualiza timestamps.
- **Aceite/testes/comandos:** fixture inclui todos casos do contrato; duas execuções
  fixture idênticas; `lidos=criados+atualizados+inalterados+rejeitados+candidatos`;
  pytest ingestion e dry-run snapshot completo quando autorizado.
- **Evidência/riscos/rollback/DoD:** JSON+humano com IDs externos seguros; risco merge
  errado; rollback run; DoD com Place IDs ausentes marcados, nunca inventados.
- **Prompt de execução:**
  ```text
  Execute ECO-1502 após ECO-1501. Preserve autoridade SEMTUR/Google e faça fuzzy
  gerar somente candidatos. Não use rede. Prove idempotência e contagens com fixture
  e snapshot autorizado. Entregue relatórios e evidência, não apenas testes verdes.
  ```
- **Entrega:** desbloqueia ECO-1503/1504.

### ECO-1503 — Geometrias e associação PostGIS persistentes

- **Resultado / prioridade / tamanho / executor:** três origens e atores associados
  espacialmente; P0; L; Codex.
- **Dependências/ADRs:** ECO-1502.
- **Contexto/leitura:** contrato §§5/7, importer OSRM/spatial, repos/migrations.
- **Arquivos:** repository/service SQLAlchemy/PostGIS e testes; sem SQL em rota.
- **Permitido/proibido:** ST_DWithin/projeção/índices em test; não recalcular via rede,
  não aceitar lat/lon invertidos.
- **Passos:** persistir LineStrings/bounds/distância; comparar 1%; associar métricas e
  flags por origem; rejeitar geometria inválida.
- **Aceite/testes/comandos:** 884/777/866 pontos e 45.229/41.452/42.319 km na
  tolerância; query plans/índices; pytest + smoke PostGIS em test com rollback.
- **Evidência/riscos/rollback/DoD:** relatório/amostras; risco SRID/ordem; rollback
  transacional; DoD com revisão visual futura marcada para staging.
- **Prompt de execução:**
  ```text
  Execute ECO-1503 em test. Use PostGIS persistente e contrato de coordenadas; não
  chame OSRM. Prove contagens, tolerâncias, índices e rejeições. Mantenha SQL fora das
  rotas HTTP e entregue evidências espaciais sanitizadas.
  ```
- **Entrega:** desbloqueia ECO-1504.

### ECO-1504 — Carga dupla de Pindobal em test isolado

- **Resultado / prioridade / tamanho / executor:** Gate 1 comprovado em banco real;
  P0; M; Codex.
- **Dependências/ADRs:** ECO-1503, ECO-1402; owner autoriza dados descartáveis test.
- **Contexto/leitura:** contrato, scripts, release Gate 1.
- **Arquivos:** somente relatórios/checklists e fixes estritamente necessários;
  fonte externa intocável.
- **Permitido/proibido:** limpar fixture test pelo mecanismo aprovado e aplicar duas
  vezes; não staging/production.
- **Passos:** verificar fingerprint; advisors/migrations; dry-run; apply 1; smoke;
  apply 2; comparar hashes/contagens/timestamps; testar APIs com JWT test.
- **Aceite/testes/comandos:** comandos exatos do CLI descobertos por `--help`; zero
  duplicata, zero rejeição silenciosa, regiões/rotas/origens/atores >0, relatórios
  iguais onde esperado; frontend recebe Pindobal.
- **Evidência/riscos/rollback/DoD:** runs, counts, query snapshots; risco ambiente
  errado; parar se fingerprint colidir; cleanup test aprovado; DoD com Gate 1 verde.
- **Prompt de execução:**
  ```text
  Execute ECO-1504 somente após provar que test é descartável e diferente de todos
  os demais ambientes. Faça dry-run e duas cargas reais, registre advisors, contagens
  e timestamps. Pare ao menor sinal de production/staging. Não conclua por alegação.
  ```
- **Entrega:** desbloqueia ECO-1505/ECO-1602/ECO-1901.

### ECO-1505 — Pacote de promoção Pindobal

- **Resultado / prioridade / tamanho / executor:** conteúdo promovível e reversível;
  P0; M; indiferente.
- **Dependências/ADRs:** ECO-1504, ECO-1303/1305.
- **Contexto/leitura:** relatórios de carga, política editorial/mídia, Gate 1.
- **Arquivos:** manifesto de promoção, checksums, queries smoke e runbook; sem dados
  pessoais/secrets.
- **Permitido/proibido:** empacotar snapshot aprovado e pendências de reconciliação;
  não aplicar staging/production.
- **Passos:** fixar versão, hashes/importer/migrations; listar candidatos/rejeições;
  definir publish/unpublish e rollback lógico.
- **Aceite/testes/comandos:** pacote pode ser verificado offline; checksum e schema
  compatíveis; `Get-FileHash`/equivalente e dry-run reproduzido em test.
- **Evidência/riscos/rollback/DoD:** pacote assinado/revisado; risco promover conteúdo
  não licenciado; rollback para status draft/unpublished; DoD com aprovação editorial.
- **Prompt de execução:**
  ```text
  Execute ECO-1505 sem aplicar dados fora de test. Gere pacote verificável com hashes,
  versões, contagens, pendências e rollback lógico. Não marque candidatos fuzzy como
  aprovados. Exija revisão editorial e entregue handoff.
  ```
- **Entrega:** usado em staging e ECO-2202.

## Marco 16 — API administrativa

### ECO-1601 — Contrato e autorização da API administrativa

- **Resultado / prioridade / tamanho / executor:** fronteira `/api/v1/admin` segura;
  P0; L; Codex.
- **Dependências/ADRs:** ECO-1403, ECO-1501; ADR 0006.
- **Contexto/leitura:** OpenAPI, Auth/RBAC, erros/idempotência/paginação.
- **Arquivos:** `docs/openapi.yaml`, schemas/types, security dependencies e testes;
  não CRUD completo/UI.
- **Permitido/proibido:** contract-first e capability checks; não autorizar por
  user_metadata/`authenticated` isolado.
- **Passos:** definir envelopes, concurrency/version, idempotency, 401/403/409/422,
  upload/job references e audit metadata.
- **Aceite/testes/comandos:** OpenAPI lint/drift, generated TS, pytest auth matrix,
  Ruff/mypy; anonymous e editor errado recebem 403 sem vazar recurso.
- **Evidência/riscos/rollback/DoD:** diff contrato e matriz; risco BOLA; versão
  compatível/feature flag; DoD com revisão cruzada.
- **Prompt de execução:**
  ```text
  Execute ECO-1601 contract-first conforme ADR 0006. Não implemente todo CRUD nem UI.
  Prove autorização por capability e erros, regenere tipos e preserve compatibilidade.
  Exija revisão cruzada de Auth/OpenAPI antes de concluir.
  ```
- **Entrega:** desbloqueia ECO-1602–1605/ECO-1801.

### ECO-1602 — CRUD administrativo de regiões, rotas, origens e geometrias

- **Resultado / prioridade / tamanho / executor:** território editável sem SQL; P0;
  L; Codex.
- **Dependências/ADRs:** ECO-1601, ECO-1504.
- **Contexto/leitura:** spec §6.1, OpenAPI admin, services/repos.
- **Arquivos:** routers/services/repos/schemas/tests/OpenAPI; sem painel.
- **Permitido/proibido:** CRUD, validação espacial, optimistic concurrency e audit;
  não publicar incompleto nem SQL direto na rota.
- **Passos:** criar/editar/listar/arquivar agregados; validar origem única, SRID,
  bounds, status e ownership editorial.
- **Aceite/testes/comandos:** happy/401/403/404/409/422, concorrência e audit; pytest,
  Ruff/mypy/OpenAPI; integração test com rollback.
- **Evidência/riscos/rollback/DoD:** exemplos e audit rows; risco geometria inválida;
  archive/unpublish; DoD após revisão cruzada.
- **Prompt de execução:**
  ```text
  Execute somente ECO-1602. Siga router→service→repository, contrato admin e RBAC.
  Implemente território completo com concorrência/auditoria, sem painel e sem SQL em
  rotas. Prove erros negativos e rollback em test.
  ```
- **Entrega:** desbloqueia ECO-1802.

### ECO-1603 — CRUD administrativo de categorias, atores e vínculos

- **Resultado / prioridade / tamanho / executor:** inventário editorial operável; P0;
  L; Codex.
- **Dependências/ADRs:** ECO-1601, ECO-1504.
- **Contexto/leitura:** spec §6.1/6.2 e contrato Pindobal.
- **Arquivos:** admin actors/categories/accessibility/route links, tests/OpenAPI.
- **Permitido/proibido:** CRUD, provenance e links; não sobrescrever autoridade nem
  inventar Google ID/rating.
- **Passos:** validar contatos/coords/taxonomia; associar múltiplas rotas; audit e
  optimistic concurrency.
- **Aceite/testes/comandos:** duplicata/chave externa/conflito/permissions; pytest,
  Ruff/mypy/OpenAPI e integração test.
- **Evidência/riscos/rollback/DoD:** casos e audit; risco merge destrutivo; soft archive;
  DoD com revisão Google/RBAC.
- **Prompt de execução:**
  ```text
  Execute ECO-1603 sem painel. Preserve proveniência e autoridade, implemente CRUD e
  vínculos auditados e nunca invente identificador externo. Prove autorização,
  validação e concorrência com comandos reais.
  ```
- **Entrega:** desbloqueia ECO-1803.

### ECO-1604 — Workflow, alertas e reconciliação administrativa

- **Resultado / prioridade / tamanho / executor:** conteúdo revisável/publicável; P0;
  L; Codex.
- **Dependências/ADRs:** ECO-1602/1603; ADR 0006.
- **Contexto/leitura:** state machine, alert rules, reconciliation candidates/audit.
- **Arquivos:** services/repos/routers/tests/OpenAPI; sem UI.
- **Permitido/proibido:** transições e decisão fuzzy explícita; não merge automático,
  delete físico ou bypass do publish guard.
- **Passos:** draft/review/publish/archive; validação de completude; alert CRUD/janela;
  accept/reject/merge com motivo e audit.
- **Aceite/testes/comandos:** matriz de transições inválidas, separação de função,
  publish incompleto 422/409, reconciliação reversível; gates backend/OpenAPI.
- **Evidência/riscos/rollback/DoD:** audit before/after; risco publicação/merge errado;
  unpublish/compensação; revisão cruzada obrigatória.
- **Prompt de execução:**
  ```text
  Execute ECO-1604 conforme state machine aceita. Não crie UI e nunca mescle fuzzy
  automaticamente. Prove publish guard, segregação de funções, auditoria e rollback.
  Pare se a política editorial estiver ambígua.
  ```
- **Entrega:** desbloqueia ECO-1804.

### ECO-1605 — Bulk import, export e jobs administrativos

- **Resultado / prioridade / tamanho / executor:** operação em lote observável; P1;
  L; Codex.
- **Dependências/ADRs:** ECO-1601, ECO-1505, ECO-1604.
- **Contexto/leitura:** ingestion/jobs, idempotency, export/backup policy.
- **Arquivos:** job service/worker/admin endpoints/reports/tests/runbook.
- **Permitido/proibido:** upload validado, dry-run, async status/cancel, export checksum;
  não scheduler improvisado em request nem lock só em memória.
- **Passos:** fila/lock distribuído aprovado, Idempotency-Key, progress/retry/cost,
  artifact retention e authorization.
- **Aceite/testes/comandos:** duplicate key retorna mesmo resultado; restart retoma;
  export reimportável; pytest/concurrency; worker command e health documentados.
- **Evidência/riscos/rollback/DoD:** job IDs/checksums; risco duplicação/DoS;
  cancel/compensação; DoD com observabilidade e revisão.
- **Prompt de execução:**
  ```text
  Execute ECO-1605 com backend aprovado. Não execute conectores reais no CI. Crie
  jobs idempotentes, retomáveis e autorizados, com dry-run, relatórios e export
  verificável. Não use lock somente em memória. Entregue runbook e evidência.
  ```
- **Entrega:** suporta painel e operação.

## Marco 17 — Mídia editorial e avatar

### ECO-1701 — Fluxo real de avatar

- **Resultado / prioridade / tamanho / executor:** usuário escolhe, envia e vê avatar;
  P0; L; Codex.
- **Dependências/ADRs:** ECO-1402, ECO-1305, ECO-1601.
- **Contexto/leitura:** Storage service/stub, perfil Expo, docs signed upload atuais.
- **Arquivos:** backend storage/me, OpenAPI/types, picker/upload/profile UI e testes.
- **Permitido/proibido:** API oficial `createSignedUploadUrl`/upload aprovado, bytes e
  owner validation; nunca fabricar token, expor secret ou usar URL de production.
- **Passos:** picker/cancel; metadata+content validation; upload; persist media/profile;
  substituir por path versionado; rollback/cleanup em falha.
- **Aceite/testes/comandos:** cancel/invalid/oversize/401/A-B/upload/PATCH/rollback;
  pytest/Ruff/mypy/OpenAPI/TS/Jest e Storage test isolado.
- **Evidência/riscos/rollback/DoD:** objeto/row sem token em logs; risco EXIF/BOLA;
  restaurar avatar anterior/remover órfão; revisão cruzada Storage/Auth.
- **Prompt de execução:**
  ```text
  Execute ECO-1701 ponta a ponta usando APIs oficiais Supabase e ADR 0008. Remova o
  token falso e o Alert placeholder. Prove picker, upload, persistência, ownership e
  rollback em test; nunca exponha secret. Não conclua só com mocks.
  ```
- **Entrega:** fecha AC-PROFILE-01.

### ECO-1702 — Ingestão e processamento de mídia editorial

- **Resultado / prioridade / tamanho / executor:** imagens seguras/licenciadas; P0;
  L; Codex.
- **Dependências/ADRs:** ECO-1402, ECO-1305, ECO-1601.
- **Contexto/leitura:** media schema, docs limits/transforms, policy editorial.
- **Arquivos:** media service/job/models/migration/API/tests; sem painel completo.
- **Permitido/proibido:** sniff MIME, dimensões, EXIF strip, resize/optimize, alt/
  crédito/licença e quarantine; não confiar extension/client MIME.
- **Passos:** upload staging; processar derivados; checksum; estado processing/ready/
  rejected; audit; publicação só ready/licensed.
- **Aceite/testes/comandos:** fixtures benignas/mismatch/bomba/dimensões/EXIF; zero
  rede no CI; pytest/advisors/migration list e artifact metadata.
- **Evidência/riscos/rollback/DoD:** checksums/derivados; risco malware/copyright/custo;
  quarantine/delete compensado; revisão cruzada.
- **Prompt de execução:**
  ```text
  Execute ECO-1702 conforme ADR de mídia. Valide conteúdo real, remova EXIF, gere
  derivados e bloqueie publicação incompleta. Não implemente painel nem aceite MIME
  declarado como prova. Use fixtures e test isolado; entregue evidências.
  ```
- **Entrega:** desbloqueia ECO-1703/ECO-1803.

### ECO-1703 — Resolução, galeria e lifecycle de mídia

- **Resultado / prioridade / tamanho / executor:** capa/galeria/URLs corretas; P0; L;
  indiferente.
- **Dependências/ADRs:** ECO-1701/1702, ECO-1602/1603.
- **Contexto/leitura:** territorial DTO/repos, app images, CDN/overwrite guidance.
- **Arquivos:** media repository/service, OpenAPI/types, route/actor/profile UI/tests.
- **Permitido/proibido:** resolver public/signed URLs conforme ADR, ordenar e alt;
  não montar tokens por string, inventar imagem/rating ou sobrescrever mesmo path.
- **Passos:** joins/batch resolution; derivatives; cache headers; replace/delete;
  orphan reconciler e fallback explicitamente branded como indisponível.
- **Aceite/testes/comandos:** capa e galeria reais; expired signed URL refresh; delete
  referenciado bloqueado; job órfão dry-run; backend/frontend gates.
- **Evidência/riscos/rollback/DoD:** screenshots/API; risco N+1/stale; versioned paths e
  restore metadata; DoD sem imagens editoriais fixas em runtime.
- **Prompt de execução:**
  ```text
  Execute ECO-1703 sem fabricar conteúdo. Resolva mídia via backend/repository,
  implemente galeria, cache e lifecycle com paths versionados e job órfão dry-run.
  Prove URLs/alt/ordem e erros; preserve privacidade definida no ADR.
  ```
- **Entrega:** desbloqueia ECO-1901/1904.

### ECO-1704 — Matriz real de segurança do Storage

- **Resultado / prioridade / tamanho / executor:** policies comprovadas; P0; M; Codex.
- **Dependências/ADRs:** ECO-1701–1703, ECO-1401/1402.
- **Contexto/leitura:** testing strategy, migrations e docs Storage atuais.
- **Arquivos:** testes integração/scripts/relatório; não mudar UX salvo finding.
- **Permitido/proibido:** test isolado com anon, A, B, editor/admin; não production.
- **Passos:** INSERT/SELECT/UPDATE/upsert/DELETE/listing; URL pública/assinada; limite/
  MIME; revoke editor; advisors.
- **Aceite/testes/comandos:** cada célula allow/deny observada; nenhum listing público
  indevido; `supabase --help`, migration list/advisors e suite Storage.
- **Evidência/riscos/rollback/DoD:** IDs sintéticos e resultados; risco policy OR;
  rollback fixture; revisão cruzada e Gate 2 parcial verde.
- **Prompt de execução:**
  ```text
  Execute ECO-1704 só no projeto test isolado. Teste operações reais com identidades
  distintas, inclusive upsert INSERT+SELECT+UPDATE e listing. Consulte docs atuais,
  rode advisors e não conclua com testes estáticos.
  ```
- **Entrega:** gate de mídia.

## Marco 18 — Painel administrativo

### ECO-1801 — Shell do painel, autenticação e autorização

- **Resultado / prioridade / tamanho / executor:** acesso editorial seguro; P0; L;
  Google Antigravity.
- **Dependências/ADRs:** ECO-1601, ECO-1403, ADR 0006.
- **Contexto/leitura:** admin OpenAPI/types, Auth e design/accessibility.
- **Arquivos:** app/admin shell/routes/API hooks/tests; evitar `app/_layout` concorrente.
- **Permitido/proibido:** capability gate, sessão, 403, nav e error boundary; não CRUD.
- **Passos:** escolher superfície conforme ADR; login/MFA handoff; menu por capability;
  timeout/revocation; loading/error/offline.
- **Aceite/testes/comandos:** anonymous/non-editor bloqueados servidor+UI; revoked
  session perde acesso; TS/Jest/OpenAPI e teclado/leitor de tela.
- **Evidência/riscos/rollback/DoD:** vídeo/screenshot sem dados; risco UI-only auth;
  feature flag; revisão cruzada Auth.
- **Prompt de execução:**
  ```text
  Execute somente ECO-1801 sobre contrato admin congelado. O backend é a autoridade;
  esconda navegação mas também prove 403. Não implemente CRUD. Cubra sessão, revogação,
  loading/erro/acessibilidade e entregue evidência visual/testes.
  ```
- **Entrega:** desbloqueia ECO-1802–1804.

### ECO-1802 — Editor de regiões, rotas, origens e geometrias

- **Resultado / prioridade / tamanho / executor:** editor opera território; P0; L;
  Google Antigravity.
- **Dependências/ADRs:** ECO-1801, ECO-1602.
- **Contexto/leitura:** admin contract, map ADR, validation errors.
- **Arquivos:** admin screens/forms/hooks/tests; sem actor/media editor.
- **Permitido/proibido:** autosave/draft se ADR, concurrency, preview mapa; não bypass
  publish guard nem chamada Supabase direta.
- **Passos:** list/create/edit/archive; origin order/geometry preview; dirty state;
  409 conflict UX; accessible forms.
- **Aceite/testes/comandos:** keyboard, screen reader, invalid coord, concurrent edit,
  retry/offline; TS/Jest/E2E staging futuro.
- **Evidência/riscos/rollback/DoD:** screenshots/forms/API audit; risco perda edição;
  draft/version rollback; DoD com revisão editorial.
- **Prompt de execução:**
  ```text
  Execute ECO-1802 usando apenas API admin. Implemente território com validação,
  conflito e preview acessível; não publique via atalho. Prove fluxo por teclado e
  testes, preserve outros editores e entregue handoff.
  ```
- **Entrega:** parte do Gate 2.

### ECO-1803 — Editor de atores, vínculos e mídia

- **Resultado / prioridade / tamanho / executor:** atores e galerias editáveis; P0;
  L; Google Antigravity.
- **Dependências/ADRs:** ECO-1801, ECO-1603, ECO-1702/1703.
- **Contexto/leitura:** taxonomia/provenance/media contract.
- **Arquivos:** admin actor/media screens/hooks/tests; não reconciliação.
- **Permitido/proibido:** form, route links, accessibility, upload state/licença/alt;
  não fabricar Google data nem publicar asset processing.
- **Passos:** create/edit/archive; provenance conflicts; gallery order/cover; orphan
  warnings; 409/422 accessible.
- **Aceite/testes/comandos:** invalid URL/coord/license/MIME, multi-route, upload fail
  rollback; TS/Jest/OpenAPI and manual keyboard.
- **Evidência/riscos/rollback/DoD:** visual/audit rows; risco rights/duplication;
  draft/restore; DoD sem direct Supabase component access.
- **Prompt de execução:**
  ```text
  Execute ECO-1803 sobre APIs aprovadas. Trate proveniência, acessibilidade e mídia
  como dados obrigatórios conforme ADR; não invente Place ID/rating. Cubra rollback,
  conflito e teclado/leitor de tela. Entregue evidência.
  ```
- **Entrega:** parte do Gate 2.

### ECO-1804 — Fila de revisão, reconciliação e auditoria

- **Resultado / prioridade / tamanho / executor:** publicação governada; P0; L;
  Google Antigravity.
- **Dependências/ADRs:** ECO-1801–1803, ECO-1604.
- **Contexto/leitura:** state machine/capabilities/audit/reconciliation.
- **Arquivos:** admin review/reconcile/audit UI/tests.
- **Permitido/proibido:** diff, approve/reject, motivo, publish guard, unpublish;
  não editar audit log ou auto-merge fuzzy.
- **Passos:** filas filtráveis; before/after; separation of duties; incomplete errors;
  confirmation and focus management.
- **Aceite/testes/comandos:** editor não autoaprova quando proibido; candidate retains
  provenance; audit immutable; TS/Jest/E2E staging.
- **Evidência/riscos/rollback/DoD:** fluxo completo e audit IDs; risco publish errado;
  unpublish/decision reversal per ADR; revisão cruzada.
- **Prompt de execução:**
  ```text
  Execute ECO-1804 conforme workflow aceito. Nunca auto-merge fuzzy nem altere audit
  history. Prove segregação, publish guard, diffs, motivos e acessibilidade. Não
  conclua sem API audit e revisão cruzada.
  ```
- **Entrega:** completa Gate 2 após homologação.

## Marco 19 — Fechamento funcional do app público

### ECO-1901 — Dados reais, paginação e favoritos consistentes

- **Resultado / prioridade / tamanho / executor:** catálogo público fiel; P0; L;
  Google Antigravity.
- **Dependências/ADRs:** ECO-1504, ECO-1703.
- **Contexto/leitura:** audit A, AC home/routes/catalog, hooks/screens/adapters.
- **Arquivos:** public screens/hooks/DTO adapters/tests; não backend admin.
- **Permitido/proibido:** infinite pagination, cancellation, real favorite state;
  remover defaults inventados; não reintroduzir `mockData`.
- **Passos:** eliminar rating/review/local/image fictícios; usar `next_cursor`;
  AbortSignal; optimistic cache real/rollback; combined filters conforme contrato.
- **Aceite/testes/comandos:** >1 página sem duplicação; stale request cancelada;
  favorites persist/reload/failure; OpenAPI/TS/Jest and staging E2E.
- **Evidência/riscos/rollback/DoD:** screenshots/API fixtures; risco regressão visual;
  feature-level revert; DoD sem dado fabricado e estados comuns.
- **Prompt de execução:**
  ```text
  Execute ECO-1901 no app público. Remova todo dado fabricado apresentado como real,
  implemente paginação/cancelamento e favorito otimista de verdade. Não use mockData
  em runtime. Prove reload, rollback e mais de uma página.
  ```
- **Entrega:** Gate 3 parcial.

### ECO-1902 — Cadastro, login, linking e ciclo de sessão

- **Resultado / prioridade / tamanho / executor:** identidade recuperável; P0; L;
  Google Antigravity.
- **Dependências/ADRs:** ECO-1304, ECO-1403.
- **Contexto/leitura:** ADR 0007, Auth docs, `src/auth`, AC-GLOBAL/SEC.
- **Arquivos:** auth screens/session/navigation/tests/OpenAPI only if needed.
- **Permitido/proibido:** flows approved, secure storage/PKCE, conflict handling;
  não armazenar token insecurely ou autorizar por metadata editável.
- **Passos:** signup/signin/link/recovery/logout/delete request; guest preservation;
  web strategy; CAPTCHA/rate handling; cache purge.
- **Aceite/testes/comandos:** guest→account retains data; existing email conflict;
  refresh concurrency/logout/expired/deleted; TS/Jest, real Auth test staging/test.
- **Evidência/riscos/rollback/DoD:** test user IDs only; risk account takeover/loss;
  feature flag/recovery; cross-review Auth.
- **Prompt de execução:**
  ```text
  Execute ECO-1902 exatamente conforme ADR 0007. Preserve guest data, secure tokens
  and handle conflicts/recovery. Use test identities only, never log JWT, and prove
  real Auth flows plus negative cases before completion.
  ```
- **Entrega:** AC-GLOBAL/SEC.

### ECO-1903 — Preferências aplicadas e comportamento offline explícito

- **Resultado / prioridade / tamanho / executor:** acessibilidade/rede confiáveis;
  P0; L; Google Antigravity.
- **Dependências/ADRs:** ECO-1901, ECO-1902.
- **Contexto/leitura:** AC states/profile, AppContext/query client/accessibility screen.
- **Arquivos:** preferences hooks/state/theme/network UI/tests.
- **Permitido/proibido:** corrigir `screen_reader_mode`, aplicar contrast/text scale/
  locale, network awareness; não fila silenciosa.
- **Passos:** hydrate preferences; mutations with rollback/announcement; offline stale
  badge; block/explicit queue; reconnect invalidation.
- **Aceite/testes/comandos:** cold start prefs; toggle persists/applies immediately;
  airplane/degraded/timeout/reconnect; TS/Jest and device/web manual.
- **Evidência/riscos/rollback/DoD:** screenshots/announcements; risk inaccessible UI;
  reset preference/cache; DoD with WCAG/platform verification queued.
- **Prompt de execução:**
  ```text
  Execute ECO-1903. Corrija o contrato de preferência e aplique visualmente os valores
  remotos. Implemente offline/degraded states explícitos, nunca perca mutation em
  silêncio. Prove cold start, rollback, reconnect e acessibilidade.
  ```
- **Entrega:** Gate 3 partial.

### ECO-1904 — Perfil, trips, visitas e contatos

- **Resultado / prioridade / tamanho / executor:** ciclo público completo; P0; L;
  Google Antigravity.
- **Dependências/ADRs:** ECO-1701/1703, ECO-1902, ECO-1303/1306.
- **Contexto/leitura:** spec §§7.3/11.4, AC profile/catalog, current me API.
- **Arquivos:** backend trip/contact, OpenAPI/types/profile/actor UI.
- **Permitido/proibido:** start/complete/cancel trip, visits e consented events;
  sem impacto/selos pessoais, CO₂ inventado, claims ou contact data fabricados.
- **Passos:** contract gap first; implement service/repos; UI actions/errors; approved
  support/legal content; avatar display.
- **Aceite/testes/comandos:** trips/visitas permanecem factuais; visit ownership; consent
  off=no event; contact validation; backend/frontend full gates/E2E.
- **Evidência/riscos/rollback/DoD:** audit/events sanitized; greenwashing/PII risk;
  recompute/unpublish; cross-review domain/privacy.
- **Prompt de execução:**
  ```text
  Execute ECO-1904 contract-first. Complete trips/visits/profile/contact flows and use
  no personal badge/impact formulas and only approved contacts. Never fabricate ecological claims
  or telemetry consent. Prove ownership and rollback end to end.
  ```
- **Entrega:** closes profile/public feature gaps.

### ECO-1905 — Expo identity, deep links, env profiles and legal UI

- **Resultado / prioridade / tamanho / executor:** app installable and identifiable;
  P0; M; Google Antigravity + owner.
- **Dependências/ADRs:** ECO-1306, ECO-1902–1904; SDK 54 remains.
- **Contexto/leitura:** app.json/assets/Expo SDK54 docs/release decisions.
- **Arquivos:** `app.json`/config, `eas.json` only if approved, assets, linking tests,
  legal/consent UI/docs.
- **Permitido/proibido:** final name/IDs/version/permissions/env profiles/deep links;
  no Expo upgrade/signing secret/production publish.
- **Passos:** package/bundle IDs; scheme/universal links; icons/splash; permissions;
  dev/test/staging/prod env mapping; legal version acceptance.
- **Aceite/testes/comandos:** `npx expo-doctor`, `npx expo export --platform web`, config
  introspection, deep-link cases Android/iOS/web; no secrets bundle scan.
- **Evidência/riscos/rollback/DoD:** config output/screens; identifier irreversible risk;
  owner approval before first store build; DoD on SDK54.
- **Prompt de execução:**
  ```text
  Execute ECO-1905 with owner-approved identifiers/legal text. Stay on Expo SDK 54,
  never include signing secrets, and do not publish. Configure profiles/deep links,
  validate expo-doctor/export and prove no secret in bundle.
  ```
- **Entrega:** enables staging builds.

## Marco 20 — Infraestrutura e staging

### ECO-2001 — Runtime de produção e serviço FastAPI no Render (Nativo Python sem Docker)

- **Resultado / prioridade / tamanho / executor:** serviço web Python implantável no Render; P0; M;
  Codex / Antigravity.
- **Dependências / ADRs:** ECO-1302 (ADR 0005 aceito: Render Native Python); sem Docker.
- **Contexto e leitura:** ADR 0005, backend config/health/jobs, `pyproject.toml`, `DEVELOPMENT.md`.
- **Arquivos esperados:** `render.yaml` (opcional/declarativo), script de build (`pip install .`),
  script/comando de startup (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`),
  `backend/app/api/v1/health.py`, documentação de deploy. Nenhum Dockerfile.
- **Permitido / proibido:** runtime nativo Python 3.13, dependências fixadas, health/readiness
  HTTP `/api/v1/health`, graceful shutdown (SIGTERM); proibido uso ou dependência de Docker;
  proibido embutir segredos no repositório.
- **Passos:** definir comandos de build (`pip install .` ou `uv sync`) e startup do Uvicorn;
  garantir healthcheck `/api/v1/health` e tratamento de encerramento seguro (SIGTERM);
  documentar variáveis de ambiente necessárias no painel Render.
- **Aceite / testes / comandos:** build e startup validados localmente em runtime Python limpo;
  verificação do endpoint de health `/api/v1/health`; testes de carga e startup;
  `python -m pytest tests/test_health.py`.
- **Evidência / riscos / rollback / DoD:** comandos de build/start comprovados; risco de dependências
  nativas resolvido via `pyproject.toml`; rollback via painel do Render (1-clique / commit anterior);
  DoD sem qualquer dependência de Docker.
- **Prompt de execução:**
  ```text
  Execute ECO-2001 conforme ADR 0005 (Render Web Service Nativo Python sem Docker).
  Configure os comandos de build e start (Uvicorn), valide o healthcheck HTTP /api/v1/health
  e graceful shutdown sem Dockerfile ou contêineres. Não embuta segredos.
  Entregue manifesto render.yaml/documentação e handoff completo.
  ```
- **Entrega:** desbloqueia ECO-2002.

### ECO-2002 — CI/CD de staging com migration gate

- **Resultado / prioridade / tamanho / executor:** repeatable staging deployment;
  P0; L; Codex.
- **Dependências/ADRs:** ECO-2001, ECO-1401/1404, ECO-1905.
- **Contexto/leitura:** workflows current, testing strategy, provider/Supabase docs.
- **Arquivos:** workflows/scripts/runbooks; secrets only in platform store.
- **Permitido/proibido:** PR quality, artifacts, scans, approved staging deploy,
  migrations/advisors/smoke/rollback; no production job enabled.
- **Passos:** CI Windows+Linux; migration dry-run/check; artifact promotion; protected
  staging environment; deploy backend/web/build profiles.
- **Aceite/testes/comandos:** workflow dispatch on staging branch; failure prevents
  deploy; migration drift/advisor blocks; smoke and rollback rehearsal.
- **Evidência/riscos/rollback/DoD:** run URLs/digests without secrets; supply-chain
  risk; redeploy previous artifact; cross-review.
- **Prompt de execução:**
  ```text
  Execute ECO-2002 for staging only. Extend quality into artifact/scans/migration
  gates/deploy/smoke with approvals and redacted secrets. Keep production disabled.
  Prove a failed gate blocks deploy and rehearse rollback.
  ```
- **Entrega:** Gate 4 partial.

### ECO-2003 — Staging web, HTTPS, domains and CORS

- **Resultado / prioridade / tamanho / executor:** public staging endpoint; P0; M;
  Codex + owner.
- **Status:** `VERIFIED`
- **Dependências/ADRs:** ECO-2002, ECO-1306.
- **Contexto/leitura:** provider/domain decision, CORS/config/deep links.
- **Arquivos:** hosting/DNS docs/config/CORS tests; no production DNS.
- **Permitido/proibido:** staging domain/TLS/CORS/web deploy with approval; no wildcard
  CORS or secret client vars.
- **Passos:** DNS/TLS; API/web origins; cache headers; security headers; deep link
  association staging; smoke.
- **Aceite/testes/comandos:** HTTPS valid, unauthorized origin denied, allowed web
  works, health/build version visible; browser smoke and curl/Invoke-WebRequest.
- **Evidência/riscos/rollback/DoD:** URLs/cert report; DNS risk; rollback record/config;
  DoD with owner confirmation.
- **Evidências reais capturadas em staging:**
  - Home: `docs/finalization/evidence/ECO-2003/01_home_screen.png`
  - Rota Pindobal: `docs/finalization/evidence/ECO-2003/02_route_pindobal_screen.png`
  - Mapa Leaflet: `docs/finalization/evidence/ECO-2003/03_leaflet_map_screen.png`
  - Network/Console: `docs/finalization/evidence/ECO-2003/04_network_console_cors_evidence.png`
- **Confirmação do Owner:**
  > Owner confirmation:
  > Eu, Bruno Darwich, confirmo a homologação da ECO-2003 em staging, incluindo deploy, CORS, browser smoke, rollback e restauração. Production e seu DNS permaneceram fora do escopo.
- **Prompt de execução:**
  ```text
  Execute ECO-2003 only for staging with approved domains. Configure HTTPS, exact
  CORS, headers and web artifact; never use wildcard or expose backend secrets.
  Prove allowed/denied origins and rollback. Do not touch production DNS.
  ```
- **Entrega:** Gate 4 partial (`VERIFIED`).

### ECO-2004 — Observability, rate limits, runbooks and cost guards

- **Resultado / prioridade / tamanho / executor:** staging operable under incidents;
  P0; L; Codex.
- **Dependências/ADRs:** ECO-2002/2003, ECO-1404, ECO-1605.
- **Contexto/leitura:** spec §§12–14, logging/connectors and owner budgets.
- **Arquivos:** telemetry/rate limit config, dashboards/alerts/runbooks/tests.
- **Permitido/proibido:** Sentry/OTel approved, redaction, distributed limits/locks,
  SLOs; no PII/token/signed URLs in telemetry.
- **Passos:** request trace; latency/error/job/Google budget metrics; alerts; rate
  limits; on-call/rollback/restore runbooks.
- **Aceite/testes/comandos:** induced safe 5xx/timeout/rate limit triggers signal;
  logs redacted; dashboards show build/run; load smoke below budget.
- **Evidência/riscos/rollback/DoD:** alert screenshots/query IDs; telemetry cost/privacy;
  disable integration/previous config; cross-review.
- **Prompt de execução:**
  ```text
  Execute ECO-2004 in staging. Instrument errors/traces/metrics and distributed rate/
  cost guards with strict redaction. Prove alerts using synthetic failures, never PII.
  Deliver usable runbooks and rollback; do not configure production yet.
  ```
- **Entrega:** completes Gate 4.

## Marco 21 — QA, segurança, conformidade e homologação

### ECO-2101 — E2E web e auditoria de acessibilidade

- **Resultado / prioridade / tamanho / executor:** jornada web homologada em staging;
  P0; L; Antigravity.
- **Dependências/ADRs:** ECO-1501–1505, ECO-1601–1605, ECO-1701–1704,
  ECO-1801–1804, ECO-2003/2004.
- **Contexto/leitura:** critérios de aceite, estratégia de testes, design specs e
  `docs/finalization/release_checklist.md`.
- **Arquivos:** configuração/fixtures/testes E2E, relatório WCAG e evidências; não
  alterar contratos para acomodar o teste.
- **Permitido/proibido:** Playwright ou ferramenta aprovada, axe, teclado e viewport;
  sem chamadas Google reais, segredos ou dados pessoais.
- **Passos:** criar projeto E2E; preparar dados idempotentes; cobrir autenticação,
  região, catálogo, detalhe, favoritos, perfil, acessibilidade, rotas e viagens;
  executar teclado, foco, contraste e leitor semântico.
- **Aceite/testes/comandos:** jornadas críticas passam em Chromium; loading/vazio/
  erro/retry são exercitados; zero violação crítica/serious de axe; navegação completa
  por teclado; `npm run e2e:web` e `npm run a11y:web` documentados.
- **Evidência/riscos/rollback/DoD:** HTML/JUnit, vídeos/screenshots sem PII; risco de
  flakiness; rollback das fixtures/configuração; execução limpa duas vezes e revisão
  cruzada do Codex.
- **Prompt de execução:**
  ```text
  Execute ECO-2101 against staging. Build deterministic web E2E and accessibility
  coverage for every critical journey and loading/empty/error/retry state. Use only
  synthetic fixtures and mocked external providers. Deliver reports, redacted media,
  exact commands and defects; do not weaken product behavior to make tests pass.
  ```
- **Entrega:** relatório por critério, comandos/resultados, defeitos com severidade,
  evidências, riscos e recomendação objetiva para o Gate 5.

### ECO-2102 — E2E Android, acessibilidade e rede degradada

- **Resultado / prioridade / tamanho / executor:** build Android homologado em
  dispositivo/emulador representativo; P0; L; Google Antigravity.
- **Dependências/ADRs:** ECO-2002/2004, ECO-2101 e perfil EAS aprovado.
- **Contexto/leitura:** critérios de aceite, design specs, matriz de dispositivos e
  políticas de distribuição Android.
- **Arquivos:** configuração E2E mobile, scripts, matriz e evidências; sem alteração de
  credenciais/dispositivos fora do escopo aprovado.
- **Permitido/proibido:** Maestro/Detox/ferramenta aprovada, TalkBack e network shaping;
  sem produção, store upload ou dados reais.
- **Passos:** instalar build staging; cobrir jornadas críticas; testar voltar/deep
  link/permissões; TalkBack, fonte ampliada, redução de movimento; offline, perda e
  retomada de rede, timeout e retry.
- **Aceite/testes/comandos:** execução reproduzível em API Android mínima e atual
  definidas; foco/labels/ordem corretos; sem perda/corrupção após reconexão; crash-free;
  comando oficial `npm run e2e:android` ou equivalente documentado.
- **Evidência/riscos/rollback/DoD:** relatório, versão/ABI, vídeo redigido, logs; risco
  de fragmentação/flakiness; desinstalar build e restaurar fixture; repetição limpa e
  revisão cruzada do Codex.
- **Prompt de execução:**
  ```text
  Execute ECO-2102 on approved Android staging builds and the documented device
  matrix. Exercise critical journeys, TalkBack, large text, reduced motion, deep links
  and degraded/offline/recovered network. Never use production or personal data.
  Deliver exact build IDs, commands, redacted evidence and severity-ranked defects.
  ```
- **Entrega:** matriz dispositivo × cenário, comandos/resultados, defeitos, evidências,
  riscos e recomendação objetiva para o Gate 5.

### ECO-2103 — E2E iOS, acessibilidade e links universais

- **Resultado / prioridade / tamanho / executor:** build iOS homologado em simulador
  e dispositivo aprovado; P0; L; Google Antigravity.
- **Dependências/ADRs:** ECO-2002/2004, ECO-2101 e conta/perfil Apple aprovados.
- **Contexto/leitura:** critérios de aceite, design specs, matriz iOS e regras App Store.
- **Arquivos:** configuração/testes/matriz/evidências; certificados só no cofre EAS/
  Apple, nunca no repositório.
- **Permitido/proibido:** ferramenta E2E aprovada, VoiceOver, Dynamic Type e universal
  links; sem produção ou submissão à loja.
- **Passos:** instalar build staging; cobrir jornadas críticas; VoiceOver e ordem de
  foco; Dynamic Type/reduce motion; cold start/universal link; offline/recovery.
- **Aceite/testes/comandos:** matriz mínima/atual aprovada passa; links abrem contexto
  correto; nenhuma barreira crítica de VoiceOver; crash-free; comando oficial E2E e
  build ID documentados.
- **Evidência/riscos/rollback/DoD:** relatório e mídia redigida; risco de credenciais e
  diferenças dispositivo/simulador; revogar build de teste; repetição limpa e revisão
  cruzada do Codex.
- **Prompt de execução:**
  ```text
  Execute ECO-2103 only with approved iOS staging credentials/builds. Verify critical
  journeys, VoiceOver, Dynamic Type, reduced motion, cold-start universal links and
  network recovery on the agreed matrix. Keep certificates out of git and production
  untouched. Deliver build IDs, commands, evidence and ranked defects.
  ```
- **Entrega:** matriz iOS, comandos/resultados, defeitos, evidências, riscos e
  recomendação objetiva para o Gate 5.

### ECO-2104 — Auditoria final de segurança, desempenho e conformidade

- **Resultado / prioridade / tamanho / executor:** parecer integrado para homologação;
  P0; L; Codex.
- **Dependências/ADRs:** ECO-1401–1404, ECO-1801–1804, ECO-1901–1905,
  ECO-2001–2004, ECO-2101–2103.
- **Contexto/leitura:** LGPD/políticas Google, licenças, threat model, SLOs, SBOM,
  advisors e checklist de release.
- **Arquivos:** relatórios/checklists/runbooks e correções documentais; nenhuma
  mudança remota destrutiva.
- **Permitido/proibido:** SAST/SCA/secret scan, DAST seguro de staging, load smoke,
  restauração ensaiada e revisão jurídica humana; sem pentest invasivo, Google real em
  teste ou promoção automática.
- **Passos:** varrer repositório/imagens; validar RLS/grants/storage/Auth; testar
  autorização negativa e rate limits; medir SLO; revisar retenção/exclusão/exportação,
  termos/privacidade/licenças e uso/atribuição Google; reconciliar defeitos E2E.
- **Aceite/testes/comandos:** zero segredo e zero vulnerabilidade crítica/alta sem
  aceite formal; RLS/advisors verdes; restauração e rollback ensaiados; SLO atendido;
  documentos jurídico-conteúdo assinados; cada achado tem owner/data.
- **Evidência/riscos/rollback/DoD:** relatórios, hashes e atas redigidos; risco de falso
  positivo/dado sensível; quarentena/reversão de configuração; parecer dos dois
  executores e aceites humanos requeridos.
- **Prompt de execução:**
  ```text
  Execute ECO-2104 as a non-destructive final audit of staging and release artifacts.
  Combine SAST/SCA/secret scans, safe DAST/load checks, Supabase authorization/advisor
  evidence, restore/rollback rehearsal and LGPD/Google/license review. Never expose
  secrets or promote automatically. Deliver pass/fail per control, owner/date for every
  exception, and a signed recommendation for Gates 5 and 6.
  ```
- **Entrega:** matriz de controles e critérios, comandos/resultados, exceções aprovadas,
  evidências, riscos, rollback e recomendação formal aos Gates 5 e 6.

## Marco 22 — Go/no-go, publicação e operação assistida

### ECO-2201 — Go/no-go e pacote imutável de release

- **Resultado / prioridade / tamanho / executor:** decisão humana registrada sobre
  artefatos candidatos imutáveis; P0; M; humano/owner.
- **Dependências/ADRs:** Gates 1–6 completos e ECO-2104 aprovado.
- **Contexto/leitura:** todos os documentos de finalização, relatórios, ADRs, changelog
  e checklist de release.
- **Arquivos:** manifesto de release, checksums, ata e plano de mudança; sem código de
  produto.
- **Permitido/proibido:** reunir evidências e obter assinaturas; não aceitar gate
  incompleto, recriar artefato após aprovação ou acessar produção sem janela.
- **Passos:** congelar SHA/digests/build IDs/migrations; revisar blockers/exceções;
  confirmar backups, responsáveis, janela, comunicação, métricas e critérios de abort;
  registrar GO ou NO-GO.
- **Aceite/testes/comandos:** todos os gates anteriores têm evidência/owner/data; nenhum
  P0/P1 aberto sem waiver explícito; manifesto verificável; simulação de comunicação e
  rollback concluída.
- **Evidência/riscos/rollback/DoD:** ata assinada e hashes; risco de decisão incompleta;
  NO-GO preserva staging; decisão pertence ao owner e não ao agente.
- **Prompt de execução:**
  ```text
  Facilitate ECO-2201 without changing production. Freeze and hash the exact release
  artifacts, reconcile every Gate 1–6 item and exception, and present evidence,
  rollback/abort criteria and owners. The human owner must record GO or NO-GO; never
  infer approval or rebuild artifacts after sign-off.
  ```
- **Entrega:** manifesto, ata GO/NO-GO, signatários, janela, comunicação, riscos,
  critérios de abort e plano de rollback.

### ECO-2202 — Promoção controlada de migrations e Pindobal

- **Resultado / prioridade / tamanho / executor:** schema e dados Pindobal promovidos
  com integridade e reconciliação; P0; L; Codex.
- **Dependências/ADRs:** ECO-2201=GO, ECO-1401/1404, ECO-1902–1905; acesso production
  explícito e janela aprovados.
- **Contexto/leitura:** runbooks de migration/importação, contrato Pindobal, manifestos,
  backups/PITR e checklist Gate 7.
- **Arquivos:** somente artefatos já aprovados; relatórios de execução fora de áreas com
  segredos.
- **Permitido/proibido:** preflight read-only, backup, migration oficial e ingestão
  idempotente na janela; proibido continuar após abort threshold, editar fonte
  `teste-rota`, inventar Place ID ou usar Dashboard para schema.
- **Passos:** validar target e backup/PITR; registrar estado anterior; aplicar migrations
  em ordem; advisors/testes negativos; dry-run/import/aprovação/publicação Pindobal;
  reconciliar contagens/rejeições e smoke.
- **Aceite/testes/comandos:** manifestos local/remoto iguais; zero advisory crítico;
  segunda importação não duplica; contagens/rejeições explicadas; leitura pública e
  restrições privadas comprovadas; rollback testado antes da janela.
- **Evidência/riscos/rollback/DoD:** IDs de backup/migration/run e relatórios redigidos;
  risco máximo de dados; abortar e executar runbook aprovado/restauração se necessário;
  owner valida contagens e Codex revisa comandos.
- **Prompt de execução:**
  ```text
  Execute ECO-2202 only after an explicit human GO, production authorization and
  approved window. Verify the exact project before every write, record backup/PITR,
  apply only versioned migrations, run advisors/negative tests, then execute the
  idempotent Pindobal pipeline with reconciliation. Stop on any abort threshold. Never
  alter the read-only source or invent IDs. Deliver redacted run IDs and counts.
  ```
- **Entrega:** linha do tempo, comandos/resultados redigidos, manifests, contagens/
  rejeições, owner approvals, riscos/incidentes e estado/rollback final.

### ECO-2203 — Publicação controlada de API e Web em production

- **Resultado / prioridade / tamanho / executor:** API e Web promovidas ao ambiente de
  production com rollback comprovado; P0; L; Codex.
- **Dependências/ADRs:** ECO-2202 aprovado, artefatos ECO-2201, domínio e política de
  rollout aprovados.
- **Contexto/leitura:** manifestos, runbooks, DNS/TLS/CORS, SLOs e checklist Gate 7.
- **Arquivos:** configurações de produção previamente revisadas; não recompilar nem
  alterar escopo durante a janela.
- **Permitido/proibido:** promover digest/web artifact exatos, rollout gradual e smoke;
  sem submissão às lojas nesta task, publicação irreversível ou segredo em log.
- **Passos:** promover API/web; validar TLS/CORS/deep links; executar smoke sintético;
  iniciar rollout gradual e observar abort thresholds/SLOs.
- **Aceite/testes/comandos:** versões/digests iguais ao manifesto; saúde e jornadas
  mínimas passam; rollback do artefato anterior é acionável; métricas ficam no SLO.
- **Evidência/riscos/rollback/DoD:** URLs/digests/deploy IDs; risco DNS/propagação;
  reverter tráfego/artefato; owner decide continuidade e assina Gate 7.
- **Prompt de execução:**
  ```text
  Execute ECO-2203 only with the approved immutable manifest and explicit production
  authorization. Promote the exact API and Web artifacts, verify TLS/CORS/deep links,
  run synthetic smoke and use gradual rollout with abort thresholds. Do not submit
  mobile builds or rebuild during release. Deliver URLs, IDs, metrics and redacted proof.
  ```
- **Entrega:** versões/IDs/URLs, comandos/resultados, métricas, incidentes, decisão do
  Gate 7 e estado final do rollback/rollout.

### ECO-2204 — Publicação controlada Android e iOS

- **Resultado / prioridade / tamanho / executor:** builds homologados publicados nas
  lojas/canais aprovados; P0; L; humano/owner.
- **Dependências/ADRs:** Gate 7 `VERIFIED`, artefatos ECO-2201, contas e metadados de
  lojas aprovados.
- **Contexto/leitura:** manifestos, privacy disclosures, listings, política OTA/rollout
  e checklist Gate 8.
- **Arquivos:** metadados/configurações aprovados; certificados ficam nos cofres das
  plataformas, nunca no repositório ou prompt.
- **Permitido/proibido:** submeter build ID exato e rollout gradual; sem rebuild,
  troca de identidade/escopo ou avanço após bloqueio da review.
- **Passos:** conferir checksum/build ID; validar listing, licenças e disclosures;
  submeter; registrar review; liberar canais gradualmente; verificar instalação,
  upgrade, deep links e política de atualização.
- **Aceite/testes/comandos:** builds iguais ao manifesto; stores aceitam metadados;
  instalação/upgrade/smoke passam; rollout pode ser pausado; status por loja registrado.
- **Evidência/riscos/rollback/DoD:** submission/build/release IDs e capturas redigidas;
  risco de review/propagação; pausar rollout/revogar canal conforme plataforma; owner
  assina publicação.
- **Prompt de execução:**
  ```text
  Execute ECO-2204 only after Gate 7 and explicit store authorization. Submit the exact
  signed Android/iOS build IDs from the immutable manifest, verify listings, privacy
  disclosures, licenses, install/upgrade and deep links, and use gradual rollout. Never
  expose certificates or rebuild. Deliver store IDs/status, evidence and rollback state.
  ```
- **Entrega:** loja/canal/versão/build/submission IDs, comandos/cenários, status de
  review/rollout, evidências, riscos e rollback.

### ECO-2205 — Operação assistida, aceite final e handoff

- **Resultado / prioridade / tamanho / executor:** primeira janela Web/API/lojas operada
  e transferida aos responsáveis; P0; L; humano/owner.
- **Dependências/ADRs:** ECO-2204 publicado ou rollout aprovado; Gate 7 concluído.
- **Contexto/leitura:** SLOs/dashboards, runbooks, suporte, retenção, matriz RACI e
  checklist Gate 8.
- **Arquivos:** registro de operação, incidentes, lições e documentação final; nenhuma
  correção improvisada em produção.
- **Permitido/proibido:** observar, triar, executar runbooks aprovados e abrir tasks;
  sem hotfix fora do fluxo, consulta de PII desnecessária ou fechamento sem sign-off.
- **Passos:** acompanhar 24–72 h definidas pelo owner; revisar disponibilidade/erros/
  latência/custos/auth/importações; confirmar backup/alertas/suporte; tratar incidentes;
  realizar handoff e retrospectiva.
- **Aceite/testes/comandos:** SLO e orçamento dentro dos limites; nenhum incidente P0/P1
  aberto; alertas têm owner; restauração/rollback continuam acionáveis; suporte e DPO
  conhecem fluxos; aceite final assinado.
- **Evidência/riscos/rollback/DoD:** dashboard/incidente/ata redigidos; risco operacional;
  pausar rollout ou rollback aprovado; ownership e backlog residual explícitos.
- **Prompt de execução:**
  ```text
  Execute ECO-2205 as the approved assisted-operation window. Monitor SLOs, errors,
  auth, data integrity, provider cost, Web/API and store rollout; triage only through
  approved runbooks and open tasks for every residual issue. Do not improvise production
  hotfixes or inspect unnecessary PII. Deliver signed handoff and final Gate 8 decision.
  ```
- **Entrega:** período observado, métricas/resultados, incidentes, backlog residual,
  responsáveis, aceite final e condição operacional/rollback.

## Modelo obrigatório de entrega de qualquer task

Além do campo **Entrega** específico, o executor encerra a task com: status objetivo;
arquivos alterados; comandos exatos e resultados; critérios de aceite um a um;
evidências com caminho/URL/ID e redação de segredos; riscos e limitações; rollback
executável; pendências/decisões; e indicação do próximo gate desbloqueado. Uma task só
pode ser marcada `VERIFIED` quando outra pessoa ou agente reproduzir a evidência
material definida em `ai_coordination.md`.
