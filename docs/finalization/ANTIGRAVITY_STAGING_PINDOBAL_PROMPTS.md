# Prompts Antigravity — promoção saudável de Pindobal para staging

Este roteiro divide o trabalho em entregas verificáveis e impede que uma execução
autônoma atravesse aprovações humanas ou alcance production. Execute um prompt por
conversa/worktree e só avance quando a entrega anterior estiver aprovada.

## Preparação no Antigravity

1. Abra o projeto `C:\Users\Bruno\Downloads\eco-nexao-v3` em **New Worktree Mode**, a
   partir da branch remota `staging` atualizada.
2. Confirme que o PR documental #6 foi incorporado ou que seu conteúdo faz parte da
   base escolhida.
3. Digite `/skills` e use somente skills realmente instaladas e pertinentes a Git,
   Python/FastAPI, PostgreSQL/Supabase, segurança e testes. A ausência de uma skill não
   autoriza instalar plugins ou alterar a arquitetura.
4. Não cole secrets no chat. Use apenas CLIs já autenticadas e secret stores das
   plataformas. Comandos e relatórios devem ocultar valores.
5. Use subagentes somente com escopo e arquivos reservados. O agente principal é o
   único responsável por integrar alterações e verificar o diff final.

## Entrega 1 — ECO-1505: pacote de promoção verificável, sem escrita remota

Use `/goal` para esta etapa, pois ela é local, reversível e tem conclusão objetiva.
Cole o prompt abaixo após `/goal`:

```text
Execute exclusivamente ECO-1505 — Pacote de promoção Pindobal — no repositório
ECOnexão. Trabalhe em New Worktree Mode a partir da branch staging atualizada.

Leia integralmente, nesta ordem: AGENTS.md; docs/README.md;
docs/backend_integration_spec.md; o bloco ECO-1505 em docs/finalization/tasks.md;
docs/ai_task_playbook.md; docs/data/pindobal_seed_contract.md e todas as referências
diretas indicadas pela task; docs/finalization/artifacts/pindobal-v1/README.md,
APPROVAL.md, promotion_manifest.json, promotion_manifest.sha256 e smoke.sql.
Respeite a precedência normativa de AGENTS.md. Antes de editar, apresente o mini-brief
obrigatório.

ESCOPO E LIMITES

- Esta etapa é somente local/test e não pode escrever em staging ou production.
- C:\Users\Bruno\Downloads\teste-rota é fonte externa somente leitura.
- Não faça chamadas reais ao Google. Use snapshots/fixtures contratuais.
- Não leia nem imprima valores de .env, tokens, JWTs, senhas ou chaves.
- Não altere migrations, schema remoto, dashboards, Vercel, Render ou Supabase remoto.
- Não aprove automaticamente candidatos fuzzy e não invente google_place_id.
- Preserve alterações existentes do usuário e não use reset/checkout destrutivo.
- Não faça refactor oportunista nem trabalhe em outra ECO.

ORQUESTRAÇÃO

Crie no máximo três subagentes:
1. Auditor de contrato, somente leitura: valide requisitos, licenças, hashes esperados,
   critérios de abort e dependências da ECO-1505.
2. Verificador técnico, somente leitura: reproduza dry-run, contagens, hashes, schema do
   manifesto e testes offline; não abra arquivos de secrets.
3. Revisor de segurança, somente leitura: procure PII indevida, secrets, referências a
   production e qualquer comando que possa escrever fora de test.

O agente principal consolida os achados, faz as edições necessárias no pacote e executa
as verificações. Subagentes não editam os mesmos arquivos nem fazem ações remotas.

USE A CLI PARA EVIDÊNCIA REPRODUZÍVEL

- git status/diff/log sem imprimir configuração sensível;
- help do seed_pindobal antes de assumir flags;
- dry-run contra teste-rota;
- verificação de SHA-256 do pacote;
- testes unitários/contratuais diretamente relacionados;
- secret scan somente por padrões e nomes, sem exibir valores encontrados.

ENTREGA SAUDÁVEL / DEFINITION OF DONE

- manifesto identifica versões de snapshot, importador, migrations e regras;
- hashes podem ser recalculados offline e coincidem;
- relatório registra lidos, candidatos, rejeições, ambiguidades e justificativas;
- rollback lógico draft/unpublished e critérios de abort estão documentados;
- segunda validação em test demonstra idempotência sem duplicação;
- zero segredo, PII indevida, chamada Google ou acesso a staging/production;
- testes e comandos executados são listados com resultados;
- diff contém apenas arquivos da ECO-1505;
- PR dedicado para staging é aberto, mas não mesclado automaticamente.

PARE E ENTREGUE BLOCKED se faltar dependência aceita, test isolado, contrato, aprovação
editorial ou se qualquer comando tentar alcançar staging/production. Ao concluir,
entregue: arquivos alterados, comandos/resultados, contagens, riscos, rollback,
pendências e link do PR. Não prossiga para ECO-2202 nem importe dados.
```

### Aceite humano da Entrega 1

Aceite somente se o PR estiver verde, os hashes forem reproduzíveis, o dry-run tiver
contagens explicadas, a idempotência estiver comprovada em test e não houver qualquer
escrita em staging/production.

## Entrega 2 — fechar a lacuna normativa de promoção para staging

Não use `/goal` nesta etapa: ela termina em uma decisão humana. Cole como uma conversa
normal ou use `/grill-me` para o agente perguntar apenas o que realmente bloquear a
definição.

