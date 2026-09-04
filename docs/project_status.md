# ECOnexão — status atual e backlog único

Atualizado em: 04/09/2026  
Prioridade atual: **terminar a versão Web**  
Fonte ativa: este é o único documento usado para decidir “o que falta?” e “qual é a próxima task?”.

> Regra simples: código existente não significa tarefa concluída. Uma capacidade só recebe
> `VERIFIED` na plataforma e no ambiente em que a evidência foi realmente reproduzida.

## Leia isto primeiro

| Pergunta | Resposta curta |
|---|---|
| O app já tem bastante implementação? | Sim. Backend, banco, catálogo, mapa e frontend têm implementação material. |
| A versão Web está pronta? | Ainda não. Falta reconciliar evidências e fechar homologação/staging/release Web. |
| Android/iOS bloqueiam a Web? | **Não.** Todo trabalho nativo está em `MOBILE_LATER`. |
| Os backlogs antigos ainda comandam a ordem? | Não. Eles são histórico e entrada de auditoria. O trabalho aberto está abaixo. |
| Produção está autorizada? | Não. Deploy, migrations remotas e promoção continuam exigindo GO humano específico. |

## Como ler o estado

### Estado da task

- `VERIFIED`: aceite reproduzido no ambiente e plataforma declarados.
- `PARTIAL`: há implementação/evidência, mas falta parte do aceite.
- `MISSING`: capacidade essencial ainda não existe.
- `BLOCKED`: depende de decisão, credencial, ambiente ou autorização.
- `NOT_VERIFIABLE`: não foi possível reproduzir a alegação com segurança.
- `MOBILE_LATER`: trabalho Android/iOS deliberadamente adiado; não bloqueia a Web.
- `RECONCILE`: há sinais de implementação, mas a task antiga ainda precisa ser conferida contra código e evidência.

### Nível de evidência

| Nível | O que comprova |
|---|---|
| `CODE` | implementação encontrada; não prova execução |
| `LOCAL_TEST` | teste automatizado local; simulação de Android/iOS continua sendo teste local |
| `WEB_LOCAL` | comportamento Web reproduzido localmente/browser |
| `STAGING` | comportamento reproduzido no ambiente remoto de staging identificado |
| `PRODUCTION` | comportamento reproduzido em produção após autorização |
| `DEVICE` | comportamento reproduzido em aparelho/emulador da plataforma indicada |

## Foto atual por frente

| Frente | Plataforma | Estado conservador | Melhor evidência registrada | O que ainda falta |
|---|---|---|---|---|
| Mapa dinâmico ECO-2301–2314 | Web | `PARTIAL` | `CODE`, `LOCAL_TEST` e alegações Web em registros da iniciativa | reconciliar a evidência Web e fechar integração real autorizada do Google Routes |
| Verificação final do mapa ECO-2315 | Web | `PARTIAL` | testes/relatórios locais | gate Web final depois da reconciliação e do staging aplicável |
| Catálogo ECO-2501–2511 | Backend/Web | `PARTIAL` | implementação e ampla suíte local | reproduzir matriz mínima de dados, API e UI; separar local de staging |
| Catálogo ECO-2512 | Web | `PARTIAL` | Jest e relatos de E2E/a11y Web | validar comandos/artefatos Web de forma independente |
| Homologação ECO-2513 | Web | `NOT_VERIFIABLE` | dossiê histórico | homologação real não pode ser inferida do dossiê ou de suítes simuladas |
| Finalização ECO-13xx–20xx | Backend/Web | `RECONCILE` | código, migrations, testes e handoffs diversos | mapear cada task ao estado real antes de chamar de concluída |
| E2E Web ECO-2101 | Web | `PARTIAL` | suítes e artefatos Web existentes | reprodução independente no ambiente-alvo |
| Release Web ECO-2104, ECO-2201–2203, ECO-2205 | Web/API | `BLOCKED` | documentos e artefatos de planejamento | depende dos gates Web, staging e GO humano correspondente |
| ECO-2310/2311 nativo, ECO-2102/2103, ECO-2204 | Android/iOS | `MOBILE_LATER` | somente código/testes locais quando existentes | será retomado depois da versão Web; não entra no caminho crítico atual |

### Correções de status importantes

- ECO-2512 não é `VERIFIED` multiplataforma na fonte ativa. Testes Jest rotulados
  Android/iOS não equivalem a evidência `DEVICE`; para Web, permanece `PARTIAL` até
  reprodução independente dos comandos e artefatos.
