# ECO-2401 — Baseline protegida e inventário preliminar

Data da captura: 27/08/2026  
Escopo: somente inventário; nenhuma limpeza, remoção, movimentação ou decisão da ECO-2402.  
Estado: `PARTIAL`; inventário criado, mas H24.1 não pode ser comprovado retroativamente em sua integralidade porque a captura inicial não registrou hashes do worktree. Sujeito à verificação independente e aos gates H24.2/H24.3.

## Mini-brief

- **Task:** ECO-2401.
- **Objetivo observável:** preservar a baseline local e registrar um inventário versionável, rastreável e sanitizado antes de qualquer limpeza.
- **Dependências verificadas:** autorização do owner dada pelo prompt; H24.1 é o gate desta task.
- **Documentos lidos:** `AGENTS.md`, `docs/README.md`, `docs/backend_integration_spec.md`, `docs/backend_integration_tasks.md`, `docs/ai_task_playbook.md` e todos os arquivos presentes em `docs/repository_health/` antes desta edição.
- **Arquivo esperado:** somente este novo documento.
- **Contrato/schema afetado:** nenhum.
- **Dados e ambiente:** inspeção local e somente leitura do Git e de metadados de arquivos; nenhum remoto, produção ou conteúdo de `.env` acessado.
- **Testes:** reprodução de contagens, cobertura das seis áreas, revisão de candidatos/evidência/confiança, busca sanitizada de segredo no novo documento e comparação final do status/diff.
- **Fora do escopo:** ECO-2402, limpeza, move/delete, alteração de código/configuração, build, deploy, remoto, commit, stash, reset, checkout e formatação em massa.
- **Riscos/ações que exigem aprovação:** qualquer remoção material depende da matriz ECO-2402 aprovada; itens com consumidor ou proveniência incertos dependem de H24.3 e confirmação do owner.

## Ponto de retorno e contagens

| Campo | Captura |
|---|---|
| Branch | `staging` |
| Commit (`HEAD`) | `a82efbddddccc37a8384b951b16191c059e859af` |
| Arquivos tracked | 530 |
| Arquivos untracked, expandidos | 43 |
| Entradas em `git status --short` | 36 (23 modificados e 13 grupos/caminhos untracked) |
| Caminhos em `git status --short --untracked-files=all` | 66 (23 modificados e 43 arquivos untracked) |
| Caminhos ignored enumerados | 93.328; contagem observada, não exaustiva devido a avisos de permissão |
| Alteração criada pela ECO-2401 | apenas `docs/repository_health/inventory_ECO-2401.md`, dentro do grupo untracked já existente `docs/repository_health/` |

O commit acima é somente um identificador de baseline; nenhum comando destrutivo foi usado para criar um ponto de retorno. O working tree já estava sujo e é tratado integralmente como trabalho do usuário.

### Baseline v2 verificável do estado corrente

Após a lacuna da captura inicial ser identificada, duas capturas SHA-256 completas e consecutivas produziram resultado idêntico. A segunda foi materializada em `docs/repository_health/baseline_ECO-2401.sha256`.

| Campo | Baseline v2 |
|---|---|
| Branch/HEAD | `staging` / `a82efbddddccc37a8384b951b16191c059e859af` |
| Tracked observados | 530 |
| Untracked observados antes do manifesto | 46, incluindo este inventário |
| Arquivos elegíveis com hash | 573 |
| Excluídos | qualquer caminho `.env*`, ignored, este inventário e o próprio manifesto |
| Algoritmo/formato | SHA-256 em minúsculas, dois espaços e caminho relativo normalizado com `/` |

Essa baseline v2 protege o estado corrente a partir da captura registrada e permite detectar alterações posteriores nos arquivos elegíveis. Ela não demonstra retroativamente que o conteúdo dos 23 modificados e 43 untracked da primeira janela permaneceu intacto durante a escrita inicial; por isso o status histórico de H24.1 continua `PARTIAL`.

### Contagens por área

As contagens abaixo usam `git ls-files` e `git ls-files --others --exclude-standard`. “Bytes” soma arquivos tracked e untracked presentes no worktree; dependências/caches ignorados não entram nessa soma.

| Área | Tracked | Untracked | Total de arquivos | Bytes |
|---|---:|---:|---:|---:|
| Raiz/repositório inteiro | 530 | 43 | 573 | não somado |
| `backend/` | 182 | 0 | 182 | 1.514.286 |
| `econexao-app/` | 152 | 29 | 181 | 14.602.875 em 179 caminhos resolvidos; dois nomes escapados pelo Git não entraram no somatório |
| `supabase/` | 26 | 0 | 26 | 151.870 |
| `landing-page/` | 57 | 0 | 57 | 54.754.613 |
| `docs/` | 96 | 14 | 110 antes deste arquivo; 111 após sua criação | 6.480.647 antes deste arquivo |

