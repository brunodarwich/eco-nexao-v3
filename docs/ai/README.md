# Desenvolvimento diário com Codex e Google Antigravity

Este é o ponto de entrada operacional para desenvolver o ECOnexão com dois agentes:

- **Codex:** identifica a próxima tarefa, planeja, prepara prompts, revisa evidências e recomenda decisões.
- **Google Antigravity:** executa implementação e testes dentro do prompt preparado pelo Codex.
- **Owner:** decide requisitos e autoriza ações sensíveis.

A constituição completa está em `DEVELOPMENT_RULES.md`. O fluxo desta página não autoriza push, PR, merge, deploy, migration, escrita remota ou production.

## Leitura por sessão

Sempre:

1. `AGENTS.md` da raiz e qualquer `AGENTS.md` do diretório afetado.
2. `docs/README.md`.
3. Este arquivo.
4. `# CORE RULES` de `docs/ai/DEVELOPMENT_RULES.md`.
5. Task, protocolo da iniciativa, ADRs, contratos e critérios diretamente aplicáveis.

Ler `DEVELOPMENT_RULES.md` integralmente quando a sessão for nova, a tarefa tiver risco médio/alto, houver conflito de instruções ou o trabalho envolver banco, migration, Auth/RLS, segurança, dados remotos, deploy, integrações externas ou production. Em tarefa pequena, ler as CORE RULES e as seções diretamente relacionadas.

## O uso diário pelo owner

### 1. Pedir a próxima tarefa ao Codex

O owner pode escrever simplesmente:

```text
Qual é a próxima tarefa do ECOnexão? Analise o estado atual e gere o prompt pronto
para eu copiar no Google Antigravity.
```

Esse pedido **não autoriza o Codex a implementar a tarefa**. O Codex deve fazer apenas inspeção read-only, escolher uma única tarefa desbloqueada e produzir o prompt do Antigravity.

### 2. Executar no Antigravity

O owner copia o bloco entregue pelo Codex para uma nova conversa/worktree do Antigravity. O Antigravity apresenta o mini-brief, executa somente o escopo autorizado e termina com o handoff exigido.

### 3. Pedir revisão ao Codex

Depois da entrega do Antigravity, o owner pode escrever:

```text
Revise independentemente esta entrega do Antigravity e, se houver correções, gere o
próximo prompt pronto para eu devolver a ele:

[colar handoff e/ou link do PR]
```

O Codex verifica diretamente Git, diff, CI, código, testes e ambiente autorizado. O relato do Antigravity não é prova suficiente.

### 4. Repetir até aprovação

- `CHANGES_REQUIRED`: Codex fornece um prompt corretivo curto; owner envia ao Antigravity.
- `BLOCKED`: Codex informa uma única decisão, configuração ou acesso necessário.
- `NOT_VERIFIABLE`: Codex indica a evidência ou ambiente ausente, sem inventar conclusão.
- `APPROVE`: Codex informa exatamente o que foi aprovado e qual próximo gate depende do owner.

O ciclo termina somente quando os critérios de aceite estiverem comprovados no nível declarado. `APPROVE` de implementação local não autoriza merge, deploy ou escrita remota.

## Contrato do Codex ao escolher a próxima tarefa

Ao receber “qual é a próxima tarefa?”, o Codex deve:

1. Inspecionar Git, documentação ativa, tarefas, dependências, decisões abertas e handoffs sem alterar arquivos.
2. Determinar qual iniciativa está ativa; não presumir que o backlog historicamente mais antigo ainda é vigente.
3. Escolher **uma única task desbloqueada** pela precedência normativa, dependências e estado real.
4. Se nenhuma task estiver desbloqueada, escolher o bloqueio mais próximo do caminho crítico e pedir somente a decisão necessária.
5. Não antecipar a task seguinte nem agrupar tasks independentes por conveniência.
6. Informar por que a task foi escolhida e quais evidências sustentam o estado.
7. Gerar um prompt autocontido, sem placeholders técnicos que o owner precise descobrir.
8. Encerrar sem implementar e sem executar ação externa.