- ECO-2513 não é `VERIFIED` nem autoriza promoção. O registro histórico é insumo;
  a homologação permanece `NOT_VERIFIABLE` até os gates Web/staging serem reproduzidos.
- ECO-2310 e ECO-2311 podem ter evidência Web sem que Android/iOS estejam prontos.
  A parte nativa foi movida para `MOBILE_LATER`.
- Números de testes em relatórios antigos são snapshots da data da execução, não o
  total atual do projeto.

## Backlog único — somente trabalho aberto

Execute uma task por vez. A ordem abaixo é o caminho Web; itens `MOBILE_LATER` ficam
fora desta sequência.

### 1 — Confiar novamente no backlog

1. **ECO-2402 — Fonte única de status e backlog aberto (`IN_PROGRESS`)**
   - concluir esta consolidação, validar links e obter aprovação do owner;
   - não mover/remover documentação nesta task.
2. **RQ-01 — Reconciliar ECO-13xx–19xx (`RECONCILE`)**
   - fila documental temporária, não uma nova feature;
   - comparar task por task com código, migration, testes e ambiente;
   - resultado: cada task fica `VERIFIED`, `PARTIAL`, `MISSING` ou `BLOCKED` com nível de evidência.
3. **RQ-02 — Reconciliar ECO-2001–2005 e staging (`RECONCILE`)**
   - resolver divergências entre ADR 0005, backlog antigo, configuração real e handoffs;
   - registrar separadamente “configurado”, “implantado” e “homologado”.
4. **RQ-03 — Reproduzir evidência Web de ECO-2301–2315 e ECO-2501–2513 (`RECONCILE`)**
   - rebaixamentos de ECO-2512/2513 permanecem até reprodução independente;
   - não exigir aparelho móvel.

### 2 — Fechar a versão Web

5. **ECO-2314 — Google Routes em ambiente autorizado (`BLOCKED`)**
   - fechar secret manager, políticas, custo/quota e smoke de staging;
   - exige configuração e GO humano imediatamente antes de qualquer chamada real.
6. **ECO-2315 — Verificação final do mapa Web (`PARTIAL`)**
   - executar os aceites Web com as três origens fixas e os fluxos dinâmicos aplicáveis.
7. **ECO-2101 — E2E Web e acessibilidade (`PARTIAL`)**
   - reproduzir jornada crítica em browser/staging e registrar falhas reais.
8. **ECO-2104 — Auditoria final aplicável à Web/API (`RECONCILE`)**
   - segurança, desempenho, privacidade, custos e contratos no escopo Web.
9. **ECO-2201 — Go/no-go Web/API (`BLOCKED`)**
   - gerar pacote imutável apenas depois dos gates anteriores.
10. **ECO-2202 — Promoção controlada de migrations e Pindobal (`BLOCKED`)**
    - requer ambiente-alvo confirmado, backup/rollback e GO humano.
11. **ECO-2203 — Publicação controlada da API e Web (`BLOCKED`)**
    - requer o artefato aprovado e GO humano separado.
12. **ECO-2205 — Operação assistida Web/API (`BLOCKED`)**
    - encerrar a janela Web sem depender das lojas mobile.

### 3 — Higiene documental depois da aprovação da matriz

13. **ECO-2403 — Arquivar planos concluídos (`BLOCKED`)**
    - depende da aprovação da matriz e preserva o histórico.
14. **ECO-2404 — Política de artefatos e evidências (`PARTIAL`)**
    - definir o que é regenerável, local ou versionável.
15. **ECO-2405–ECO-2410 — Saúde restante (`BLOCKED`)**
    - executar na ordem e nos gates do pacote histórico, sem misturar com features Web.

## Mobile, depois da Web

Estes itens estão deliberadamente fora do backlog ativo Web:

- parte Android/iOS de ECO-2304, ECO-2307, ECO-2310, ECO-2311, ECO-2315 e ECO-2512/2513;
- ECO-2102 — E2E Android;
- ECO-2103 — E2E iOS;
- ECO-2204 — publicação Android/iOS.

Estado comum: `MOBILE_LATER`. Quando a versão Web estiver encerrada, será criado um
backlog mobile próprio com evidência `DEVICE` e critérios por plataforma.

## Próxima ação única

Revisar e aprovar a matriz em [`documentation_matrix.md`](documentation_matrix.md).
Depois disso, a próxima execução é **RQ-01**, sem implementação de feature.