O total de arquivos do app é 181. A medida de bytes é um limite inferior porque o somatório baseado na saída textual de `git ls-files` não resolveu dois nomes escapados; isso não autoriza inferência ou limpeza.

## Alterações locais preexistentes preservadas

Lista sanitizada e integral das 36 entradas colapsadas observadas antes da criação deste documento:

```text
 M docs/README.md
 M docs/finalization/artifacts/e2e_web_and_a11y_report.md
 M econexao-app/app/(tabs)/(routes)/index.tsx
 M econexao-app/app/_layout.tsx
 M econexao-app/app/route/[routeId]/map.tsx
 M econexao-app/package-lock.json
 M econexao-app/package.json
 M econexao-app/src/components/admin/WorkflowReviewQueue.tsx
 M econexao-app/src/components/common/AppHeader.tsx
 M econexao-app/src/components/common/ErrorBoundary.tsx
 M econexao-app/src/components/common/RegionSelectorModal.tsx
 M econexao-app/src/components/map/MapAdapter.helpers.test.ts
 M econexao-app/src/components/map/MapAdapter.helpers.ts
 M econexao-app/src/components/map/MapAdapter.native.tsx
 M econexao-app/src/components/map/MapAdapter.types.ts
 M econexao-app/src/components/map/MapAdapter.web.tsx
 M econexao-app/src/components/profile/AccountDeletionModal.tsx
 M econexao-app/src/components/profile/AuthModal.tsx
 M econexao-app/src/components/profile/EditProfileModal.tsx
 M econexao-app/src/components/routes/CompactRouteCard.tsx
 M econexao-app/src/components/routes/OriginSelector.tsx
 M econexao-app/src/e2e/accessibilityAudit.e2e.test.tsx
 M econexao-app/tsconfig.json
?? docs/repository_health/
?? econexao-app/e2e/
?? econexao-app/playwright-report/
?? econexao-app/playwright.config.ts
?? econexao-app/screenshots/
?? econexao-app/scripts/serve-dist.mjs
?? econexao-app/src/components/common/AccessibleModal.native.tsx
?? econexao-app/src/components/common/AccessibleModal.tsx
?? econexao-app/src/components/common/AccessibleModal.web.tsx
?? econexao-app/src/utils/focusManager.dom.test.tsx
?? econexao-app/src/utils/focusManager.test.tsx
?? econexao-app/src/utils/focusManager.ts
?? econexao-app/test-results/
```

### Separação operacional

- **Trabalho local ativo:** todos os 23 arquivos modificados; os arquivos untracked de acessibilidade, E2E, configuração Playwright e servidor de `dist`; o pacote `docs/repository_health/`. Classificação preliminar `ACTIVE`; nada pode ser descartado com base neste inventário.
- **Saída regenerável:** `playwright-report/` e `test-results/` têm estrutura típica de output de Playwright; dependências instaladas e caches ignorados são outputs de ferramenta. Classificação preliminar `GENERATED`, mas remoção continua fora desta task.
- **Evidência potencial:** `screenshots/` e partes dos relatórios podem registrar aceite visual/acessível. Mesmo quando regeneráveis, precisam de seleção/proveniência antes de descarte; ficam `EVIDENCE` quando citadas e `GENERATED` somente quando não citadas.

## Configurações de projeto observadas

Somente os caminhos foram inventariados; `.env.example` não teve conteúdo lido.

| Área | Configurações/entrypoints | Classificação | Fonte normativa/consumidor conhecido | Risco e confirmação |
|---|---|---|---|---|
| Raiz | `.gitignore`, `requirements.txt`, `main.py`, `render.yaml`, `vercel.json`, `DEVELOPMENT.md`, `AGENTS.md` | `ACTIVE` para governança; wrappers/deploy também aparecem abaixo como `UNKNOWN` | AGENTS/spec/ADR 0005; ferramentas locais e plataformas podem consumir os wrappers | Não consolidar até mapear working directories de CI/Render/Vercel na ECO-2406 |
| Backend | `backend/pyproject.toml`, `backend/requirements.txt`, `backend/.env.example` | `ACTIVE` | spec §4.1/§4.2; Python/FastAPI e ambiente local | Preservar; conteúdo de ambiente não foi inspecionado |
| App | `econexao-app/package.json`, `package-lock.json`, `app.json`, `tsconfig.json`, `.gitignore`, `.env.example`, `playwright.config.ts`, `vercel.json` | `ACTIVE` | AGENTS e ADR 0001; npm/Expo/TypeScript/Playwright/Vercel | Lockfile/configs têm alterações locais; não editar |
| Supabase | `supabase/config.toml`, `supabase/migrations/` | `ACTIVE` | AGENTS/spec: migrations individuais são a única fonte normativa do schema | Não reconciliar schema nesta task |
| Landing page | `landing-page/package.json`, `package-lock.json` | `ACTIVE` | npm e build/deploy independente da landing page | Não acoplar ao app sem gate do owner |
| Docs | `docs/README.md`, ADRs, spec, contratos, critérios, finalization e repository_health | `ACTIVE` | precedência explícita em AGENTS/docs README | `docs/README.md` já estava modificado; preservar |

