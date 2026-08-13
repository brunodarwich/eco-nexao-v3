# Checklist de release e homologação

Data-base: **2026-08-12**. Nenhum gate é presumido por histórico, checkbox ou teste
parcial. Cada item exige estado, ambiente, artefato, comando/cenário, resultado,
evidência redigida, executor, revisor, data, risco e rollback. Produção e lojas exigem
autorização humana explícita.

Estados permitidos: `VERIFIED`, `PARTIAL`, `MISSING`, `BLOCKED`, `NOT_VERIFIABLE` e
`SUPERSEDED`, conforme `audit_report.md`. `PARTIAL` não libera o próximo gate.

## Pré-gate — Baseline e fundações verificáveis

**Estado em 2026-08-13: `BLOCKED`.** A cópia não contém `.git`; `.env.test` aponta
para um project ref inexistente e não conecta; a última leitura válida tinha cinco
migrations remotas contra sete locais. A correção local de Storage passou gates
estáticos, mas não a matriz remota. Suíte backend pytest (176/176 testes, 90,10%
de cobertura), Ruff e mypy passaram localmente.

**Pré-condições:** ECO-1301–1404 e ADRs ECO-1302–1306 aceitos.

- [ ] Worktree/commit íntegros e alterações do usuário conhecidas.
- [ ] Bootstrap Windows e Linux, Ruff, mypy, pytest/cobertura, OpenAPI, typecheck e Jest
      passam pelos scripts oficiais.
- [ ] Development/test/staging/production têm referências e credenciais separadas.
- [ ] Manifesto de migrations, grants, RLS e Storage passam matriz A/B/anônimo e
      advisors em test; restore/rollback foi ensaiado.
- [ ] Scanner de segredos/dependências não tem crítico/alto sem waiver.

**Comandos/cenários:** `git status`; scripts de bootstrap/quality de ECO-1301;
guardrail de isolamento antes de qualquer reset; testes Supabase positivos/negativos;
clone limpo por outro agente. **Evidência/responsáveis:** Codex executa, Antigravity
reproduz, owner fornece ambientes/ADRs. **Bloqueadores:** qualquer falha, colisão,
segredo, drift ou ADR aberto. **Rollback:** nenhuma promoção; descartar somente ambientes
locais/test autorizados e restaurar config/artefato versionado.

## Gate 1 — Conteúdo importável

**Estado em 2026-08-13: `PARTIAL` (conteúdo técnico `VERIFIED`).** ECO-1501 gravou atomicamente a fatia territorial
e provou rollback. ECO-1502 aplicou duas cargas autorizadas em test: 674 atores
estáveis, 0 criações/updates na segunda carga, 1661 inalterados e 53 candidatos por
execução. ECO-1503 persistiu bounds/hashes das três geometrias e 313 associações
PostGIS idempotentes. ECO-1504 confirmou JWT test → FastAPI → região/rota/3 origens/
313 atores/mapa e o cliente Expo passou typecheck, OpenAPI e 74 testes. O estado geral
permanece `PARTIAL`: a ECO-1505 gerou e verificou o pacote imutável, mas a aprovação
editorial humana continua pendente e explicitamente marcada como NO-GO.

**Pré-condições:** Pré-gate; ECO-1501–1505; test isolado; contrato Pindobal; fonte
`C:\Users\Bruno\Downloads\teste-rota` montada somente leitura.

- [x] Manifesto/hashes e dry-run são determinísticos.
- [x] `--apply` usa transação/rollback real e falha fechado sem sessão.
- [x] Upsert/proveniência/rejeições/contagens ficam persistidos e auditáveis.
- [x] OSRM, SEMTUR, snapshot Google e Place IDs obedecem contrato; nenhum ID é inventado.
- [x] PostGIS e associações ator–rota passam validações.
- [x] Duas execuções idênticas não duplicam e produzem reconciliação explicável.
- [x] Pacote técnico é imutável/verificável e exige aprovação separada por ambiente.

