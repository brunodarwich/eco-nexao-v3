# ECOnexão — Índice da documentação

Este diretório é a entrada canônica para produto, arquitetura, dados, execução e testes.

## Comece aqui

| Documento | Finalidade |
|---|---|
| `../AGENTS.md` | Regras obrigatórias para agentes |
| `backend_integration_spec.md` | Arquitetura e comportamento final |
| `finalization/README.md` | Entrada do programa ativo de finalização |
| `finalization/audit_report.md` | Estado real auditado e evidências |
| `finalization/implementation_plan.md` | Marcos, caminho crítico e estratégia de entrega |
| `finalization/tasks.md` | Backlog ativo `ECO-13xx` a `ECO-22xx` |
| `backend_integration_tasks.md` | Índice do backlog histórico arquivado e sucessor ativo |
| `ai_task_playbook.md` | Como uma IA executa e entrega cada task |
| `../DEVELOPMENT.md` | Setup e comandos locais/remotos |
| `acceptance_criteria.md` | Cenários ponta a ponta por tela |
| `testing_strategy.md` | Pirâmide, ambientes, fixtures e comandos |
| `backend_integration_progress.md` | Índice do progresso histórico arquivado |
| `data/pindobal_data_contract.md` | Contrato de importação da primeira rota |

## Decisões arquiteturais

| ADR | Decisão |
|---|---|
| `adr/0001-expo-version.md` | Manter SDK 54 durante a integração |
| `adr/0002-supabase-platform.md` | Supabase gerenciado sem Docker obrigatório |
| `adr/0003-map-platforms.md` | Abstração de mapa nativo + web |
| `adr/0004-product-decisions.md` | Auth anônima, plataformas e infraestrutura em nível ainda genérico |
| `adr/0005-provedor-fastapi.md` | Provedor FastAPI no Google Cloud Run (southamerica-east1) |
| `adr/0006-operacao-editorial-rbac.md` | Operação editorial, RBAC, state machine, Publish Guard e audit trail |
| `adr/0007-identidade-sessao-linking.md` | Identidade, sessão guest, account linking, expurgo 90d e localStorage Web |
| `adr/0008-politica-de-midia-e-privacidade.md` | Buckets híbridos Storage, EXIF strip, WebP, proxy Google Photos e alt text |
| `adr/0009-remocao-impacto-ecologico-pessoal.md` | Remove impacto/selos pessoais e preserva selos editoriais territoriais |
| `adr/0013-google-routes-como-provedor-de-roteamento.md` | Google Routes API Essentials substitui OSRM no Gate H3 revisado |

## Programa de finalização

- `finalization/dependency_graph.md`: dependências, paralelismo e conflitos.
- `finalization/release_checklist.md`: gates objetivos até produção e lojas.
- `finalization/ai_coordination.md`: protocolo Codex × Google Antigravity.
- `finalization/decisions_needed.md`: decisões exclusivas do proprietário.
- `archive/planning/2026-08-12/`: backlog e progresso históricos preservados.

## Iniciativa de mapa dinâmico

- `mapa_dinamico/README.md`: entrada única para a evolução de categorias, pins,
  camadas territoriais e origens dinâmicas.
- `mapa_dinamico/plano_implementacao.md`: sequência proposta ECO-2301 a
  ECO-2315, dependências, gates humanos e critérios de encerramento.
- `mapa_dinamico/tasks.md`: registro das tasks propostas e condição de ativação.
- `mapa_dinamico/prompts/`: um prompt executável por sessão, sempre uma task por
  vez e com orquestração obrigatória de subagentes.

## Design e inventário

- `elementos_interativos_telas.txt`: inventário canônico do estado atual.
- `design-specs/DESIGN.md`: linguagem visual global.
- `stitch-screens/*/DESIGN.md`: referência visual por tela.

O arquivo `../elementos_interativos_telas.txt` é uma cópia legada e não deve ser atualizado nem usado por agentes. Remoção/arquivamento depende de confirmação do proprietário.

## Precedência

ADR aceito → spec → OpenAPI → contrato de dados → critérios de aceite → tasks → inventário atual → design → mocks/código legado.

## Atualização obrigatória

- Mudança arquitetural: criar/alterar ADR e spec.
- Mudança HTTP: alterar OpenAPI e tipos gerados.
- Mudança de origem/normalização: alterar contrato Pindobal e fixtures.
- Mudança de interação: alterar critérios de aceite e inventário quando necessário.
- Novo comando: atualizar `DEVELOPMENT.md` e `AGENTS.md`.