## Tamanhos relevantes

| Caminho/grupo | Arquivos | Bytes observados | Classificação | Observação |
|---|---:|---:|---|---|
| `econexao-app/node_modules/` | 34.381 | 345.605.139 | `GENERATED` | dependências instaladas; regeneração deve ser confirmada por lockfile/comando |
| `landing-page/node_modules/` | 33.369 | 262.574.315 | `GENERATED` | dependências instaladas; regeneração deve ser confirmada por lockfile/comando |
| `econexao-app/playwright-report/` | 3 | 584.920 | `GENERATED` | output E2E; pode conter parte citada como evidência |
| `econexao-app/screenshots/` | 14 | 4.704.334 | `EVIDENCE` | capturas locais não rastreadas; proveniência/aceite ainda precisam ser confirmados |
| `econexao-app/test-results/` | 3 | 35.742 | `GENERATED` | output E2E; contextos de erro podem ter valor diagnóstico transitório |
| `.git-history-backup/` | 44 | 599.619 | `UNKNOWN` | finalidade/recuperabilidade não demonstradas |
| `.coverage` | 1 | 69.632 | `GENERATED` | banco de cobertura local |
| `supabase/all_migrations_consolidated.sql` | 1 | 60.141 | `LEGACY_CANDIDATE` | não pode substituir migrations individuais |
| `elementos_interativos_telas.txt` | 1 | 15.499 | `DUPLICATE_CANDIDATE` | cópia raiz declarada não normativa |
| `stats_summary.txt` | 1 | 3.823 | `UNKNOWN` | origem, comando de geração e consumidor ainda não provados |

## Inventário preliminar por área

