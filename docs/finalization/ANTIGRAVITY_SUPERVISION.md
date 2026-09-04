# Supervisão Codex × Google Antigravity

Guia operacional para o Codex revisar qualquer entrega do Google Antigravity no
ECOnexão. O Antigravity pode executar tarefas; Codex deve verificar evidências,
contratos, segurança e limites de autorização de forma independente.

## Regra de operação

- Uma task, um worktree, uma branch e um executor até o handoff.
- O relato do Antigravity é uma pista, não evidência final. Reproduza comandos e leia
  o diff antes de aprovar.
- Não faça merge, push, fechamento de PR, deploy, acesso remoto, alteração de schema,
  exclusão de dados ou uso de credenciais sem autorização explícita do owner.
- Preserve alterações existentes do usuário e não faça refactors oportunistas.
- Toda nova falha de processo encontrada deve ser adicionada à seção **Lições vivas**
  deste arquivo com: situação, risco, prevenção e teste/evidência exigida.

## Roteiro do Codex para toda revisão

1. Ler `AGENTS.md`, `docs/README.md`, a task ativa, `docs/ai_task_playbook.md` e os
   ADRs/contratos diretamente aplicáveis.
2. Identificar branch, worktree, commit-base, commit entregue, arquivos reservados e
   alterações alheias com Git somente leitura.
3. Comparar o diff com o objetivo e com a fonte normativa; verificar que mocks,
   documentação e código de produção dizem a mesma coisa.
4. Reproduzir os testes relevantes e os testes negativos. Executar checks de formato,
   tipos, segredos e status em proporção ao risco.
5. Para mudanças remotas, separar: implementação local, preflight read-only, ação de
   escrita e validação posterior. Cada etapa exige autorização própria quando aplicável.
6. Entregar `APPROVE`, `CHANGES_REQUIRED`, `BLOCKED` ou `NOT_VERIFIABLE`, sempre com
   evidência, riscos e próximo prompt do Antigravity.

## Instruções por capacidade do Antigravity

| Capacidade | Uso adequado | Supervisão e limites |
|---|---|---|
| Git, branches, worktrees e PRs | criar worktree limpo a partir da base indicada; commits pequenos; push de alterações autorizadas | conferir baseline, branch alvo, diff e CI; não inferir autorização para abrir/mesclar/fechar PR; nunca reset/checkout destrutivo |
| Implementação backend/frontend | implementar somente a task e contratos declarados; manter camadas e tipos | revisar caminho real e tipos de retorno; não aceitar `Any`, casts ou ignores como correção sem justificativa; evitar refactor fora do escopo |
| Testes, qualidade e CI | executar testes relevantes, lint, typecheck e scan de segredos | reproduzir pelo menos o caminho de maior risco; conferir exit codes e não aceitar “passou” sem saída; teste mockado deve respeitar contrato real |
| Supabase, migrations e dados | validar localmente; usar migration versionada; executar preflight somente quando autorizado | nunca expor secrets; sem production; não usar Dashboard para mudar schema; verificar RLS/grants/advisors/lista de migrations no ambiente correto |
| APIs, Auth e segurança | atualizar contratos e testes positivos/negativos | verificar 401/403/ownership/validação e não confiar em UI para autorização; revisar ameaça e rollback |
| Documentação e runbooks | registrar comandos, evidências, riscos, estados e rollback reais | não transformar plano em fato; declaração de ambiente remoto só vale com evidência sanitizada e reproduzível |
| Browser, MCP, CLI e automação | browser para smoke visual autorizado; CLI para evidência; MCP quando oferece a mesma auditoria | não contornar gates por MCP/browser; não automatizar mutação remota; screenshots/logs não podem expor PII ou segredos |
| Subagentes e skills | dividir leitura/auditoria independente; usar skill aplicável antes de agir | agente principal integra; reservar arquivos; não delegar aprovação final ou ação remota; cada subagente deve entregar evidência verificável |

## Antipadrões que exigem correção imediata

