# ECOnexão — Programa de higiene e saúde do repositório

Status: referência histórica. O estado individual e a prioridade das ECO-2401–2410
estão exclusivamente em [project_status.md](../project_status.md). O antigo resumo
de conclusão da baseline não substitui sua reconciliação atual.

Owner de ativação: proprietário do produto

Fonte normativa superior: `../README.md`

Fonte ativa de estado e backlog: [`../project_status.md`](../project_status.md).
`tasks.md` preserva a sequência histórica do programa de higiene.

## Objetivo

Reduzir ambiguidade documental, artefatos transitórios, legado técnico e duplicação
sem comprometer o aplicativo, apagar evidências ou antecipar decisões do owner.

Este pacote define as tasks `ECO-2401` a `ECO-2410`. Cada sessão executa somente uma
task desbloqueada por meio do prompt correspondente em `prompts/`.

## Regra de ativação

O pacote é apenas uma proposta até o owner autorizar `ECO-2401`. Uma task concluída
não autoriza automaticamente ações remotas, produção, exclusão material ou a task
seguinte.

## Arquivos

- `plan.md`: sequência, gates e estratégia de rollback.
- `tasks.md`: backlog e critérios de conclusão.
- `session_protocol.md`: contrato comum de execução e subagentes.
- `prompts/`: um prompt autocontido para cada sessão Codex.

## Resultado esperado

- uma fonte única e atual do estado do projeto;
- documentação histórica preservada e explicitamente arquivada;
- artefatos gerados fora do Git, salvo evidência selecionada;
- legado removido somente após prova de ausência de consumidores;
- deploy e assets com origem canônica definida;
- checks automáticos que impeçam a regressão da higiene.