| Caminho/grupo | Estado Git | Classificação | Fonte normativa | Consumidor/evidência | Regeneração/proveniência | Risco | Confirmação necessária | Confiança |
|---|---|---|---|---|---|---|---|---|
| `AGENTS.md`, `docs/README.md`, spec, ADRs e contratos | tracked; `docs/README.md` modificado | `ACTIVE` | precedência declarada em AGENTS | agentes, implementação e revisão | autoria versionada | apagar/arquivar quebra governança | nenhuma remoção; ECO-2402 deve mapear status documental | alta |
| `main.py`, `requirements.txt`, `render.yaml`, `vercel.json` da raiz versus equivalentes do backend/app | tracked | `UNKNOWN` | ADR 0005, DEVELOPMENT e configs reais | possível consumo por deploy e ferramentas locais | proveniência via Git/configuração | remover wrapper pode quebrar deploy | provar working directory e consumidores em CI/Render/Vercel | média |
| `backend/app/`, `backend/tests/`, `backend/scripts/`, `backend/pyproject.toml` | tracked | `ACTIVE` | spec §4/AGENTS | FastAPI, testes e jobs | código versionado | impacto funcional e de dados | preservar; análise de legado só em task própria | alta |
| runtime/conector/scripts/testes OSRM | tracked | `LEGACY_CANDIDATE` | ADR 0013 substitui o provider runtime; prompt ECO-2405 separa runtime de dados | referências históricas/test/dev podem existir | Git e testes; não é regenerável por presunção | apagar importador, fixture ou dado histórico | provar cada consumidor; preservar geometrias importadas e FakeRoutingConnector legítimo | média-alta |
| `econexao-app/app/`, `src/`, configs e testes | tracked + alterações/untracked locais | `ACTIVE` | ADR 0001/spec/app atual | Expo, web, testes e trabalho ativo do usuário | código e lockfile | perda direta de trabalho local | preservar todas as 23 modificações e arquivos ativos untracked | alta |
| `econexao-app/playwright-report/`, `test-results/` | untracked | `GENERATED` | configuração Playwright/comandos E2E | ferramentas de teste; relatórios locais | estrutura típica de output; comando exato deve ser confirmado | descarte pode perder diagnóstico citado | cruzar referências em docs e reproduzir comando antes de qualquer remoção | alta para “gerado”, média para descartabilidade |
| `econexao-app/screenshots/` | untracked | `EVIDENCE` | relatório E2E/a11y modificado pode citá-las | revisão visual e aceite | captura Playwright presumida pelos nomes; metadados não bastam | remover pode apagar evidência formal | verificar citações, ambiente, data e seleção formal | média |
| caches, `.coverage`, `.venv`, `node_modules`, `dist` e caches de ferramenta ignorados | ignored/locais | `GENERATED` | configs de Python/npm/Expo/testes | runtimes e ferramentas locais | normalmente recriados por install/build/test; comando por grupo ainda precisa ser documentado | limpeza pode quebrar ambiente offline ou apagar diagnóstico | confirmar ignore, lockfiles e comando reprodutível na ECO-2404 | alta para caches/deps; média para `dist` |
| `supabase/migrations/`, `config.toml`, `seed.sql` quando presente | tracked | `ACTIVE` | AGENTS/spec: migrations individuais são fonte única | Supabase CLI, banco e testes | versionado; não regenerar por consolidação | perda de schema/policies/RLS | preservar integralmente | alta |
| `supabase/all_migrations_consolidated.sql` | tracked | `LEGACY_CANDIDATE` | regra normativa favorece migrations individuais | possível consumidor manual não provado | origem deve ser comparada às migrations | remoção prematura pode quebrar runbook oculto | busca em CI/docs/scripts + comparação semântica + owner na ECO-2405 | média-alta |
| `landing-page/` fonte, assets e configs | tracked | `ACTIVE` | configuração própria do projeto | build/deploy independente | lockfile e fonte versionados | acoplamento ou remoção quebra landing | preservar e mapear deploy na ECO-2406/2407 | alta |
| `docs/finalization/artifacts/` | tracked; um relatório modificado | `EVIDENCE` | finalization/audit e documentação de aceite | auditorias e handoff | evidência selecionada/versionada | arquivar/apagar perde prova | manter até matriz documental e revisão de referências | alta |
| `docs/archive/` | tracked | `EVIDENCE` | índice documental e histórico | rastreabilidade de decisões/tasks | Git + arquivo deliberado | confundir histórico com backlog ativo ou perder contexto | ECO-2402 classifica; ECO-2403 só move após aprovação | alta |
| `docs/repository_health/` preexistente nesta sessão | untracked | `ACTIVE` | prompt autorizado ECO-2401 e protocolo | coordenação ECO-24XX | trabalho local do usuário/da sessão | descartar perde autorização/plano | preservar; este inventário é o único acréscimo | alta |
| `elementos_interativos_telas.txt` da raiz | tracked | `DUPLICATE_CANDIDATE` | AGENTS/docs README dizem que `docs/` é canônico | consumidores desconhecidos; cópia raiz não normativa | origem histórica no Git | links/ferramentas antigas podem depender do caminho | busca de consumidores + confirmação do owner na ECO-2405 | alta para duplicidade normativa; média para remoção |
| `stats_summary.txt` | tracked | `UNKNOWN` | nenhuma fonte normativa identificada nesta task | consumidor não provado | comando/proveniência desconhecidos | classificar como lixo sem prova perde evidência | Git history, referências e comando de geração na ECO-2405 | média |
| `.git-history-backup/` | ignored/local | `UNKNOWN` | nenhuma | possível recuperação manual | 44 arquivos/599.619 bytes; origem não inspecionada | remover pode eliminar único backup local | owner deve explicar finalidade; avaliar recuperabilidade sem conteúdo sensível | baixa |

## Candidatos a remoção: evidência e gate

Nenhuma linha abaixo é autorização para remover.

