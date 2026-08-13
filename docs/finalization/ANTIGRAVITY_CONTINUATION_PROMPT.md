# Prompt de continuidade para o Google Antigravity

Continue o desenvolvimento do ECOnexão a partir do estado real do repositório, mas **nesta primeira etapa apenas investigue e crie um plano de implementação para minha aprovação**. Não altere código, dependências, migrations, ambientes remotos ou dados antes da aprovação explícita do plano.

## Contexto já conhecido

- A fonte ativa de planejamento é `docs/finalization/`; o backlog `ECO-0001–ECO-1205` e seu progresso são históricos arquivados.
- O estado global documentado é: **não pronto para staging nem production**.
- O código já contém FastAPI, migrations Supabase, OpenAPI, cliente Expo tipado, TanStack Query, Auth anônima, telas públicas e testes locais.
- O baseline auditado registra frontend com 15 suítes/74 testes, backend com 170/170 testes, cobertura de 90,10%, Ruff e mypy sem erros; reproduza o que for seguro e trate esses números como alegações até confirmar no ambiente atual.
- O banco remoto anteriormente inspecionado tinha PostgreSQL 17/PostGIS e 24 tabelas privadas, mas estava sem regiões, rotas, origens, atores, mídia ou execuções de ingestão.
- A migration local de Storage ainda não estava promovida; buckets/policies não existiam no remoto verificado.
- `seed_pindobal.py --apply` não persiste; avatar/signed upload são stubs; API/painel editorial ainda não existem.
- ADR 0005 (Cloud Run em `southamerica-east1`) e ADR 0006 (RBAC/workflow editorial) estão aceitos.
- ECO-1304, ECO-1305 e ECO-1306 continuam dependentes de decisão do proprietário.
- A cópia auditada não contém `.git`. Isso bloqueia comprovação de status/diff/histórico e **bloqueia trabalho paralelo com escrita** até restaurar um worktree íntegro.
- Próximo ponto de entrada esperado: **ECO-1301 — Restabelecer baseline verificável**. Não pule para tasks posteriores sem satisfazer dependências e gates.

## Leitura obrigatória, nesta ordem

1. `AGENTS.md` da raiz e qualquer `AGENTS.md` aplicável ao diretório trabalhado.
2. `docs/README.md`.
3. `docs/backend_integration_spec.md`.
4. `docs/finalization/README.md`.
5. `docs/finalization/audit_report.md`.
6. `docs/finalization/implementation_plan.md`.
7. `docs/finalization/tasks.md`, especialmente o bloco completo de ECO-1301 e as dependências imediatas.
8. `docs/finalization/dependency_graph.md`.
9. `docs/finalization/decisions_needed.md`.
10. `docs/finalization/ai_coordination.md`.
11. `docs/finalization/release_checklist.md`.
12. `docs/ai_task_playbook.md` e referências específicas da task escolhida.

Respeite a precedência normativa definida em `AGENTS.md`. Não use a cópia de `elementos_interativos_telas.txt` da raiz como fonte de verdade. Não implemente decisão aberta.

## Orquestração obrigatória com subagentes

Crie subagentes para melhorar investigação, planejamento, revisão e consolidação. Enquanto não houver worktree Git íntegro, limite-os a tarefas **somente leitura**, sem edições concorrentes. Sugestão de divisão:

1. **Subagente de baseline e repositório:** localizar a raiz Git real ou comprovar sua ausência; inspecionar estrutura, scripts, runtimes e comandos de qualidade; não imprimir valores de `.env`.
2. **Subagente de backlog e dependências:** confrontar audit, tasks, grafo, gates e ADRs; indicar a primeira task executável e tudo que a bloqueia.
3. **Subagente de validação técnica:** revisar evidências de testes, OpenAPI, frontend, backend e Supabase; propor somente comandos read-only/locais seguros para reproduzir o baseline.
4. **Agente principal:** cruzar os três relatórios, resolver divergências pelas fontes normativas e produzir um único plano para aprovação.

Não deixe subagentes editarem os mesmos arquivos. Depois que o Git for restaurado e o plano aprovado, use branch/worktree por agente, declare arquivos reservados e aplique a matriz de conflitos de `dependency_graph.md`. Toda entrega de subagente deve seguir o handoff de `ai_coordination.md`.

## O que fazer agora

1. Inspecione o estado atual sem modificar arquivos.
2. Confirme se existe `.git` em algum nível válido e identifique o commit-base; se não existir, classifique ECO-1301 como bloqueada e proponha opções seguras para restaurar/obter o clone íntegro, sem apagar ou sobrescrever esta cópia.
3. Verifique quais ADRs e decisões humanas estão aceitos, pendentes ou inconsistentes.
4. Reproduza apenas verificações locais, read-only ou não destrutivas que sejam necessárias para validar o diagnóstico. Não acesse production. Não aplique migrations. Não use credenciais ou segredos em saídas.
5. Identifique a **única próxima task ativa** segundo dependências, prioridade e regras de parada. O padrão esperado é ECO-1301; qualquer escolha diferente deve ser justificada com evidência normativa.
6. Antes de qualquer futura edição, prepare o mini-brief exigido por `docs/ai_task_playbook.md`.
7. Produza um plano de implementação em etapas pequenas, cada uma com: objetivo, arquivos prováveis, dependências, executor/subagente, critérios de aceite, comandos de verificação, riscos, rollback e ponto de parada.
8. Separe claramente:
   - ações que podem ser executadas após minha aprovação;
   - decisões/credenciais que dependem de mim;
   - ações proibidas ou ainda bloqueadas;
   - atividades que podem ou não ocorrer em paralelo.

## Restrições essenciais

- Uma task `ECO-XXXX` por vez, incluindo apenas dependências diretas.
- Não fazer refactor oportunista nem upgrade do Expo SDK 54.
- Não acessar production nem apagar/sobrescrever dados remotos.
- Não alterar a fonte externa `C:\Users\Bruno\Downloads\teste-rota`.
- Não expor `service_role`, secret key ou qualquer segredo no Expo, prompt, log, fixture ou commit.
- Supabase: consultar changelog/documentação atuais antes de implementar; migrations SQL em `supabase/migrations` são a única fonte do schema; criar novas migrations pelo comando da CLI instalado após consultar `--help`; grants, RLS e policies exigem testes positivos e negativos; não usar `auth.role()` nem `SECURITY DEFINER` como atalho.
- Não deixar fallback silencioso para `mockData.ts` em produção.
- Não declarar como verificado o que não foi reproduzido no ambiente correto.
- Pare para decisão se faltar Git íntegro, ambiente test isolado, ADR aceito, credencial/autorização externa ou se a ação tocar production.

## Formato da resposta para aprovação

Entregue exatamente estas seções:

1. **Estado real resumido** — o que está VERIFIED, PARTIAL, MISSING, BLOCKED ou NOT_VERIFIABLE.
2. **Divergências encontradas** — documentação versus código versus execução versus ambiente.
3. **Próxima task proposta** — ID, motivo e dependências.
4. **Plano de implementação para aprovação** — etapas numeradas, arquivos, responsáveis/subagentes, testes e rollback.
5. **Paralelismo e reservas de arquivos** — o que pode rodar junto e o que deve ser serial.
6. **Decisões ou acessos que preciso fornecer** — perguntas objetivas, sem pedir segredos no chat.
7. **Critério de conclusão da próxima task** — evidências necessárias para mudar seu estado.
8. **Estimativa de sessões** — diga explicitamente se será necessário continuar em uma nova conversa/sessão e indique o melhor ponto de handoff.

Encerre aguardando minha aprovação. Não comece a implementação nesta resposta.
