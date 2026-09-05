# ECO-2602 — Baseline funcional e matriz de dependências

Data: 05/09/2026. Task de diagnóstico local, sem alteração de funcionalidades.
Resultado: baseline local verificada; lacunas e gates identificados. Não é aprovação
do lançamento, da carga das dez rotas ou dos ambientes remotos.
Tasks/status/ordem continuam exclusivamente em [project_status.md](project_status.md).

## Revisão exata e alcance

- Branch: `codex/fix-staging-smoke-host`.
- Commit-base: `c49a83ca1995d281e10593ce1866c030a9fd68f3`.
- Última alteração de produto anterior: `2d39005` (localização, notice e headers).
- `git diff HEAD -- backend econexao-app/app econexao-app/src econexao-app/package.json
  econexao-app/package-lock.json supabase` não mostrou diferenças antes dos checks.
- As alterações preexistentes fora do commit eram documentos e artefatos, não código
  runtime. Seus 22 arquivos foram inventariados por SHA-256 antes do export/browser:
  oito documentais e quatorze de resultados/imagens. Nenhum foi apagado, movido ou
  incorporado ao commit da ECO-2602.
- Oito worktrees locais foram listadas; nenhuma foi trocada, mesclada ou limpa.
  Código presente em outra worktree não foi considerado integrado na baseline.
- Há 25 arquivos SQL em `supabase/migrations`; isso é contagem local, não prova de
  aplicação, sincronização remota ou ausência de drift.

Ambiente: Windows/PowerShell; Node 24.13.0, npm 11.6.2; Python dos testes
`backend/.venv/Scripts/python.exe` 3.13.12. O Python global 3.13.13 foi usado somente
para verificações auxiliares de arquivos. Pacotes observados no venv: FastAPI 0.141.1,
Pydantic 2.13.4, SQLAlchemy 2.0.52, psycopg 3.3.4, pytest 9.1.1, Ruff 0.16.2 e mypy 2.3.0.
Essas versões descrevem o ambiente efetivamente testado, não uma atualização de dependências.

## Evidências reproduzidas

| Diretório | Comando | Exit code | Resultado |
|---|---|---:|---|
| `econexao-app` | `npm run typecheck` | 0 | TypeScript sem erros |
| `econexao-app` | `npm run openapi:check` | 0 | Tipos sincronizados com contrato versionado |
| `econexao-app` | `npm test -- --watch=false` | 0 | 41 suítes, 240 testes, 38,858 s |
| `backend` | `.\.venv\Scripts\python.exe -m pytest -q` | 0 | 660 testes, 17 avisos, 54,53 s |
| `backend` | `.\.venv\Scripts\python.exe -m ruff check app tests scripts` | 0 | Sem findings |
| `backend` | `.\.venv\Scripts\python.exe -m mypy app scripts` | 0 | 124 arquivos sem erros |
| `backend` | `.\.venv\Scripts\python.exe scripts/scan_secrets.py --root ..` | 0 | `SECRET_SCAN=OK`, padrões de alta confiança do scanner existente |
| `econexao-app` | `npm run export:web -- --output-dir .tmp-eco2602-dist` | 0 | Bundle Web gerado com configuração sintética |
| `econexao-app` | `npm run test:browser -- --config .tmp-eco2602/playwright.config.ts` | 0 | 4/4 Playwright Chromium, desktop e viewport mobile, 44,7 s |

Os primeiros checks TypeScript/contrato e Ruff/mypy foram executados em sequência
condicional: o segundo só roda quando o primeiro retorna zero. Não houve instalação,
atualização de dependências, migration ou chamada Google real por esta task.

O pytest usa a configuração local existente e doubles dos testes; esta execução não
é ensaio hermético de instalação nem teste de integração com PostgreSQL remoto.
O scanner não é prova absoluta de ausência de todos os tipos possíveis de segredo.

### Export/browser isolados e reproduzíveis

O export foi executado com variáveis temporárias somente no processo:

```powershell
$env:EXPO_NO_DOTENV='1'
$env:EXPO_PUBLIC_API_URL='http://localhost:8000/api/v1'
$env:EXPO_PUBLIC_SUPABASE_URL='https://unit-test.supabase.co'
$env:EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY='sb_publishable_unit_test'
npm run export:web -- --output-dir .tmp-eco2602-dist
```

Esses valores são sintéticos, não credenciais operacionais. O build não carregou
`.env` via Expo. O browser intercepta API, Auth e tiles; os testes continuam exatamente
os versionados em `e2e/web-a11y-browser.spec.ts`. Embora um título diga “origens reais”,
os dados vêm de fixtures. Resultado é WEB_LOCAL, não STAGING, GPS real ou DEVICE.