| Candidato | Evidência disponível | Risco | Confirmação necessária | Confiança na candidatura |
|---|---|---|---|---|
| relatórios/resultados Playwright locais | caminhos untracked e estrutura de output | perder diagnóstico/evidência citada | provar comando de regeneração e ausência de citação; separar evidência selecionada | alta |
| dependências e caches ignorados | nomes convencionais, grande volume e regras de ferramentas | ambiente offline/execução local pode depender deles | lockfile + install/test reproduzível + política ECO-2404 | alta |
| screenshots locais | nomes de cenários E2E e relatório de a11y modificado | perder evidência visual | mapear referências, data/ambiente e seleção formal | média |
| cópia raiz de `elementos_interativos_telas.txt` | AGENTS declara `docs/` canônico e raiz não normativa | consumidor oculto/path legado | `rg`/configs/Git + owner | alta para candidatura, média para remoção |
| migration consolidada | conflito conceitual com fonte única de migrations individuais | runbook manual oculto e perda de comparação histórica | consumidores + equivalência + owner | média-alta |
| runtime OSRM | ADR 0013 e prompt ECO-2405 | apagar importador, fixtures ou geometrias válidas | separar provider runtime de dados históricos e fakes de teste | média-alta |
| `stats_summary.txt` | nome e localização sugerem relatório, mas não provam geração | possível evidência única | history/referências/comando | média-baixa |
| wrappers/configs duplicados de raiz/backend | arquivos homônimos/entrypoints em mais de uma área | quebra de deploy por working directory | CI/deploy/docs e smoke nos diretórios reais | média |
| `.git-history-backup/` | nome e metadados somente | perda de recuperação local | decisão do owner e inspeção sanitizada de proveniência | baixa |

## Comandos reproduzíveis

Executar a partir da raiz, em PowerShell, sem abrir `.env`:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git status --short --untracked-files=all
(git ls-files | Measure-Object -Line).Lines
(git ls-files --others --exclude-standard | Measure-Object -Line).Lines
(git ls-files --others --ignored --exclude-standard | Measure-Object -Line).Lines

$scopes = @('backend','econexao-app','supabase','landing-page','docs')
foreach ($scope in $scopes) {
  $tracked = (git ls-files -- $scope | Measure-Object -Line).Lines
  $untracked = (git ls-files --others --exclude-standard -- $scope | Measure-Object -Line).Lines
  "$scope tracked=$tracked untracked=$untracked"
}

$tracked = @(git -c core.quotepath=false ls-files)
$untracked = @(git -c core.quotepath=false ls-files --others --exclude-standard)
$excluded = @(
  'docs/repository_health/inventory_ECO-2401.md',
  'docs/repository_health/baseline_ECO-2401.sha256'
)
$paths = @($tracked + $untracked) |
  Where-Object {
    $_ -and
    $_ -notin $excluded -and
    $_ -notmatch '(^|[\\/])\.env[^\\/]*$' -and
    (Test-Path -LiteralPath $_ -PathType Leaf)
  } |
  Sort-Object -Unique
$paths | ForEach-Object {
  $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_).Hash.ToLowerInvariant()
  $normalized = $_ -replace '\\', '/'
  "$hash  $normalized"
}

git diff --name-only
git diff -- docs/repository_health/inventory_ECO-2401.md
git diff --no-index -- NUL docs/repository_health/inventory_ECO-2401.md
```

Para o arquivo novo, `git diff --no-index` retorna exit code 1 quando há diferenças; isso é esperado. A comparação da lista de 36 entradas acima com o status final comprova somente a estabilidade de nomes, estados Git e contagens: a única novidade de caminho permitida é este arquivo dentro do grupo já existente `docs/repository_health/`.

## Limitações e decisões pendentes

- O Git não conseguiu acessar o ignore global `C:\Users\Bruno\.config\git\ignore`; a classificação usa o ignore do repositório e o que pôde ser enumerado.
- Houve `Access denied` em `.pytest_cache/`, `backend/.pytest_cache/` e alguns diretórios `backend/.test-tmp/`; portanto 93.328 ignored é uma observação, não garantia de total exato.
- As contagens mudam se outro agente/processo editar o worktree; o verificador deve capturá-las atomicamente e explicar qualquer delta.
- O snapshot inicial registrou nomes, estados Git e contagens, mas não hashes dos 23 arquivos modificados nem dos 43 untracked. Portanto, a ausência de alteração de conteúdo durante a primeira escrita deste inventário não é comprovável retroativamente de forma independente. H24.1 e o status desta task permanecem `PARTIAL`; hashes capturados antes/depois de correções posteriores só protegem essas correções, não reconstituem a lacuna inicial.
- Nenhum conteúdo de `.env`, token, DSN, JWT, chave, remoto ou produção foi acessado ou registrado.
- Classificações são preliminares. H24.2 exige aprovação do owner para manter/arquivar/remover; H24.3 exige busca de consumidores e configurações reais.
- ECO-2402 não foi iniciada.

## Rollback documental

Como este arquivo é novo e untracked, rollback significa deixar de incluí-lo em uma futura entrega ou removê-lo apenas mediante autorização explícita do owner/coordenador. Nenhum arquivo preexistente precisa ser restaurado, pois não foi editado por esta implementação.
