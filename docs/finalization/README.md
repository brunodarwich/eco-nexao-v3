# ECOnexão — Programa de finalização

Baseline auditado em: 12/08/2026  
Escopo: finalizar, popular, homologar, publicar e operar o ECOnexão sem atualizar o Expo SDK 54.  
Estado global: **não pronto para staging nem production**.

## Leitura obrigatória

Antes de executar qualquer task ativa:

1. `AGENTS.md`.
2. `docs/README.md`.
3. `docs/backend_integration_spec.md`.
4. Este documento.
5. `docs/finalization/tasks.md`, no bloco completo da task escolhida.
6. `docs/ai_task_playbook.md`.
7. Referências indicadas pela task.

Aplicar a precedência normativa do `AGENTS.md`. O programa de finalização não
reescreve decisões aceitas; quando o escopo atual ultrapassa a spec 1.0, a task de
ADR precede a implementação.

## Documentos ativos

| Documento | Papel |
|---|---|
| `audit_report.md` | Confronto entre declaração, código, teste, execução e ambiente |
| `implementation_plan.md` | Marcos 13–22, caminho crítico, resultados e sequência |
| `tasks.md` | Tasks autocontidas para Codex, Antigravity ou owner |
| `dependency_graph.md` | Dependências, paralelismo, arquivos em conflito e revisão cruzada |
| `release_checklist.md` | Gates 1–8 e evidência de go/no-go |
| `ai_coordination.md` | Protocolo operacional entre agentes sem memória compartilhada |
| `ANTIGRAVITY_SUPERVISION.md` | Protocolo geral para supervisionar entregas do Antigravity |
| `ANTIGRAVITY_ECO2005_SUPERVISION.md` | Estudo de caso e checklist específico de ECO-2005 |
| `decisions_needed.md` | Decisões humanas e ADRs que bloqueiam implementação |

## Vocabulário de estado

Somente os estados abaixo podem ser usados:

| Estado | Significado operacional |
|---|---|
| `VERIFIED` | Aceite reproduzido no ambiente adequado, com comando, resultado e artefato |
| `PARTIAL` | Há implementação ou teste, mas parte do aceite/ambiente está ausente |
| `MISSING` | Capacidade ou evidência essencial não existe |
| `BLOCKED` | Depende de decisão, credencial, plataforma ou autorização ainda ausente |
| `NOT_VERIFIABLE` | A evidência não pôde ser reproduzida sem ação proibida ou ambiente indisponível |
| `SUPERSEDED` | Registro histórico substituído por fonte ativa, sem apagar a história |

`Há código`, `há teste unitário`, `foi testado contra ambiente real`, `pronto para
staging` e `pronto para production` são afirmações diferentes. Nenhuma implica a
seguinte automaticamente.

## Baseline resumido

- O repositório contém FastAPI, migrations, OpenAPI, cliente Expo tipado, TanStack
  Query, Auth anônima, telas públicas e testes locais de componentes/unidade.
- O ambiente remoto acessível contém PostgreSQL 17, PostGIS e 24 tabelas privadas,
  mas zero regiões, rotas, origens, atores, mídia e execuções de ingestão.
- Oito migrations locais/remotas estão alinhadas no Supabase test. As duas
  migrations de Storage foram promovidas somente nesse ambiente em 13/08/2026.
- Development e test estão separados e o gate confere project ref, banco e
  conectividade. Staging e production continuam adiados/bloqueados.
- `seed_pindobal.py --apply` persiste a fatia Pindobal de forma transacional e
  idempotente em test; associação PostGIS, painel/API editorial e homologação ainda
  estão pendentes.
- Não há `Dockerfile`, `eas.json`, package/bundle identifiers finais, pipeline de
  release, deploy, E2E real ou evidência Android/iOS/Web de homologação.
- A suíte frontend passou localmente (15 suítes/74 testes), assim como Ruff (0 erros) e mypy (45 arquivos, 0 erros).
  A suíte backend pytest executou 193/193 testes com sucesso (42,40s) e atingiu 88,92% de cobertura (limiar exigido: 85%).
- O diretório recebido não contém `.git`; portanto, status/diff/histórico e `git mv`
  não são verificáveis nesta cópia (Proveniência Git: BLOCKED).

## Atualização do progresso

Ao terminar uma task:

1. anexar comando exato, exit code, ambiente e resumo;
2. registrar migration/contrato/build/screenshot/log correspondente;
3. atualizar a linha pertinente do `audit_report.md` e o gate aplicável;
4. não editar checkboxes históricos arquivados;
5. marcar `VERIFIED` somente após reprodução no ambiente exigido;
6. fazer handoff no modelo definido em `ai_coordination.md`.

## Paradas obrigatórias adicionais

Além do `AGENTS.md`, parar quando `.env.test` não estiver isolado, quando uma task
editorial depender dos ADRs ECO-1302–ECO-1306, quando a ação atingir production ou
quando o diretório não for um worktree Git íntegro para trabalho paralelo.

## Referências Supabase revalidadas

- [Mudança de exposição explícita da Data API](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)
- [Controle de acesso do Storage](https://supabase.com/docs/guides/storage/security/access-control)
- [Anonymous Sign-Ins](https://supabase.com/docs/guides/auth/auth-anonymous)
- [Signed upload URLs](https://supabase.com/docs/reference/javascript/file-buckets-createsigneduploadurl)
- [Backups e PITR](https://supabase.com/docs/guides/platform/backups)
- [Security e Performance Advisors](https://supabase.com/docs/guides/database/database-advisors)