```text
Faça uma análise somente leitura para definir a autorização normativa da promoção
Pindobal em staging. Não implemente código e não escreva em ambiente remoto.

Leia AGENTS.md, docs/finalization/tasks.md (ECO-1505, ECO-2002, ECO-2003 e ECO-2202),
docs/finalization/dependency_graph.md, docs/finalization/release_checklist.md,
docs/finalization/artifacts/pindobal-v1/* e os runbooks de promoção.

Há uma lacuna a resolver: ECO-1505 proíbe aplicar fora de test, enquanto ECO-2202 exige
GO/janela/autorização de production. O trabalho atual é exclusivamente staging e não
pode usar ECO-2202 como autorização implícita para production.

Proponha para aprovação humana uma única task/alteração normativa que autorize somente
a promoção test -> staging. Não invente um ID silenciosamente: apresente a opção de ID,
dependências e texto completo para aprovação. A definição deve incluir target allowlist
por project ref/host, confirmação dupla antes de escrita, transação, advisory locks,
idempotência, relatório redigido, rollback lógico, abort thresholds, RLS/Auth/Storage
positivo e negativo, smoke público e proibição absoluta de production e Google real.

Entregue apenas: divergência normativa, proposta de task, arquivos documentais a
alterar, critérios de aceite, comandos planejados sem valores, riscos e perguntas ao
owner. Pare aguardando aprovação. Não edite código nem documentação nesta conversa.
```

### Aceite humano da Entrega 2

O owner deve aprovar explicitamente a task, o ambiente staging exato, as contagens do
dry-run, os critérios de abort e o rollback. Production deve continuar fora do escopo.

## Entrega 3 — promoção e homologação em staging

Use uma nova conversa/worktree depois dos aceites das Entregas 1 e 2. Não use `/goal`
durante a escrita remota: o agente precisa parar no checkpoint GO antes do apply.

```text
Execute somente a task de promoção test -> staging aprovada pelo owner e somente no
Supabase econexao-staging, project ref kchzucvrnzwzehfdwzwi. Production é proibida.

Antes de agir, leia AGENTS.md e todas as referências da task aprovada; apresente o
mini-brief; faça preflight read-only de Git, pacote, hashes, vínculo Supabase, migration
list, advisors e target identity. Não imprima valores de credenciais.

Primeiro implemente e teste localmente o mecanismo de promoção com allowlist explícita
de staging, fail-closed, transação, lock, idempotência, dry-run e relatório redigido.
Abra PR e exija checks verdes. Não aplique no remoto nesta fase.

Depois do merge e somente após um segundo GO explícito do owner, execute nesta ordem:
1. reconfirmar target staging por project ref e negar qualquer outro target;
2. registrar estado anterior e capacidade de rollback;
3. repetir o dry-run e comparar hashes/contagens com o pacote aprovado;
4. abortar em qualquer divergência ou advisory crítico;
5. aplicar uma única carga transacional e idempotente;
6. executar a segunda carga para provar ausência de duplicação;
7. validar RLS, Auth e Storage com casos positivos e negativos;
8. validar /health, /health/ready, /regions, mapa/catálogo e CORS permitido/negado;
9. produzir relatório final redigido com run IDs, contagens e incidentes.

Use CLIs para Git, testes e Supabase. Use MCP apenas se estiver configurado e oferecer
o mesmo isolamento/auditoria; nunca o use para contornar gates. Não faça chamadas reais
ao Google.

Use /browser somente após a carga e os checks técnicos, para um smoke visual read-only
em https://econexao-app-staging.vercel.app. Verifique console/rede, região Pindobal,
rota, mapa, catálogo, estados vazio/erro/retry e ausência de dados inventados. Não abra
production nem dashboards que possam revelar secrets. Capture apenas telas sem dados
sensíveis.

ENTREGA SAUDÁVEL / DEFINITION OF DONE

- target comprovado como kchzucvrnzwzehfdwzwi antes de cada escrita;
- pacote/hashes exatamente iguais aos aprovados;
- carga 1 com contagens explicadas e carga 2 com zero duplicações;
- zero rejeição inexplicada e zero publicação parcial;
- migrations alinhadas, advisors sem crítico e RLS/Auth/Storage positivos/negativos;
- API e web de staging exibem o conteúdo esperado;
- workflow staging verde ou falha residual explicada e corrigida;
- rollback testado/documentado e relatório sem secrets/PII;
- production e Google não foram acessados;
- arquivos, comandos, resultados, riscos e próxima ação entregues.

Pare imediatamente se o target divergir, faltar GO, os hashes/contagens mudarem, houver
advisory crítico, risco de sobrescrita, falha de transação/idempotência ou qualquer
referência a production. Não tente corrigir dados diretamente pelo Dashboard.
```

## Uso recomendado das capacidades do Antigravity

- **`/goal`:** sim, apenas na Entrega 1 local e totalmente delimitada.
- **`/grill-me`:** sim, na Entrega 2, para fechar a decisão normativa.
- **Skills:** sim, após `/skills`; somente skills instaladas e relevantes.
- **Subagentes:** sim, para auditoria/revisão com escopos independentes; escrita serial
  e integração pelo agente principal.
- **CLI/terminal:** obrigatório para evidências reproduzíveis e redigidas.
- **MCP:** opcional; nunca substitui allowlists, checks de target ou aprovações.
- **`/browser`:** somente no smoke visual read-only da Entrega 3.
- **`/schedule`:** não usar; promoção de dados não deve rodar de forma agendada.