1. Assumir target, ambiente, permissões ou aprovação humana por fallback.
2. Declarar sucesso baseado apenas em teste mockado, sem conferir o contrato de produção.
3. Esconder falha de tipo/contrato com `type: ignore`, `cast` ou `Any` não justificado.
4. Afirmar que migração, advisor, auditoria, RLS, deploy ou escrita remota foi validado
   sem comando, ambiente, exit code e resultado correspondentes.
5. Executar ação remota porque o código está pronto, porque há credencial disponível ou
   porque uma confirmação de terminal foi digitada.
6. Misturar planejamento, implementação, preflight e apply na mesma autorização.
7. Fazer alterações amplas, apagar arquivos, resolver conflitos automaticamente ou
   modificar `.env`/secrets fora do escopo.
8. Declarar “zero segredos”, “árvore limpa” ou “todos os testes” sem limitar o escopo
   da afirmação e sem prova reproduzível.

## Lições vivas

| Data | Situação | Prevenção obrigatória |
|---|---|---|
| 03/09/2026 | O runner ECO-2005 tratou um `dict` real como dataclass porque o mock retornava outra forma. | Testar o contrato de retorno real entre produtor e consumidor; MyPy completo antes do push. |
| 03/09/2026 | Guardas por somatório aceitaram estados híbridos de carga. | Para operações sensíveis, validar perfis completos e mutuamente exclusivos; testar combinações inválidas. |
| 03/09/2026 | Proteção de CLI não cobria chamada programática. | Aplicar fail-closed também nas APIs/funções invocáveis, antes de abrir conexão ou transação. |
| 03/09/2026 | Runbook poderia prometer verificações remotas/auditoria ainda não implementadas. | Documentar somente evidência existente; pendências remotas ficam explicitamente `BLOCKED`. |
| 03/09/2026 | Idempotência de domínio e histórico append-only podem parecer contraditórios. | Declarar a fronteira de idempotência e testar separadamente entidades de domínio e ledger de auditoria. |
| 03/09/2026 | A supervisão procurou `ECO-2005` na branch principal desatualizada, embora a task já existisse no commit-base do PR em `origin/staging`. | Validar a fonte normativa na branch-base e no worktree exatos da entrega; registrar ref e SHA usados em toda busca documental. |
| 03/09/2026 | A supervisão declarou incorretamente que uma seção da spec não existia sem conferir o índice integral da revisão normativa correta. | Antes de apontar referência inválida, listar os cabeçalhos do documento no commit-base da entrega e citar a revisão consultada. |
| 03/09/2026 | Foram tentadas duas estratégias mutáveis de merge em sequência, mas o handoff registrou apenas a estratégia que concluiu. | Para toda tentativa mutável, registrar comando, exit code e mensagem sanitizada; após qualquer sucesso, interromper novas tentativas e confirmar o objeto Git resultante. |
| 03/09/2026 | Um preflight chamou de “zero schema drift” o simples alinhamento do histórico de migrations. | Separar migration-history alignment de comparação real do schema; cada conclusão exige comando, exit code e saída sanitizada próprios. |
| 03/09/2026 | Ausência de findings em advisors foi usada como prova completa de RLS/grants, e estatísticas estimadas foram tratadas como contagens exatas. | Advisors são sinal complementar: provar RLS/grants com testes positivos/negativos e obter contagens exatas por queries contratuais antes de autorizar carga. |
| 03/09/2026 | Um relatório de `migration list` acrescentou nomes que não correspondiam aos arquivos versionados, embora os timestamps estivessem alinhados. | Não enriquecer saída remota por memória ou inferência; associar versões a nomes diretamente de `supabase/migrations` e executar comparação automática antes do handoff. |
| 03/09/2026 | Um preflight com `SELECT count(*)` declarou “zero aquisição de locks”, embora consultas PostgreSQL adquiram locks de leitura. | Descrever precisamente “nenhum advisory lock nem lock de escrita”; quando relevante, diferenciar `AccessShareLock` transitório de bloqueios mutáveis/exclusivos. |
| 03/09/2026 | Testes baseados em `AsyncMock` foram apresentados como prova da lógica transacional real do PostgreSQL. | Classificar mocks como testes unitários de orquestração; exigir PostgreSQL real isolado para provar advisory lock, commit, rollback e constraints. |
| 03/09/2026 | Rollback lógico foi tratado como disponível sem script executável, enquanto PITR estava desabilitado e não havia backup listado. | Antes de qualquer escrita, exigir mecanismo pós-commit existente, testado e autorizado; documentação de intenção não substitui artefato nem restore comprovado. |
| 03/09/2026 | A supervisão transformou um PostgreSQL test adicional e Docker em bloqueadores para uma carga controlada em staging vazio, apesar de Docker não ser pré-requisito e já existirem testes, guards e preflight proporcionais. | Distinguir proteção essencial de defesa redundante: para staging descartável/vazio, permitir homologação controlada com State Guard, transação, contagens e autorização explícita; reservar infraestrutura extra para risco que ela realmente reduz. |
| 03/09/2026 | O runner de ingestão falhou antes do CLI porque importar models carregou `app.db.__init__`, a engine global e toda a configuração da API, exigindo chave pública e provider de rotas sem relação com a carga. | CLIs operacionais devem importar apenas base/models sem inicializar runtime global; testar o entrypoint em subprocesso com somente as variáveis documentadas. |
| 03/09/2026 | O validador normalizou `DATABASE_URL` para psycopg, mas o runner criou sua engine com o valor bruto e tentou carregar `psycopg2`. | Normalizar o DSN uma única vez no boundary do CLI e usar exatamente o valor validado; cobrir o entrypoint com URI `postgresql://` em subprocesso. |
| 03/09/2026 | O entrypoint assíncrono foi aprovado sem execução no Windows e falhou porque psycopg não suporta o `ProactorEventLoop` nesse modo. | Testar o CLI real no sistema operacional operacional e selecionar explicitamente `WindowsSelectorEventLoopPolicy` antes de `asyncio.run` quando aplicável. |
| 03/09/2026 | O State Guard codificou perfil inicial `924/737` com mocks, mas o produtor real classificou `674 created` e `987 unchanged` conforme seus três fluxos de entrada. | Derivar invariantes do retorno real do repositório e de uma execução transacional abortada controladamente; testes devem chamar o produtor real, não injetar o próprio perfil esperado. |
| 03/09/2026 | Após corrigir as contagens, o runbook atribuiu os 674 criados a “SEMTUR e recorte”, embora somente SEMTUR crie atores e o recorte componha os inalterados/raw. | Para cada métrica operacional, rastrear no código qual fluxo incrementa o contador e revisar também a descrição semântica, não apenas os números. |
| 03/09/2026 | Ao faltar um DSN, o operador vasculhou `.env`, keyring, traces e transcrições internas e sugeriu que o owner informasse a senha. | Verificar apenas presença/target sanitizado; o owner injeta o DSN completo por entrada oculta ou secret store, nunca por chat, log ou argumento com senha. |
| 03/09/2026 | Um worktree foi colocado em detached HEAD por `checkout --detach`, mas o handoff declarou ausência de operação Git mutável. | Registrar toda mudança de estado do worktree; para execução imutável, confirmar o SHA atual e só destacar HEAD quando isso estiver previsto e autorizado. |

## Handoff mínimo do Antigravity

```text
Task:
Executor / branch / worktree:
Commit-base e commit entregue:
Objetivo observável atendido:
Arquivos alterados:
Contratos, migrations ou dados afetados:
Comandos, exit codes e ambiente:
Testes negativos e evidências:
Riscos, limitações e rollback:
Ações remotas realizadas: nenhuma / listar autorização e evidência
Próxima ação que depende do owner:
```

## Estudos de caso

- `ANTIGRAVITY_ECO2005_SUPERVISION.md`: aplicação deste protocolo à promoção Pindobal.
