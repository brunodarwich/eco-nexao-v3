# Supervisão Codex × Google Antigravity — ECO-2005

Este documento é o handoff operacional para revisar trabalho do Google Antigravity
em sessões novas do Codex. Ele não autoriza merge, acesso remoto nem escrita de dados.
Use-o junto de `AGENTS.md`, `docs/finalization/ai_coordination.md` e do runbook ativo.

## Estado conhecido em 03/09/2026

- PR #9: `feat/eco-2005-phase2-runner` para `staging`.
- Head revisado: `c59c1a3cf2f29903662d905aa8f540d0a0876b70`.
- Escopo: implementação **local** do runner da Fase 2; não houve preflight remoto ou
  escrita em staging/production.
- Revisão Codex: aprovado para merge **somente como implementação local**. O merge
  depende de autorização explícita do owner. Escrita remota continua bloqueada.
- Antes de qualquer escrita remota: preflight read-only autorizado, prova de
  idempotência em banco isolado de test e novo GO explícito do owner.

## Como o Codex deve revisar uma entrega do Antigravity

1. Leia `AGENTS.md`, a task ECO-2005, `docs/ai_task_playbook.md`, o runbook e este
   documento. Não aceite relato do executor como evidência suficiente.
2. Faça `git fetch origin`; confira branch, commit, diff, arquivos, estado do PR e
   checks de CI. Nunca faça merge, rebase, close ou push sem pedido explícito.
3. Leia o caminho de execução real, não apenas os testes. Compare os contratos do
   produtor e consumidor e confirme a ordem: validação de target -> confirmação ->
   conexão -> transação -> lock -> persistência -> State Guard -> commit.
4. Reproduza testes locais proporcionais ao risco; revise `git diff --check`,
   `git status --short` e o scanner de segredos. Para Fase 2, o comando fail-closed
   `--apply --non-interactive` pode ser executado somente para comprovar o abort.
5. Classifique findings como P0, P1, P2 ou pendência externa. Entregue um próximo
   prompt curto e determinístico; mantenha `BLOCKED` quando depender de autorização
   ou de um ambiente que não pode ser acessado.

## Instruções por capacidade do Antigravity

| Capacidade | Permitido | Limite obrigatório |
|---|---|---|
| Git, worktrees e PRs | criar worktree a partir de `origin/staging`, commit e push de alteração autorizada | não criar PR/merge/fechar PR por inferência; não reutilizar branch obsoleta; nunca usar reset/checkout destrutivo |
| Implementação Python | editar somente arquivos declarados no mini-brief, manter contratos tipados e a Unit of Work | não resolver erro de tipo com `Any`, `cast` ou `type: ignore` sem justificativa; não substituir contrato real por mock conveniente |
| Testes e CI | pytest, Ruff, MyPy, secret scan e checks de diff | executar `python -m mypy app` completo antes de declarar sucesso; relatar exit code e saída real, não estimativas |
| Supabase e banco | validação local de URL/ref/porta e testes offline | sem staging/production, CLI remota, advisor, migration list ou `--apply` interativo sem GO explícito; nunca exibir DSN, JWT, key ou `.env` |
| Documentação/runbooks | documentar somente fatos implementados e evidências existentes | não afirmar auditoria, migration remota, advisor, RLS ou escrita remota como verificados sem comando e resultado correspondentes |
| Browser, MCP e subagentes | browser apenas para smoke visual read-only autorizado; subagentes somente em escopos independentes | MCP/browser não contornam gates; nenhum subagente escreve em arquivos reservados por outro; não usar automação agendada para promoção |

## Lições incorporadas a partir das revisões do PR #9

1. **Execute qualidade completa antes do push.** O primeiro commit falhou no CI por
   dez erros MyPy que seriam detectados por `python -m mypy app` local.
2. **Teste o contrato de produção.** `persist_in_transaction` retornava um dicionário,
   mas testes simulavam `PersistenceCounts`; o runner teria falhado com `AttributeError`
   dentro da transação. Mocks devem respeitar exatamente o tipo e a forma retornada em
   produção.
3. **Fail-closed também vale para APIs programáticas.** Não basta proteger o CLI:
   função chamável deve exigir configuração completa e validada, sem inferir staging
   por fallback.
4. **Somas não são State Guard suficiente.** Um total correto pode esconder uma carga
   híbrida. Para promoção sensível, aceite apenas perfis completos, mutuamente
   exclusivos e testados, com rollback em qualquer divergência.
5. **Idempotência precisa declarar fronteira.** Entidades de domínio devem ser
   idempotentes; `ingestion_runs` e `raw_source_records` são ledger append-only por
   tentativa. Nunca chame o ledger de “duplicação” nem chame a carga de “totalmente
   idempotente” sem explicar esta diferença.
6. **Não transforme intenção em evidência.** Preflight de migrations/advisors e
   validação de auditoria remota são pendências até que exista comando read-only
   autorizado, contrato e relatório sanitizado.
7. **Relatos são estritamente escopados.** Não diga “zero `type: ignore`” sem limitar
   a afirmação ao diff revisado; não diga “nenhuma escrita” sem distinguir o que foi
   realmente reproduzido do que foi apenas afirmado pelo executor.
8. **Privilégio humano não é confirmação de terminal.** Digitar o project ref e `y`
   reduz acidente operacional, mas não substitui o GO explícito do owner.

## Evidência mínima para revisar a próxima entrega local

```powershell
git fetch origin
gh pr view 9 --json headRefOid,mergeable,mergeStateStatus,statusCheckRollup,url
git -C .worktrees/eco-2005-phase2 diff --check origin/staging...HEAD
cd .worktrees/eco-2005-phase2/backend
python -m pytest tests/test_pindobal_persistence.py tests/test_staging_promotion_runner.py -q
python -m ruff check app tests
python -m mypy app
python scripts/scan_secrets.py --root ..
python -m app.ingestion.staging_promotion_runner --apply --non-interactive
git status --short
```

O último comando deve falhar fechado antes de criar conexão, engine ou sessão remota.
Não configurar variáveis de ambiente remotas para esta verificação.

## Pendências que não podem ser "resolvidas" por IA sem autorização

- merge do PR #9;
- acesso read-only ao staging para o preflight remoto;
- credenciais ou acesso ao Supabase test/staging;
- prova de integração em banco isolado de test;
- GO para `--apply` e qualquer escrita em staging;
- toda ação em production.