Para preservar `dist/`, screenshots e relatórios antigos, um helper ignorado foi
criado em `.tmp-eco2602/`: cópia de `scripts/serve-dist.mjs` alterando somente
`../dist` para `../.tmp-eco2602-dist`, e configuração que importa a configuração
Playwright original, usa `testDir: '../e2e'`, `outputDir: '../.tmp-eco2602-results'`,
reporter `list` e servidor `node .tmp-eco2602/serve.mjs` com `cwd: process.cwd()`.
Porta 8082, um worker, casos, asserts, timeouts e projetos originais foram preservados.
Os helpers e outputs são regeneráveis e não integram o commit.

Bundle JS: `entry-b60a237533816a852c8fa8912d276110.js`, 2.548.619 bytes,
SHA-256 `ddd901d5ec94b148d8c1b67d100633b71caa007c219dc9fa79f2886bef114260`.
Export também listou imagens de aproximadamente 3,49 MB e 1,87 MB. São tamanhos
dos artefatos sem medir transferência comprimida/cache; não são latência nem prova
de que todos sejam baixados na primeira tela. Medição/otimização pertence à ECO-2615.

## Pendências preexistentes preservadas

| Grupo | Arquivos/caminhos | Tratamento nesta task |
|---|---|---|
| Documentação ainda não commitada | `docs/README.md`, `deployment_google_routes.md`, `documentation_matrix.md`, `finalization/ANTIGRAVITY_CONTINUATION_PROMPT.md`, `finalization/decisions_needed.md`, `mapa_dinamico/tasks.md` | Preservar; relatos de homologação/categorização exigem revisão própria antes de commit |
| Evidência e política locais | `docs/privacy_location_policy.md`, `docs/relatorio_reconciliacao_rq03.md` | Preservar como arquivos locais não versionados; não presumir disponibilidade num clone |
| Artefatos antigos | `econexao-app/screenshots/`, `playwright-report/`, `test-results/` | Preservar quatorze arquivos pendentes; não incluir em commit de baseline |
| Artefatos desta execução | `.tmp/eco2602/`, `econexao-app/.tmp-eco2602*/` | Saídas separadas e ignoradas; nenhuma política global de remoção alterada |

A ECO-2404 continua responsável pela política ampla de artefatos. Separar para
esta execução/commit não significa ter saneado todo o histórico Git.

## Matriz por ID: reutilização, lacuna e destino

As suítes acima exercitam testes locais destas áreas. Não promovem cada aceite
remoto individual. A leitura independente da matriz não executou testes nem remoto.
“Absorver” significa concluir a evolução na sucessora, não aprovar a base inteira.

| Base | Evidência concreta na árvore atual | Lacuna / destino antes de liberar consumidor |
|---|---|---|
| ECO-2005 | `app/ingestion/seed_pindobal.py`, `pindobal_repository.py`, `scripts/verify_pindobal_promotion_package.py`, `tests/test_pindobal_persistence.py` | Runner `staging_promotion_runner.py` e teste correspondente ausentes nesta árvore; handoff aponta outra worktree. ECO-2603 deve decidir como reconciliar base; ECO-2605 incorpora/reproduz o subescopo necessário antes de carga |
| ECO-1902 | `src/auth/sessionManager.ts`, `AuthModal.tsx`, testes de sessão/auth | E-mail/senha e linking existentes; OAuth Google não encontrado. Evolução absorvida em ECO-2606; callback e isolamento reais ainda a homologar |
| ECO-1904 | `api/v1/me.py` GET/POST trips, hooks de histórico, `test_me_trips_impact.py` | Pausar/retomar/finalizar não encontrados nos endpoints inspecionados. Absorver em ECO-2607, sem reimplementar perfil/contatos que já passam |
| ECO-2304 | `MapAdapter.web.tsx` cria ícone numérico e chama `clusterPins` | Novo desenho sem clusters em ECO-2608; testes da baseline aprovam o comportamento antigo |
| ECO-2307 | Câmera, filtros e zoom no adapter; Playwright local passa | Densidade/seleção novas absorvidas em ECO-2608; posição/origem em ECO-2609; nativo continua adiado |
| ECO-2512 | `LocalCatalogPreview.tsx` filtra e mostra três atores em `View` | Carrosséis novos em ECO-2610, experiências ECO-2611 e ordenação ECO-2612; não herdam aprovação do preview atual |
| ECO-1401 | `scripts/check_test_isolation.py` e testes locais | Verifica dev × test por configuração; não comprova os quatro ambientes reais. Confirmar identidade/isolamento antes da primeira operação remota aplicável |
| ECO-1402 | Migrations Storage e `avatar_storage.py`/`editorial_storage.py`; testes HTTP | Aplicação SQL, grants/RLS/advisors e upsert reais não observados. Gate antes de upload/carga dependente de Storage |
| ECO-1403 | `services/editorial_authorization.py`, testes de capabilities/escopo/revogação | RBAC local reutilizável; membership/revogação persistentes e isolamento real ainda precisam matriz. Não adiar segurança junto do painel |
| ECO-1404 | Scanner passou; configuração e runbooks existem | Backup/restore não ensaiados. Runbook de promoção cita módulos ausentes: corrigir comandos antes de uso remoto; ECO-2603 registra dependência e gate ECO-2104 continua |
| ECO-1704 | `scripts/verify_storage_policies.py` exige isolamento e faz operações A/B | Executor remoto com escrita, não executado. Matriz real deve ser autorizada e comprovada; mock não a substitui |
| ECO-1601 | API admin, contrato e testes de 401/negação/capabilities | Contratos locais reutilizáveis; autorização persistente/cross-region real antes da carga que usar admin |
| ECO-1602 | CRUD territorial service/repository/API e testes | SQL, auditoria e concorrência reais pendentes; avisos de mocks a conferir. Subescopo rotas/origens/geometrias precisa gate antes da ingestão |
| ECO-1603 | CRUD atores/categorias/vínculos e testes | Mesmos limites de SQL/auditoria/concorrência e avisos de mocks; homologar somente o subescopo usado pela equipe, sem exigir painel completo |
| ECO-1604 | `repositories/workflow_admin.py` publish guard/transições e testes | Publicação de região falha explicitamente por requisitos não modelados. ECO-2603 define fluxo aprovado para novas regiões; ECO-2605 não pode contornar o guard para Altamira |
| ECO-1605 | Schemas de jobs/idempotência, importadores específicos, jobs POI/mídia | API bulk import/export e worker persistente com retomada não encontrados em `backend/app`. Absorver apenas pipeline da equipe em ECO-2605; escopo amplo permanece parcial |
| ECO-2001 | `render.yaml`: Python, Uvicorn e health path | Versão servida, disponibilidade e cold start remotos não observados; medição ECO-2615 e publicação ECO-2203 |
| ECO-2002 | `.github/workflows/staging-deploy.yml`, migration gate e smoke tests | CI/deploy reais, advisors e rollback não executados; gate antes de promover dados/API |
| ECO-2003 | Factory/CORS/headers em `app/main.py`; testes passam | HTTPS, origem real, CORS remoto e artefato servido pendentes; homologar em staging antes de ECO-2101 |
| ECO-2004 | `core/rate_limit.py` em memória, testes de rate limits/runbooks | Limite por processo não é limite financeiro global persistente. ECO-2615 mede/define guardas por serviço e múltiplas instâncias; alertas/SLO reais em homologação |

