# Protocolo obrigatório das sessões ECO-24XX

## 1. Meta e escopo

Todo prompt começa com `/goal`. O coordenador registra a meta, executa somente a task
indicada e não inicia a próxima. Antes de editar, lê integralmente as fontes exigidas
e publica o mini-brief de `docs/ai_task_playbook.md`.

## 2. Orquestração de subagentes

Usar os subagentes disponíveis sem ultrapassar quatro agentes ativos, incluindo o
coordenador. O coordenador continua responsável pela leitura normativa e decisão final.

1. **arquiteto**, somente leitura: inventário, dependências, riscos, paradas e plano.
2. **implementador**, escrita restrita: aplica apenas o mini-brief aprovado e registra
   comandos; nunca edita em paralelo os mesmos arquivos do coordenador.
3. **verificador**, independente e somente leitura: executa testes, revisa diff,
   procura consumidores esquecidos, segredos, alterações comportamentais e perda de
   evidência.

Quando a task tiver inventários independentes, o arquiteto pode dividir pesquisa com
um segundo auditor somente leitura, desde que o limite de agentes seja respeitado.
Para confirmação final, o verificador não reutiliza conclusões do implementador:
reproduz comandos e aceites. Finding P0/P1 retorna ao implementador por follow-up;
depois, o verificador repete os gates afetados.

Subagentes não criam outros subagentes. Nenhuma edição concorrente é permitida em
OpenAPI, migrations, lockfiles, workflows, configs de deploy ou índices normativos.

## 3. Segurança

- registrar `git status --short` e preservar alterações do usuário;
- não imprimir `.env`, tokens, DSNs, JWTs ou chaves;
- não acessar production ou alterar remotos;
- não apagar ou mover material sem alvo exato e gate humano quando exigido;
- não usar refactor oportunista para justificar remoção;
- não atualizar dependências salvo task explícita;
- usar `rg`/Git/import graph e configuração real para provar ausência de consumidor;
- tratar ausência de referência como evidência necessária, não prova suficiente.

## 4. Estados

- `PROPOSED`: ainda não autorizada.
- `BLOCKED`: decisão, dependência ou autorização ausente.
- `PARTIAL`: alteração feita, mas gate obrigatório não reproduzido.
- `VERIFIED`: aceites reproduzidos de forma independente.
- `NOT_VERIFIABLE`: ambiente obrigatório indisponível.

## 5. Entrega

```text
Goal:
Resultado:
Task concluída: sim/não
Status:
Baseline e alterações preservadas:
Arquivos alterados/movidos/removidos:
Comandos, ambiente e exit codes:
Aceites reproduzidos pelo verificador:
Findings e correções:
Evidências preservadas:
Riscos e limitações:
Rollback:
Decisões humanas pendentes:
Próxima task desbloqueada:
```

