# Backlog proposto — ECO-2401 a ECO-2410

> **Referência histórica de manutenção.** Estado, dependências atuais e prioridade
> de todas as tarefas estão em [project_status.md](../project_status.md).
> Este arquivo preserva os aceites originais; não mantém uma fila concorrente.

| Task | Resultado | Depende de | Gate de conclusão |
|---|---|---|---|
| ECO-2401 | Baseline protegida e inventário rastreável | autorização do owner | H24.1 verificado; nenhuma alteração perdida |
| ECO-2402 | Fonte única de status e backlog aberto | ECO-2401 | contradições identificadas; status atual aprovado |
| ECO-2403 | Planos concluídos arquivados com índices | ECO-2402, H24.2 | links válidos; histórico preservado |
| ECO-2404 | Política de artefatos gerados e evidências | ECO-2401 | outputs regeneráveis ignorados; evidências selecionadas mantidas |
| ECO-2405 | Legado OSRM/runtime e arquivos órfãos tratados | ECO-2402, H24.2, H24.3 | nenhum consumidor; regressão verde; snapshots preservados |
| ECO-2406 | Configuração de deploy e wrappers redundantes consolidados | ECO-2402, H24.2 | Render/Vercel/CI coerentes e smoke aplicável verde |
| ECO-2407 | Assets duplicados governados por origem e checksum | ECO-2402, H24.2 | builds independentes preservados; nenhuma imagem quebrada |
| ECO-2408 | Checks automáticos de saúde implementados | ECO-2403–ECO-2407 aplicáveis | comando único local e CI sem falsos positivos críticos |
| ECO-2409 | Fronteiras arquiteturais protegidas por testes | ECO-2408 | violações intencionais falham; suíte normal passa |
| ECO-2410 | Auditoria final e handoff de manutenção | ECO-2401–ECO-2409 | verificação independente e backlog residual explícito |

Nenhuma task altera produção. Remoção material exige a matriz aprovada na ECO-2402.