Formato obrigatório da resposta:

```text
Próxima task:
Status atual e evidência:
Por que é a próxima:
Dependências confirmadas:
Decisão/configuração necessária do owner: nenhuma | descrever uma ação objetiva
Risco e ponto de parada:

PROMPT PRONTO PARA O GOOGLE ANTIGRAVITY
[prompt autocontido em um bloco separado]

O que o owner faz agora: copiar o prompt acima no Antigravity.
```

## Como o Codex monta o prompt do Antigravity

O prompt deve resolver explicitamente:

```text
Task e objetivo observável:
Modo, repositório, branch-base e worktree:
Leituras obrigatórias e precedência:
Dependências e decisões aceitas:
Escopo, arquivos prováveis/reservados e fora do escopo:
Ambiente permitido e ações proibidas:
Mini-brief antes da primeira edição:
Capacidades: /goal, /grill-me, /skills, subagentes, CLI, MCP e /browser:
Contratos e comportamento que devem ser preservados:
Implementação esperada sem prescrever solução não investigada:
Testes, checks, evidências e exit codes:
Gates humanos, condições de abort e rollback:
Formato do handoff e ponto exato de parada:
```

O Codex deve entregar o prompt já adaptado à tarefa. Não deve mandar o owner escolher subagentes, descobrir comandos, localizar documentos ou decidir sozinho quais testes executar.

## Seleção das capacidades do Antigravity

- **`/goal`:** usar para uma tarefa única, executável e delimitada. Não confundir com GO humano.
- **GO humano:** pedir ao owner imediatamente antes da ação sensível; nunca inserir autorização presumida no prompt.
- **`/grill-me`:** usar para fechar conflito ou requisito por perguntas objetivas, sem edição.
- **`/skills`:** pedir quando houver skill especializada aplicável; usar somente as instaladas e pertinentes.
- **Subagentes:** definir papéis, ordem, escopo e arquivos reservados; nenhum subagente cria outro ou aprova a própria entrega.
- **CLI:** usar para evidências reproduzíveis, com ambiente, exit code e saída sanitizada.
- **MCP:** opcional e sujeito aos mesmos gates da CLI.
- **`/browser`:** usar para documentação oficial ou validação visual/interativa autorizada; normalmente depois dos checks técnicos.
- **`/schedule`:** não usar para deploy, migration, promoção, carga ou outra mutação sensível.

Protocolos específicos da iniciativa prevalecem quanto ao número e à sequência de subagentes. Na ausência de regra específica, o Codex usa a menor equipe que forneça planejamento, teste e revisão independentes proporcionais ao risco.

## Contrato de revisão do Codex

O Codex deve responder à entrega do Antigravity com:

```text
Task, autor e revisor:
Baseline, branch e commit revisados:
Fonte normativa:
Aceites e testes negativos reproduzidos:
Findings P0/P1/P2:
Decisão: APPROVE | CHANGES_REQUIRED | BLOCKED | NOT_VERIFIABLE
Evidência e limitações:
Decisão/configuração necessária do owner:
Próxima ação única:
Prompt corretivo pronto para o Antigravity, se necessário:
```

Finding P0/P1 volta ao Antigravity em um prompt curto que preserve o mesmo escopo e baseline. Depois da correção, o Codex repete os gates afetados e a regressão proporcional; não reinicia toda a auditoria sem ganho de confiança.

## Regras de comunicação com o owner

- Usar linguagem direta e acessível a uma pessoa não desenvolvedora.
- Apresentar uma decisão principal por vez.
- Dizer explicitamente se o owner precisa decidir, configurar ou autorizar algo.
- Nunca pedir segredo no chat; explicar apenas onde o owner deve configurá-lo com segurança.
- Terminar com uma única próxima ação concreta.