**Comandos:** suites unit/integration; pipeline oficial `--dry-run`; duas execuções
`--apply` apenas em test após guardrail; queries de contagem/hash/rejeição. **Cenários
manuais:** arquivo inválido, falha no meio da transação, fuzzy match pendente e promoção
bloqueada. **Evidência/responsáveis:** Codex implementa/executa; Antigravity revisa
relatórios; owner de dados aceita reconciliação. **Bloqueadores:** fonte alterada,
ambiente ambíguo, divergência de contagem ou rollback/idempotência falhos. **Rollback:**
rollback transacional/cleanup idempotente no test; nenhuma promotion.

## Gate 2 — Operação editorial segura

**Estado em 2026-08-12: `MISSING`.** Não existem API/painel administrativos, RBAC
editor/admin, state machine completa, upload editorial real ou audit/export operacional.

**Pré-condições:** Gate 1; ECO-1402/1403, ECO-1601–1605, ECO-1701–1704 e
ECO-1801–1804; ADR editorial/mídia aceito.

- [ ] Editor/admin e capabilities têm least privilege e testes A/B/anônimo.
- [ ] API CRUD cobre regiões, rotas, origens, geometrias, categorias, atores e vínculos.
- [ ] Rascunho→revisão→publicado→arquivado e publish guard impedem incompletos.
- [ ] Reconciliação/duplicatas, alertas, bulk import, export e jobs são idempotentes.
- [ ] Audit trail é íntegro; painel usa somente API, sem SQL/Supabase direto.
- [ ] Mídia valida MIME/bytes/limites, remove EXIF, deriva, exige alt/crédito/licença e
      resolve capa/galeria; órfãos/substituição/exclusão são reconciliados.
- [ ] Storage passa INSERT/SELECT/UPDATE/upsert/DELETE por owner/editor e nega cross-user.

**Comandos:** contratos/OpenAPI; suites repository/service/API; RLS/Storage positivos e
negativos; E2E editorial e export checksum. **Cenários manuais:** editor versus admin;
lock otimista; publicação incompleta; duplicata; mídia inválida; rollback de upload.
**Evidência/responsáveis:** Codex cobre API/segurança, Google Antigravity painel,
owner/editor homologa; revisão cruzada obrigatória. **Bloqueadores:** bypass de
autorização, audit mutável, publication guard ou Storage negativo falhos. **Rollback:**
despublicar por transição auditada, reverter artefato/config e reconciliar objeto/registro
com job aprovado.

## Gate 3 — App público funcional com dados reais de staging

**Estado em 2026-08-12: `MISSING`.** Há fluxos parciais, mas catálogo/detalhe fabricam
campos, mídia usa tokens sintéticos e auth/trips/offline/preferências estão incompletos.

**Pré-condições:** Gates 1–2; ECO-1901–1905; staging com dados Pindobal aprovados.

- [ ] OpenAPI/cliente não têm drift; nenhum mock/fallback/campo fabricado em runtime.
- [ ] Região, catálogo, detalhe, paginação e favoritos usam dados reais consistentes.
- [ ] Guest→conta, login/linking/conflito/refresh/deep link funcionam.
- [ ] Preferências/acessibilidade persistem e se aplicam; offline/retry são explícitos.
- [ ] Perfil/avatar, trips/visitas/complete/cancel, selos e contatos funcionam.
- [ ] Loading, vazio, erro, retry e rollback otimista acessível existem em cada consulta.
- [ ] App identity, package/bundle IDs, permissões, env profiles e UI legal aprovados.

**Comandos:** OpenAPI check, typecheck, Jest, contract/integration e build/smoke staging.
**Cenários manuais:** critérios de aceite P0 em Web/Android/iOS; A/B/anônimo; rede perdida
e retomada; deep link frio; erro de upload/mutation. **Evidência/responsáveis:** Codex
revisa contrato/backend; Antigravity implementa/homologa UI; owner aprova identidade e
legal. **Bloqueadores:** dado inventado, fluxo P0 ausente, segredo no cliente ou estado
sem retry/acessibilidade. **Rollback:** artefato/flag aprovados e limpeza apenas de
fixtures; reabrir task dona.

## Gate 4 — Infraestrutura de staging

**Estado em 2026-08-12: `MISSING`.** Não há Dockerfile, `eas.json`, pipeline de release,
deploy/domain staging ou observabilidade integrados comprovados.

