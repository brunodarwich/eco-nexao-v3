# Protocolo obrigatório das sessões ECO-23XX

## 1. Uma task por sessão

O agente raiz executa somente a task indicada no prompt. Não antecipa dependências,
não aproveita para refatorar e não inicia a próxima task após terminar.

## 2. Orquestração obrigatória de subagentes

Respeitar no máximo quatro agentes ativos, incluindo o coordenador. Para minimizar
conflitos, este pacote exige no máximo um subagente ativo por vez. Cada subagente é
encerrado antes da criação do seguinte e fica proibido de criar outros subagentes.

### Etapa 1 — planejar

Criar `planejador`, somente leitura. Ele lê fontes normativas, produz o mini-brief,
verifica dependências, conflitos, segurança, privacidade, custo e paradas obrigatórias.
O agente raiz espera o encerramento e publica o mini-brief antes de qualquer edição.

### Etapa 2 — implementar

Depois de encerrar o planejador, criar:

- `implementador`: realiza somente as alterações aprovadas no mini-brief, preserva
  mudanças do usuário e registra comandos executados.

O coordenador não permite que outro agente edite os mesmos arquivos em paralelo.

### Etapa 3 — testar

Depois de encerrar o implementador, criar `testador`, somente leitura. Ele executa os
testes proporcionais ao risco e relata comandos, ambiente e exit codes. O testador não
corrige o produto.

### Etapa 4 — revisar

Depois de encerrar o testador, criar `revisor`, somente leitura. Ele revisa diff,
contrato, acessibilidade, segurança, privacidade, escopo e aderência normativa.

Finding P0/P1 ou teste obrigatório falho retorna ao `implementador` por follow-up.
Após correção, o coordenador aciona novamente testador e revisor, em sequência, para
a validação afetada e os gates regressivos necessários.

### Etapa 5 — consolidar

Depois de testes e revisão verdes, criar:

- `consolidador`: confere aceites um a um, organiza evidências sanitizadas, riscos,
  rollback e handoff. Não inventa aprovação e não altera código do produto.

O agente raiz valida o relatório e faz a entrega final. A consolidação não transforma
`PARTIAL` ou `NOT_VERIFIABLE` em `VERIFIED`.

## 3. Leitura obrigatória do agente raiz

Subagentes não substituem a leitura do coordenador. Antes de agir, o agente raiz lê:

1. `AGENTS.md`;
2. `docs/README.md`;
3. `docs/backend_integration_spec.md`;
4. `docs/ai_task_playbook.md`;
5. `docs/mapa_dinamico/README.md`;
6. `docs/mapa_dinamico/plano_implementacao.md`;
7. `docs/mapa_dinamico/tasks.md` e o bloco completo da task;
8. o prompt completo da task;
9. ADRs, contratos e critérios citados no prompt.

## 4. Regras de segurança e coordenação

- Registrar `git status --short` e baseline; se não houver Git verificável, declarar.
- Não compartilhar `.env`, DSN, JWT, API key, localização real ou payload pessoal.
- Não usar produção nem fazer chamadas externas em testes.
- Não permitir edições concorrentes em OpenAPI, migrations, modelos, `app.json`,
  lockfiles ou workflows.
- Contract-first: OpenAPI/schema antes de consumidores.
- Migration apenas pelo comando oficial descoberto com `supabase --help`.
- Integração Google exige documentação atual, mocks, cost guard e revisão cruzada.
- Qualquer acesso production, gasto, dado remoto destrutivo ou ADR aberto causa parada.

## 5. Mini-brief obrigatório

```text
Task:
Objetivo observável:
Dependências verificadas:
Documentos lidos:
Arquivos esperados:
Contrato/schema afetado:
Dados e ambiente:
Testes que serão executados:
Fora do escopo:
Riscos/ações que exigem aprovação:
```

## 6. Entrega obrigatória

```text
Resultado:
Task concluída: sim/não
Status: VERIFIED | PARTIAL | BLOCKED | NOT_VERIFIABLE
Arquivos alterados:
Contratos/migrations:
Testes executados, exit codes e ambiente:
Aceites comprovados:
Evidências sanitizadas:
Verificações Supabase/RLS/Google/privacidade:
Findings do revisor:
Riscos ou limitações:
Rollback:
Pendências/decisões humanas:
Próxima task desbloqueada:
```