Referências de código são relativas a `backend/` ou `econexao-app/`, conforme a camada.
Inspeção adicional: `docs/runbooks/production_promotion_runbook.md` cita
`app.scripts.check_environment` e `app.ingestion.ingest_pindobal`, não encontrados na
árvore. Não executar esse roteiro sem correção e autorização; os comandos existentes
devem ser descobertos no entrypoint real, não deduzidos desses nomes.

## Avisos e condições para prosseguir

1. Pytest passou com 17 avisos: depreciação Starlette/TestClient e corrotinas AsyncMock
   não aguardadas em testes de repositórios admin/mídia. Não provar persistência real
   com esses doubles; verificar mocks/asserções quando mexer nos consumidores
   ECO-1602/1603/1703 e ECO-2605. Não alterar runtime para silenciar o aviso sem diagnóstico.
2. Playwright atual ainda testa clusters numéricos, não o desenho aprovado sem clusters.
   Ele serve de baseline de regressão; ECO-2608 deve atualizar o aceite visual.
3. Templates/readmes antigos descrevem ausência de Git/backend ou sessão Web em memória.
   Não usar esses snapshots para tomar decisões atuais. Reconciliar referências
   diretamente afetadas na ECO-2603; arquivamento amplo permanece pós-evento.
4. Gates remotos não bloqueiam a conclusão deste diagnóstico local, mas bloqueiam a
   ação remota consumidora. Não foram acessados staging/production, consoles, billing,
   fonte externa `teste-rota`, credenciais ou serviços Google por esta task.

## Marcos de commit e encerramento

- Revisão documental independente: APPROVE, sem correções obrigatórias; matriz e
  contadores conferidos. Raiz verificou links, 205 IDs únicos, diff e preservação
  por SHA-256 dos 22 arquivos anteriores; scanner repetido com `SECRET_SCAN=OK`.
- ECO-2601: `c49a83c`, inventário único revisado.
- ECO-2602: somente este relatório e atualização correspondente em `project_status.md`;
  commit local após revisão, mensagem `docs(baseline): verify ECO-2602 local foundations`.
- Próximos incrementos: commit por comportamento coerente, testes pertinentes,
  diff revisado, evidência e referência ao ID. Não incluir artefatos/preexistentes por
  arrasto. Nenhum commit implica push, merge, deploy ou carga remota.
- Rollback desta entrega documental: reverter apenas seu commit se necessário,
  preservando alterações anteriores. Nenhum dado/schema foi alterado.
- Próxima task: **ECO-2603**, reconciliar decisões/contratos/pré-requisitos usando a
  matriz acima. A task deve decidir os resíduos bloqueadores antes de liberar os
  consumidores; não deve implementar implicitamente Google login, mapa ou importador.