**Pré-condições:** Gate 3; ECO-2001–2004; provedor, domínio e orçamento decididos.

- [ ] Imagem imutável non-root, startup/readiness/shutdown e SBOM/scans passam.
- [ ] CI gera artefato; migration gate, approvals, smoke e rollback bloqueiam falha.
- [ ] HTTPS, CORS exato, domínio Web/API e deep links staging funcionam.
- [ ] Builds mobile staging são instaláveis e identificáveis.
- [ ] Logs/traces/métricas redigem PII/tokens/URLs; SLOs/alertas/rate limits/cost guards
      e runbooks são acionáveis.

**Comandos:** build/test/scan de imagem; workflow staging; smoke HTTPS/CORS; falhas
sintéticas 5xx/timeout/rate limit; rollback; comandos EAS oficiais. **Cenários manuais:**
deploy falho bloqueado, digest anterior restaurado, alerta recebido, origem proibida e
conector degradado. **Evidência/responsáveis:** Codex plataforma; Antigravity smoke UI;
owner fornece contas/secrets. **Bloqueadores:** produção habilitada, wildcard CORS,
segredo em log, alerta/rollback ausente. **Rollback:** redeploy do digest anterior,
pausa de job/conector e restauração de config versionada.

## Gate 5 — Homologação Android/iOS/Web

**Estado em 2026-08-12: `MISSING`.** Não foram encontrados E2E real, evidência em
dispositivos, TalkBack/VoiceOver, teclado ou auditoria WCAG automatizada.

**Pré-condições:** Gate 4; ECO-2101–2103; matriz de browser/dispositivos aprovada.

- [ ] Web, Android mínimo/atual e iOS mínimo/atual passam jornadas críticas duas vezes.
- [ ] Loading/vazio/erro/retry, rede degradada, deep/universal links e cold start passam.
- [ ] Teclado, TalkBack, VoiceOver, Dynamic Type e reduce motion são aprovados.
- [ ] Zero violação crítica/serious sem waiver; nenhum P0/P1 aberto.

**Comandos:** `npm run e2e:web`, `npm run a11y:web`, `npm run e2e:android` e
`npm run e2e:ios`, ou equivalentes documentados. **Cenários manuais:** foco após modal/
erro, zoom/fonte, leitor de tela, perda/retorno de rede e links com app aberto/fechado.
**Evidência/responsáveis:** Antigravity executa mídia redigida; Codex revisa reports;
owner fornece dispositivos/contas. **Bloqueadores:** barreira crítica, crash, P0/P1 ou
cenário P0 sem cobertura. **Rollback:** bloquear promoção, revogar build de teste e
reabrir task funcional.

## Gate 6 — Segurança, LGPD e backups

**Estado em 2026-08-12: `BLOCKED`.** Não há termos/política LGPD do produto, aceite
jurídico, DAST/load/restore completo, revisão Google/licenças ou scanner comprovado.

**Pré-condições:** Gate 5; ECO-2104; segurança, conteúdo, DPO/jurídico e owner nomeados.

- [ ] SAST/SCA/secret scan, DAST seguro, SBOM e authorization matrix aprovados.
- [ ] Load smoke atende SLO/orçamento sem Google real em teste.
- [ ] Backup, PITR, restore e rollback foram ensaiados e cronometrados; objetos Storage
      têm estratégia separada do backup do banco.
- [ ] Privacidade, termos, consentimento, retenção, exclusão/exportação e disclosures
      têm aceite humano.
- [ ] Conteúdo, licenças/créditos/atribuições e políticas Google estão aprovados.
- [ ] Exceções têm risco, compensação, owner e validade.

**Comandos:** scanners e suites de segurança aprovados; load smoke; restore rehearsal;
SBOM/licenças. Sem pentest invasivo sem autorização separada. **Cenários manuais:** abuso/
rate limit, exclusão/exportação, incidente/restore e conteúdo despublicado. **Evidência/
responsáveis:** Codex técnico; Antigravity regressão; DPO/jurídico/owner assinam.
**Bloqueadores:** segredo, crítico/alto sem waiver, restore falho ou aceite legal ausente.
**Rollback:** NO-GO, revogar artefato/credencial e executar runbook; nenhuma promoção.

## Gate 7 — Produção

**Estado em 2026-08-12: `BLOCKED`.** Depende de todos os gates anteriores, manifesto
imutável, acesso e autorização. Nenhuma escrita/deploy de produção ocorreu na auditoria.

**Pré-condições:** Gates 1–6 `VERIFIED`; ECO-2201=GO; janela, backups, comunicação,
observadores e abort thresholds aprovados.

- [ ] SHA/digests/migrations conferem com manifesto; target é verificado antes de write.
- [ ] Migrations e Pindobal terminam com advisors/reconciliação aprovados.
- [ ] API/Web exatos são promovidos; HTTPS/CORS/health/jornadas mínimas passam.
- [ ] Rollout gradual, SLOs, alertas e rollback estão ativos; nenhum P0/P1 aberto.

**Comandos:** somente runbooks ECO-2202/2203 já ensaiados, outputs redigidos; smoke
sintético e comparação de digest/build. **Cenários manuais:** conta sintética, login,
catálogo/favorito/rota/viagem e rollback. **Evidência/responsáveis:** owner dá GO e
controla janela; Codex executa/revisa; Antigravity smoke. **Bloqueadores:** divergência
de target/artefato, migration/contagem/SLO falhos. **Rollback:** abortar no limiar,
reverter tráfego/artefato e seguir restore aprovado; nunca improvisar SQL destrutivo.

## Gate 8 — Publicação nas lojas e operação assistida

**Estado em 2026-08-12: `MISSING`.** Só começa após produção estável, contas de lojas,
builds homologados e aprovação humana.

**Pré-condições:** Gate 7; ECO-2204–2205; manifesto mobile, listings/disclosures,
política de rollout, on-call, suporte e janela assistida aprovados.

- [ ] Builds Android/iOS exatos são aceitos; instalação, upgrade e links passam.
- [ ] Rollout gradual pode ser pausado e cada store/channel/version está registrado.
- [ ] Durante 24–72 h ou período aprovado, disponibilidade/erro/latência/custo, Auth,
      dados, Storage e ingestão permanecem dentro dos limites.
- [ ] Alertas têm owner; suporte/ops/DPO receberam handoff; nenhum P0/P1 está aberto.
- [ ] Backlog residual tem severidade/owner/prazo e aceite final é assinado.

**Comandos:** submissão/consulta oficial das lojas sem expor certificados; smoke de
install/upgrade; consultas read-only de health/build/dashboards; sintéticos agendados.
**Cenários manuais:** review rejeitada, pausa de rollout, upgrade, deep link, alerta,
suporte e passagem de plantão. **Evidência/responsáveis:** owner publica/assina;
Antigravity verifica apps; Codex/ops monitoram. **Bloqueadores:** review/metadata,
P0/P1, SLO violado, alerta sem owner ou handoff incompleto. **Rollback:** pausar/revogar
rollout conforme plataforma, reverter serviço e reabrir Gate 7 quando necessário.

## Quadro de decisão

| Etapa | Estado inicial | Responsável por fechar | Evidência/decisão |
|---|---|---|---|
| Pré-gate | BLOCKED | Codex + Antigravity + owners | _pendente_ |
| Gate 1 | MISSING | Codex + owner de dados | _pendente_ |
| Gate 2 | MISSING | Codex + Antigravity + owner editorial | _pendente_ |
| Gate 3 | MISSING | Antigravity + Codex | _pendente_ |
| Gate 4 | MISSING | Codex + owner de plataforma | _pendente_ |
| Gate 5 | MISSING | Antigravity + Codex | _pendente_ |
| Gate 6 | BLOCKED | Segurança + DPO/jurídico + owner | _pendente_ |
| Gate 7 | BLOCKED | Owner | _pendente_ |
| Gate 8 | MISSING | Owner + ops | _pendente_ |

O produto só está finalizado quando o pré-gate e os oito gates estiverem `VERIFIED` e
o aceite do Gate 8 estiver assinado.
