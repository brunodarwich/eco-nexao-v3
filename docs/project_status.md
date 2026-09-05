# ECOnexão — documento único de tarefas

Atualizado em: 05/09/2026. Consolidação **revisada; commit local autorizado pelo owner após verificação**.
Este é o único cadastro de tasks: concluídas, parciais, novas, adiadas e substituídas.
Os documentos de iniciativas preservam aceites/evidências históricos, mas não definem
prioridade ou estado atual. A sequência abaixo orienta a próxima execução; decisões
ainda abertas permanecem em ECO-2603 e não são aprovadas pelo commit documental.

## Como acompanhar

- **Agora:** ECO-2601 concluída documentalmente. Próxima task: ECO-2602, identificação
  da baseline, antes de assumir que a pasta é a versão entregue.
- **Objetivo:** Web com dez rotas, mapa fluido, pins sem clusters, catálogo por categorias
  e experiências, login Google, favoritos e histórico de viagens.
- **Dados:** owner entrega dez rotas até sexta; data absoluta ainda a confirmar
  (próxima sexta na data desta nota: 11/09). Piloto em uma semana e evento em cerca
  de quinze dias são janelas informadas, não promessa de conclusão nem datas confirmadas.
- **Orçamento:** R$ 500/mês total, cerca de 300 pessoas no evento e acessos posteriores
  por compartilhamentos. Orçamento não equivale a autorização de contratação.
- **Fora do lançamento:** painel completo, comentários, contribuições públicas e nativo.
  Posição no mapa está dentro; voz/curva a curva não são desejadas.
- **Commits:** por incremento testado e revisado. A consolidação foi apresentada e o
  owner autorizou seu commit após revisão. Push/PR/merge/deploy/migration/carga exigem seus gates.

## Estados e evidências

| Estado | Significado |
|---|---|
| CONCLUÍDA DOCUMENTAL | Decisão/documento aceito anteriormente; não prova software em execução |
| CONCLUÍDA LOCAL | Aceite local registrado em evidência anterior; não reexecutado nesta consolidação |
| CONCLUÍDA STAGING LIMITADA | Somente o smoke/escopo remoto descrito; não equivale ao release |
| PARCIAL | Há implementação ou evidência, mas falta parte do resultado |
| PENDENTE | Trabalho novo ainda não comprovado; só iniciar com dependências satisfeitas |
| EM REVISÃO | Entrega preparada, esperando revisão; não significa aprovada |
| A RECONCILIAR | Situação individual exige confrontar evidência e ambiente |
| BLOQUEADA / BLOQUEADA POR DADOS | Gate humano, dependência ou conteúdo ausente |
| CONDICIONAL / DECISÃO PENDENTE | Proposta não obrigatória ou dependente de decisão explícita |
| ADIADA | Preservada para depois, sem bloquear a Web |
| SUBSTITUÍDA | ID histórico mantido; execução transferida às sucessoras indicadas |
| CANCELADA NO ESCOPO | Não será executada neste direcionamento |

CODE = existência de código/SQL; LOCAL_TEST = teste local; WEB_LOCAL = navegador
local; STAGING = ambiente remoto identificado; DEVICE = aparelho/emulador nativo;
PRODUCTION = versão realmente servida em produção. Não transferir evidência entre níveis.
Web no Safari do iPhone não é homologação do aplicativo iOS nativo.

## Ordem proposta da versão do evento

Executar uma task por vez. Dependências externas podem ser preparadas cedo, sem
antecipar escrita remota. Cada task concluída recebe evidência e commit, quando houver.

| Marco | Tasks em ordem | Ponto de controle/commit |
|---|---|---|
| 0 — Consolidar e proteger base | ECO-2601 → ECO-2602 → ECO-2603 | Consolidação revisada; identificar baseline e reconciliar contratos |
| 1 — Preparar alimentação | ECO-2604 → ECO-2605 | Template/pipeline reproduzíveis sem depender do painel |
| 2 — Conta e viagens | ECO-2606 → ECO-2607 | Login e persistência verificados; configurar dependências cedo |
| 3 — Experiência Web | ECO-2608 → ECO-2609 → ECO-2610 → ECO-2611 → ECO-2612 → ECO-2613 → ECO-2614 | Commits pequenos por comportamento funcional, sem aguardar todo marco |
| 4 — Dez rotas | ECO-2621 → ECO-2622 → ECO-2623 → ECO-2624 → ECO-2625 → ECO-2626 → ECO-2627 → ECO-2628 → ECO-2629 → ECO-2630 | Primeira/segunda rota comprovam padrão; demais têm aceite individual |
| 5 — Fluidez e homologação | ECO-2615 → ECO-2315 → ECO-2513 → ECO-2101 | Navegador e API reais; novos aceites não herdam aprovação antiga |
| 6 — Auditoria e release | ECO-2104 → ECO-2201 → ECO-2202 → ECO-2203 → ECO-2205 | Artefato imutável, GO separado, dados/publicação/observação |

ECO-2616 (fotos nos cards) é opcional após ECO-2615; se implementada, repetir os gates
afetados antes do go/no-go. ECO-2310/2311 (origem dinâmica) podem ficar desabilitadas
sem retirar o acompanhamento da posição: decisão explícita em ECO-2603.
Pré-condições antigas de segurança/dados permanecem obrigatórias quando aplicáveis;
lacuna descoberta em task de base deve ser corrigida antes do consumidor, sem fingir
que RQ-01/RQ-02 concluíram todos os aceites operacionais individuais.

**Gate de dependências em ECO-2602/2603:** para cada base PARCIAL citada abaixo,
registrar se o requisito necessário já passa, se a nova task assume sua conclusão
ou se uma correção da base deve entrar imediatamente antes na sequência. Até essa
classificação, a task consumidora não está liberada. Não exigir que um painel adiado
seja completado para reutilizar a API que já funciona.

| Base anterior | Task que evolui/reutiliza | Regra para não duplicar trabalho |
|---|---|---|
| ECO-2005 | ECO-2605 | Reusar runner/guardas; generalização é da nova task. Corrigir falha de integridade antes de qualquer carga |
| ECO-1902 | ECO-2606 | OAuth Google e continuidade de conta completados na nova task; não repetir login por e-mail já verificado |
| ECO-1904 | ECO-2607 | Ciclo de viagens evoluído na nova task; perfil/contatos continuam com aceites próprios |
| ECO-2304/2307 | ECO-2608 | Novo comportamento sem clusters substitui a aceitação visual antiga; nativo não bloqueia Web |
| ECO-2512 | ECO-2610 | Novo catálogo assume aceites de carrossel; homologação final permanece em ECO-2513 |

Bases de segurança (ECO-1401–1404 e ECO-1704), operação editorial efetivamente usada
pela ingestão (ECO-1601–1605) e infraestrutura (ECO-2001–2004) exigem evidência do
subescopo necessário ao consumidor. ECO-2602 deve listar lacuna concreta por ID;
ECO-2603 ajusta a sequência e os contratos antes de liberar implementação. Isso não
autoriza trocar estado PARCIAL por CONCLUÍDA sem prova.

## Mudanças de direcionamento e destino do trabalho anterior

| Mudança | Tasks afetadas | Destino |
|---|---|---|
| Painel completo deixa de bloquear lançamento | ECO-1801–1804 | Pós-evento; APIs/RBAC/guardas usados na carga continuam necessários |
| Sem clusters, com densidade e destaque | ECO-2304/2307, ECO-2512 | Evolução em ECO-2608, sem apagar a implementação anterior |
| Google login e ciclo de viagem explícito | ECO-1902/1904 | ECO-2606/2607; testes atuais não bastam para novos aceites |
| Catálogo por categorias e experiências | ECO-2512 | ECO-2610/2611/2612 |
| Fotos no detalhe; cards condicionais | ECO-2510 | ECO-2613 e opcional ECO-2616; sem espelhamento Google |
| Publicação deixa de ser só Pindobal | ECO-1505, ECO-2202 | Pipeline ECO-2605 e dez aceites individuais ECO-2621–2630 |
| Aprovação do mapa/catálogo antigo não cobre novo design | ECO-2315, ECO-2513 | Reabrir somente gates afetados e homologação final |
| Mobile não bloqueia Web/API | ECO-2102/2103/2204 e partes nativas do mapa | Adiadas; ECO-2104/2205 sem dependência de lojas |
| OSRM self-hosted substituído pelo provedor aceito | ECO-0404, ECO-2313/2314 | Não recontratar; preservar snapshots permitidos até análise ECO-2405 |
| Impacto e selos pessoais removidos | ECO-0206/0606/1101 | ADR 0009; não restaurar ao implementar histórico de viagens |
| Voz/curva a curva e comentários | ECO-2693 / ECO-2692 | Respectivamente fora do escopo e adiados |

Não há exclusão física de documentos/código nesta consolidação. SUBSTITUÍDA não
significa que o código foi descartado ou que a tarefa antiga foi integralmente concluída.

## Cadastro integral

Cada task aparece uma única vez como registro abaixo. As tabelas de ordem acima são
índices, não uma segunda definição de status. **Commit não vinculado** significa que
nesta auditoria não foi estabelecida correspondência exata; não significa ausência
de commits no Git. Responsáveis padrão: desenvolvimento executa, Codex revisa,
owner fornece conteúdo/decisões e autoriza operações sensíveis. Nas tasks de conteúdo,
owner revisa a ficha e desenvolvimento valida/importa. RQ são reconciliações históricas.
Os aceites históricos são referências técnicas; se houver conflito com ADR/decisão
atual, a task ECO-2603 resolve antes de executar. Nenhuma alteração de schema/API é
autorizada simplesmente por estar nesta lista.

Total: **205 registros**, incluindo histórico substituído; não usar como percentual de progresso.

A RECONCILIAR: 2 | ADIADA: 13 | BLOQUEADA: 4 | BLOQUEADA POR DADOS: 9 | CANCELADA NO ESCOPO: 1 | CONCLUÍDA DOCUMENTAL: 13 | CONCLUÍDA LOCAL: 13 | CONCLUÍDA STAGING LIMITADA: 1 | CONDICIONAL: 1 | DECISÃO PENDENTE: 1 | PARCIAL: 47 | PENDENTE: 14 | SUBSTITUÍDA: 86

### Novas tasks para concluir a versão e conteúdo

#### ECO-2601 — Consolidar registro único de tarefas

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Versão do evento / NOVA.
- **Dependências ou sucessoras:** Nenhuma.
- **Conclusão / aceite:** Todos os IDs das cinco fontes e ECO-2005/RQ incluídos, sem duplicatas; decisões desta conversa rastreadas; referências antigas apontam aqui; owner recebeu a consolidação e autorizou commit após revisão.
- **Evidência e limite:** Documento preparado: 205 registros; 170 IDs das cinco fontes cobertos, mais ECO-2005/RQ e novas tasks; sem IDs duplicados/desconhecidos, links locais existentes, grafo das novas tasks sem ciclos e diff sem erros de whitespace. Revisão documental independente realizada e achados de dependências/fonte concorrente tratados. Revisão final e commit local autorizados pelo owner; não comprova funcionalidades do produto.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** commit que introduz este registro (localizável por `git log --grep="docs(tasks): consolidate event release registry"`); hash informado no handoff.

#### ECO-2602 — Identificar baseline funcional e marcos de commit

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2601.
- **Conclusão / aceite:** Revisar Git/diff sem absorver alterações alheias, identificar revisão, conferir tipos/contrato/testes proporcionais; separar artefatos; registrar problemas e commits por incremento após revisão. Produzir por ID a matriz das bases PARCIAIS: requisito já verificado, absorvido por sucessora ou correção que bloqueia consumidor.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2603 — Reconciliar decisões, contratos e pré-requisitos do evento

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2602.
- **Conclusão / aceite:** Atualizar ADRs/spec/aceites afetados: sem clusters/voz, Web, painel adiado, posição versus origem dinâmica, mapa compatível, login Google e mídia. Confirmar datas, assets, callbacks e orçamento R$ 500; separar decisões abertas de autorizadas; nenhum gasto/deploy implícito. Ajustar a sequência com correções de bases indicadas em ECO-2602 e registrar aceites absorvidos pelas sucessoras antes de liberar cada consumidor.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2604 — Padronizar pacote de dados e revisão de cada rota

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2603.
- **Conclusão / aceite:** Template preenchido com Pindobal: ficha, destino, origens, geometria/proveniência, atores, contatos, categorias, tags e mídia/licença/alt; valores ausentes explícitos; instrução utilizável pelo owner/IA.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2605 — Generalizar importação para múltiplas rotas e regiões

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2604, ECO-2005.
- **Conclusão / aceite:** Reusar pipeline existente; dry-run e erros/rejeições claros; segunda carga sem duplicação, preservação de origem, transação/rollback/isolamento testados; sem CSV em runtime e sem IDs Google inventados; carga remota separadamente autorizada.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2606 — Entregar login Google com favoritos preservados

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2603, ECO-1902.
- **Conclusão / aceite:** Login/callback/logout/retorno após refresh, guest→conta e conflito com conta existente respeitam ADR; favoritos preservados no fluxo aceito e isolamento A/B testado; configuração externa homologada antes de concluir.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2607 — Completar ciclo e histórico de viagens

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2606, ECO-1904.
- **Conclusão / aceite:** Iniciar, pausar, retomar e finalizar com transições válidas, persistência após recarregar, isolamento e retry sem duplicação; histórico distingue estados; nenhuma dependência de comentários ou rastreamento contínuo armazenado.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2608 — Exibir pins sem clusters com densidade controlada

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2603, ECO-2304, ECO-2307.
- **Conclusão / aceite:** Sem bolhas numéricas; cor+ícone por categoria, colisões controladas, mais pontos com zoom/filtro e selecionado sempre visível; coordenadas não falsificadas; catálogo conserva acesso aos demais; teclado e toque verificados.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2609 — Simplificar origens e acompanhar posição no mapa

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2603, ECO-2608.
- **Conclusão / aceite:** Seletor compacto, pontos de saída por rota e posição em primeiro plano com consentimento; região distante não produz corredor intermunicipal; falha/negação GPS permite origem fixa; rota não se recalcula só por exibir posição; sem voz/curva a curva.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2610 — Organizar catálogo em carrosséis por categoria

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2603, ECO-2512.
- **Conclusão / aceite:** Seções e cards horizontais, cor coerente com pin, alternativa por teclado, preservar ator/origem/filtros; relevância padrão e opção alfabética; loading/vazio/erro/retry e detalhes reais.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2611 — Criar filtros de experiências com regras editoriais

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2604, ECO-2610.
- **Conclusão / aceite:** Taxonomia inicial e critérios registrados pela equipe, evidência/revisor/data por classificação; tags no pacote e filtros API/UI coerentes; IA sugere sem publicar; combinações e vazio testados.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2612 — Ordenar por relevância e qualidade do cadastro

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2610, ECO-2604.
- **Conclusão / aceite:** Critérios explícitos: pertinência, verificação/completude/atualidade e foto real; desempate estável, sem shuffle; não confundir qualidade cadastral com certificação e não esconder saúde/segurança sem foto; imagem IA não pontua como foto real.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2613 — Completar perfil do ator e fotos Google sob demanda

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2603, ECO-2510.
- **Conclusão / aceite:** Ficha com contatos/localização/serviços/redes verificáveis, ausências honestas; Google consultado ao abrir detalhe, atribuição/link à fonte, timeout/fallback; sem espelhar fotos em Storage; conteúdo principal não espera galeria.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2614 — Aplicar identidade e cards das rotas na Web

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2604, ECO-2610.
- **Conclusão / aceite:** Logo oficial e layout responsivo; todas as rotas publicadas aparecem na inicial/aba, região correta, título legível, capa autorizada ou placeholder honesto; card leva à rota certa; dados não publicados não parecem prontos.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2615 — Medir fluidez, orçamento e recuperação de integrações

- **Estado / horizonte / alteração:** PENDENTE / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2607, ECO-2608, ECO-2609, ECO-2610, ECO-2611, ECO-2612, ECO-2613, ECO-2614, ECO-2630.
- **Conclusão / aceite:** Acordar e medir metas em rede/aparelho definidos (proposta: feedback 200 ms, conteúdo 3 s, mapa 5 s); abertura fria/cache/rede degradada; medir pico separado de 300 visitantes; custos fixos+variáveis+reserva dentro de R$ 500; limites e fallback testados, inclusive tráfego de compartilhamentos.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2616 — Avaliar e habilitar fotos Google nos cards se viável

- **Estado / horizonte / alteração:** CONDICIONAL / Opcional no evento / NOVA.
- **Dependências ou sucessoras:** ECO-2613, ECO-2615.
- **Conclusão / aceite:** Medir custo total/SKU e desempenho com cards visíveis; atribuição compatível; ativação somente se orçamento permitir; caso contrário detalhe sob demanda satisfaz base aceita e registrar adiamento sem bloquear release.
- **Evidência e limite:** Solicitação/decisões do owner nesta conversa; implementação nova não verificada.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2621 — Preparar, importar e verificar rota: Pindobal

- **Estado / horizonte / alteração:** PARCIAL / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Pindobal tem implementação/evidência anterior; adequar ao pacote novo.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2622 — Preparar, importar e verificar rota: Praia do Amor

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2621.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2623 — Preparar, importar e verificar rota: Vila Socorro

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2622.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2624 — Preparar, importar e verificar rota: Ponta de Pedras

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2623.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2625 — Preparar, importar e verificar rota: Eramanai (grafia a confirmar)

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2624.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2626 — Preparar, importar e verificar rota: Altamira 1 — nome a fornecer

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2625.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2627 — Preparar, importar e verificar rota: Altamira 2 — nome a fornecer

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2626.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2628 — Preparar, importar e verificar rota: Altamira 3 — nome a fornecer

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2627.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2629 — Preparar, importar e verificar rota: Altamira 4 — nome a fornecer

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2628.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2630 — Preparar, importar e verificar rota: Altamira 5 — nome a fornecer

- **Estado / horizonte / alteração:** BLOQUEADA POR DADOS / Versão do evento / NOVA.
- **Dependências ou sucessoras:** ECO-2605, ECO-2611, conteúdo e revisão do owner, ECO-2629.
- **Conclusão / aceite:** Ficha/origens/percursos/modos de acesso revisados, atores pertinentes, categorias/tags/mídia/proveniência válidos; dry-run aprovado, carga autorizada em ambiente confirmado e conferência via API/Web. Não exige infraestrutura turística inexistente nem inventa conteúdo.
- **Evidência e limite:** Owner prevê informações até sexta; insumo final e revisão ainda não conferidos.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

### Homologação e publicação Web

#### ECO-2101 — E2E web e auditoria de acessibilidade

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2315, ECO-2513, ECO-2606, ECO-2607, ECO-2615.
- **Conclusão / aceite:** Jornadas do visitante e conta completas em staging; Chrome desktop/Android e Safari iPhone Web; teclado, loading/vazio/erro/retry, favoritos e viagens após recarregar; sem provedores Google reais nos testes automatizados.
- **Evidência e limite:** Playwright local com API/Auth simulados registrado; homologação da jornada real Web pendente.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2104 — Auditoria final de segurança, desempenho e conformidade

- **Estado / horizonte / alteração:** A RECONCILIAR / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2615, ECO-1401, ECO-1402, ECO-1403, ECO-1404, ECO-1704, ECO-2004.
- **Conclusão / aceite:** Segurança/Auth/RLS/Storage e contratos, desempenho, privacidade/licenças, custo e restauração verificados; nenhum P0/P1 aberto; gate Web sem depender das lojas.
- **Evidência e limite:** Auditoria final Web/API não concluída; não herdar aprovação de suites locais.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2201 — Go/no-go e pacote imutável de release

- **Estado / horizonte / alteração:** BLOQUEADA / Lançamento Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2104, ECO-1306.
- **Conclusão / aceite:** Manifesto imutável de código/config/migrations/dados das dez rotas, evidências e rollback revisados; GO humano explícito, sem implantar nesta task.
- **Evidência e limite:** Depende de homologação e GO específico; nenhuma execução de produção comprovada aqui.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2202 — Promoção controlada de migrations e pacote das dez rotas (antes: Pindobal)

- **Estado / horizonte / alteração:** BLOQUEADA / Lançamento Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2201, ECO-1401, ECO-1404.
- **Conclusão / aceite:** Target confirmado, backup/rollback, promoção autorizada, contagens/proveniência das dez rotas e persistência verificadas; não repetir carga sem avaliar estado.
- **Evidência e limite:** Depende de homologação e GO específico; nenhuma execução de produção comprovada aqui.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2203 — Publicação controlada de API e Web em production

- **Estado / horizonte / alteração:** BLOQUEADA / Lançamento Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2202, ECO-2201.
- **Conclusão / aceite:** GO separado; API/Web servem a revisão aprovada, smoke funcional e fallback/rollback verificados; nenhum mock de runtime.
- **Evidência e limite:** Depende de homologação e GO específico; nenhuma execução de produção comprovada aqui.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2205 — Operação assistida, aceite final e handoff

- **Estado / horizonte / alteração:** BLOQUEADA / Lançamento Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2203.
- **Conclusão / aceite:** Janela acordada de operação: monitorar disponibilidade, erros, integridade, custos e compartilhamentos; suporte responsável e nenhum P0/P1 aberto; sem depender de ECO-2204.
- **Evidência e limite:** Depende de homologação e GO específico; nenhuma execução de produção comprovada aqui.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

### Histórico de fundações, integração e operação

#### ECO-1301 — Restabelecer baseline verificável

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** Conforme referência; confirmar antes da execução.
- **Conclusão / aceite:** Reproduzir critérios e evidências da referência no ambiente declarado.
- **Evidência e limite:** Git local presente; fundações implementadas; baseline atual será identificada em ECO-2602.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1302 — ADR do provedor e topologia FastAPI

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** Conforme referência; confirmar antes da execução.
- **Conclusão / aceite:** ADR `Status: aceito`, provedor/região/plano, startup e rollback definidos; `rg -n "Status: aceito/Provedor/Rollback" docs/adr/0005-*.md`.
- **Evidência e limite:** ADR 0005/0006/0007/0008 aceito; decisão documental, sem alegar execução remota.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1303 — ADR de operação editorial, RBAC e publicação

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1301; novo ADR obrigatório..
- **Conclusão / aceite:** tabela papel×ação×recurso e transições válidas/inválidas; `rg -n "admin/editor/reviewer/publisher/draft/published/archived" docs/adr/0006-*.md`.
- **Evidência e limite:** ADR 0005/0006/0007/0008 aceito; decisão documental, sem alegar execução remota.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1304 — ADR de identidade, linking e sessão Web

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1301; complementa ADR 0004..
- **Conclusão / aceite:** diagramas/cenários guest perdido, email existente, refresh/logout/delete; `rg -n "conflito/recuperação/Web/CAPTCHA/exclusão" docs/adr/0007-*.md`.
- **Evidência e limite:** ADR 0005/0006/0007/0008 aceito; decisão documental, sem alegar execução remota.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1305 — ADR de mídia, licença e privacidade

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1301; novo ADR..
- **Conclusão / aceite:** cada classe tem owner, base/licença, visibilidade, TTL, delete e fallback; `rg -n "avatar/editorial/Google/EXIF/alt/licença/órf" docs/adr/0008-*.md`.
- **Evidência e limite:** ADR 0005/0006/0007/0008 aceito; decisão documental, sem alegar execução remota.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1306 — Registro de decisões de lançamento

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2603.
- **Conclusão / aceite:** Datas, identidade, contatos, termos e responsáveis de lançamento Web confirmados; contas de lojas ficam para depois.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1401 — Isolar e verificar Supabase development/test/staging/production

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1306; ADR 0002..
- **Conclusão / aceite:** `python -m scripts.check_test_isolation`; smoke read-only por ambiente autorizado; `npx --yes supabase@<pin> --help`; fingerprints distintos.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1402 — Corrigir e verificar base do Supabase Storage

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1305, ECO-1401; ADR 0008..
- **Conclusão / aceite:** `supabase --help`, `supabase migration --help`, comando oficial de criação; aplicar somente test isolado; matriz usuário A/B/anon; advisors e migration list; upsert exige INSERT+SELECT+UPDATE.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1403 — Implementar RBAC editorial e audit trail

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1303, ECO-1401; ADR 0006..
- **Conclusão / aceite:** pytest de admin/editor/reviewer/publisher/anonymous, revogação e objeto; Ruff/mypy/OpenAPI; migration list/advisors em test.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1404 — Secrets, backups e recuperação por ambiente

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1401, ECO-1302, ECO-1306..
- **Conclusão / aceite:** scanner executável (`gitleaks`/equivalente aprovado), dependency audits; checklist de restore tabletop; comandos descobertos/documentados, não executados contra production.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1501 — Persistência transacional do `seed_pindobal --apply`

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1401, ECO-1403; contrato Pindobal..
- **Conclusão / aceite:** dry-run zero writes; apply controlado; falha induzida deixa zero publicação parcial; `python -m app.ingestion.seed_pindobal --help` e comandos test documentados; pytest/Ruff/mypy.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1502 — Idempotência, proveniência e relatório completo

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1501..
- **Conclusão / aceite:** fixture inclui todos casos do contrato; duas execuções fixture idênticas; `lidos=criados+atualizados+inalterados+rejeitados+candidatos`; pytest ingestion e dry-run snapshot completo quando autorizado.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1503 — Geometrias e associação PostGIS persistentes

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1502..
- **Conclusão / aceite:** 884/777/866 pontos e 45.229/41.452/42.319 km na tolerância; query plans/índices; pytest + smoke PostGIS em test com rollback.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1504 — Carga dupla de Pindobal em test isolado

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1503, ECO-1402; owner autoriza dados descartáveis test..
- **Conclusão / aceite:** comandos exatos do CLI descobertos por `--help`; zero duplicata, zero rejeição silenciosa, regiões/rotas/origens/atores >0, relatórios iguais onde esperado; frontend recebe Pindobal.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1505 — Pacote de promoção Pindobal

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1504, ECO-1303/1305..
- **Conclusão / aceite:** pacote pode ser verificado offline; checksum e schema compatíveis; `Get-FileHash`/equivalente e dry-run reproduzido em test.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1601 — Contrato e autorização da API administrativa

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1403, ECO-1501; ADR 0006..
- **Conclusão / aceite:** OpenAPI lint/drift, generated TS, pytest auth matrix, Ruff/mypy; anonymous e editor errado recebem 403 sem vazar recurso.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1602 — CRUD administrativo de regiões, rotas, origens e geometrias

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1601, ECO-1504..
- **Conclusão / aceite:** happy/401/403/404/409/422, concorrência e audit; pytest, Ruff/mypy/OpenAPI; integração test com rollback.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1603 — CRUD administrativo de categorias, atores e vínculos

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1601, ECO-1504..
- **Conclusão / aceite:** duplicata/chave externa/conflito/permissions; pytest, Ruff/mypy/OpenAPI e integração test.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1604 — Workflow, alertas e reconciliação administrativa

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1602/1603; ADR 0006..
- **Conclusão / aceite:** matriz de transições inválidas, separação de função, publish incompleto 422/409, reconciliação reversível; gates backend/OpenAPI.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1605 — Bulk import, export e jobs administrativos

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1601, ECO-1505, ECO-1604..
- **Conclusão / aceite:** duplicate key retorna mesmo resultado; restart retoma; export reimportável; pytest/concurrency; worker command e health documentados.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1701 — Fluxo real de avatar

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1402, ECO-1305, ECO-1601..
- **Conclusão / aceite:** cancel/invalid/oversize/401/A-B/upload/PATCH/rollback; pytest/Ruff/mypy/OpenAPI/TS/Jest e Storage test isolado.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1702 — Ingestão e processamento de mídia editorial

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1402, ECO-1305, ECO-1601..
- **Conclusão / aceite:** fixtures benignas/mismatch/bomba/dimensões/EXIF; zero rede no CI; pytest/advisors/migration list e artifact metadata.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1703 — Resolução, galeria e lifecycle de mídia

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1701/1702, ECO-1602/1603..
- **Conclusão / aceite:** capa e galeria reais; expired signed URL refresh; delete referenciado bloqueado; job órfão dry-run; backend/frontend gates.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1704 — Matriz real de segurança do Storage

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1701–1703, ECO-1401/1402..
- **Conclusão / aceite:** cada célula allow/deny observada; nenhum listing público indevido; `supabase --help`, migration list/advisors e suite Storage.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1801 — Shell do painel, autenticação e autorização

- **Estado / horizonte / alteração:** PARCIAL / Pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-1601, ECO-1403, ADR 0006..
- **Conclusão / aceite:** anonymous/non-editor bloqueados servidor+UI; revoked session perde acesso; TS/Jest/OpenAPI e teclado/leitor de tela.
- **Evidência e limite:** Painel existe em código, com lacunas; owner retirou sua conclusão do lançamento. APIs/guardas usados pela equipe continuam obrigatórios.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1802 — Editor de regiões, rotas, origens e geometrias

- **Estado / horizonte / alteração:** PARCIAL / Pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-1801, ECO-1602..
- **Conclusão / aceite:** keyboard, screen reader, invalid coord, concurrent edit, retry/offline; TS/Jest/E2E staging futuro.
- **Evidência e limite:** Painel existe em código, com lacunas; owner retirou sua conclusão do lançamento. APIs/guardas usados pela equipe continuam obrigatórios. Editor inspecionado sem fluxo completo de origem/geometria e com região automática; não classificar como concluído.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1803 — Editor de atores, vínculos e mídia

- **Estado / horizonte / alteração:** PARCIAL / Pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-1801, ECO-1603, ECO-1702/1703..
- **Conclusão / aceite:** invalid URL/coord/license/MIME, multi-route, upload fail rollback; TS/Jest/OpenAPI and manual keyboard.
- **Evidência e limite:** Painel existe em código, com lacunas; owner retirou sua conclusão do lançamento. APIs/guardas usados pela equipe continuam obrigatórios.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1804 — Fila de revisão, reconciliação e auditoria

- **Estado / horizonte / alteração:** PARCIAL / Pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-1801–1803, ECO-1604..
- **Conclusão / aceite:** editor não autoaprova quando proibido; candidate retains provenance; audit immutable; TS/Jest/E2E staging.
- **Evidência e limite:** Painel existe em código, com lacunas; owner retirou sua conclusão do lançamento. APIs/guardas usados pela equipe continuam obrigatórios.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1901 — Dados reais, paginação e favoritos consistentes

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1504, ECO-1703..
- **Conclusão / aceite:** >1 página sem duplicação; stale request cancelada; favorites persist/reload/failure; OpenAPI/TS/Jest and staging E2E.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1902 — Cadastro, login, linking e ciclo de sessão

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-1304, ECO-1403..
- **Conclusão / aceite:** guest→account retains data; existing email conflict; refresh concurrency/logout/expired/deleted; TS/Jest, real Auth test staging/test.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação. Login Google novo em ECO-2606; e-mail/senha existente não satisfaz esse aceite.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1903 — Preferências aplicadas e comportamento offline explícito

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1901, ECO-1902..
- **Conclusão / aceite:** cold start prefs; toggle persists/applies immediately; airplane/degraded/timeout/reconnect; TS/Jest and device/web manual.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1904 — Perfil, trips, visitas e contatos

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-1701/1703, ECO-1902, ECO-1303/1306..
- **Conclusão / aceite:** trips/visitas permanecem factuais; visit ownership; consent off=no event; contact validation; backend/frontend full gates/E2E.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação. Pausar/retomar/finalizar e histórico consolidados em ECO-2607; comentários fora desta versão.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-1905 — Expo identity, deep links, env profiles and legal UI

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-1306, ECO-1902–1904; SDK 54 remains..
- **Conclusão / aceite:** Identidade, retorno de login, URLs Web e conteúdo legal funcionando; package/bundle IDs nativos ficam para depois.
- **Evidência e limite:** Reconciliação RQ-01 registrada em nível local; execução remota completa não demonstrada nesta consolidação.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2001 — Runtime de produção e serviço FastAPI no Render (Nativo Python sem Docker)

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** Conforme referência; confirmar antes da execução.
- **Conclusão / aceite:** Reproduzir critérios e evidências da referência no ambiente declarado.
- **Evidência e limite:** RQ-02 registrada como aprovada em LOCAL_TEST (150 testes e linters); comprovação operacional completa continua pendente.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2002 — CI/CD de staging com migration gate

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2001, ECO-1401/1404, ECO-1905..
- **Conclusão / aceite:** workflow dispatch on staging branch; failure prevents deploy; migration drift/advisor blocks; smoke and rollback rehearsal.
- **Evidência e limite:** RQ-02 registrada como aprovada em LOCAL_TEST (150 testes e linters); comprovação operacional completa continua pendente.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2003 — Staging web, HTTPS, domains and CORS

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2002, ECO-1306..
- **Conclusão / aceite:** HTTPS valid, unauthorized origin denied, allowed web works, health/build version visible; browser smoke and curl/Invoke-WebRequest.
- **Evidência e limite:** RQ-02 registrada como aprovada em LOCAL_TEST (150 testes e linters); comprovação operacional completa continua pendente.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2004 — Observability, rate limits, runbooks and cost guards

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2002/2003, ECO-1404, ECO-1605..
- **Conclusão / aceite:** Métricas, limites e runbooks Web/API; custos dentro da parcela aprovada de R$ 500/mês; ensaiar fallback, alertas e recuperação.
- **Evidência e limite:** RQ-02 registrada como aprovada em LOCAL_TEST (150 testes e linters); comprovação operacional completa continua pendente.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2005 — Runner de promoção Pindobal — Fase 2

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-1505, ECO-2002.
- **Conclusão / aceite:** Preflight/guardas, transação, idempotência e rollback reproduzidos; escrita remota exige gate próprio. Generalização em ECO-2605.
- **Evidência e limite:** Handoff de 03/09 registra aprovação local do PR #9; RQ-02 local. Não inferir merge/deploy pelo relato.
- **Referência:** [finalization/ANTIGRAVITY_ECO2005_SUPERVISION.md](finalization/ANTIGRAVITY_ECO2005_SUPERVISION.md). **Commit:** c59c1a3 (referência do handoff; não prova ambiente servido).

### Mapa e catálogo — entregas e pendências

#### ECO-2301 — Decisão de taxonomia visual

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** nenhuma nova.
- **Conclusão / aceite:** ADR 0010 aceito pelo owner (Concluído em 2026-08-24)
- **Evidência e limite:** ADR 0010/0011/0012/0013 aceito; CODE documental.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2302 — Schema e normalização da taxonomia

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2301.
- **Conclusão / aceite:** VERIFIED em 2026-08-24 no Supabase test: 21/21 migrations alinhadas, dry-run final vazio, oito categorias/metadados exatos, remediação auditável e reversível aplicada, testes SQL positivos/negativos aprovados e advisors sem findings
- **Evidência e limite:** Schema versionado; preservar evidência histórica de test, sem inferir estado atual de staging.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2303 — Contrato visual do mapa v2

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2302.
- **Conclusão / aceite:** OpenAPI/backend/tipos sem drift (Concluído em 2026-08-24)
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; isso não comprova toda a versão implantada.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2304 — Pins e legenda no frontend

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2303.
- **Conclusão / aceite:** web verificada; nativo conforme ambiente (Concluído em 2026-08-24)
- **Evidência e limite:** RQ-03: evidência local registrada; homologação de staging da experiência final ainda pendente. Novo comportamento sem clusters em ECO-2608; evidência antiga não o aprova.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2305 — Decisão de camadas espaciais

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2301.
- **Conclusão / aceite:** ADR 0011 aceito pelo owner (Concluído em 2026-08-24)
- **Evidência e limite:** ADR 0010/0011/0012/0013 aceito; CODE documental.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2306 — Backend das camadas estáticas

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2303, ECO-2305.
- **Conclusão / aceite:** VERIFIED em 2026-08-25 no Supabase test: migration forward 20260825003236 aplicada sem editar a migration registrada, 22 versões alinhadas, matriz PostGIS/negativos com rollback aprovada, advisors sem findings e 370 testes backend aprovados
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; isso não comprova toda a versão implantada.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2307 — Interface Rota × Cidade

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2304, ECO-2306.
- **Conclusão / aceite:** câmera/densidade/acessibilidade verificadas (Concluído em 2026-08-24)
- **Evidência e limite:** RQ-03: evidência local registrada; homologação de staging da experiência final ainda pendente. Novo comportamento sem clusters em ECO-2608; evidência antiga não o aprova.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2308 — ADR de origens dinâmicas

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ADR 0003.
- **Conclusão / aceite:** ADR 0012 aceito pelo owner (Concluído em 2026-08-24)
- **Evidência e limite:** ADR 0010/0011/0012/0013 aceito; CODE documental.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2309 — Preview dinâmico com fake

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2308.
- **Conclusão / aceite:** endpoint/contrato/fake sem escrita nem rede (VERIFIED em 2026-08-24)
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; isso não comprova toda a versão implantada.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2310 — Minha localização

- **Estado / horizonte / alteração:** PARCIAL / Condicional nesta versão / CONDICIONAL.
- **Dependências ou sucessoras:** ECO-2309.
- **Conclusão / aceite:** Remediação concluída em 2026-08-26: integração de feature_flags.dynamic_routing via AppContext com fail-closed estrito; ocultação e bloqueio de request de GPS quando flag for false; preservação de fluxo e acessibilidade quando flag for true; 3 origens fixas perenes; Web VERIFIED; Android/iOS mantido PARTIAL por ausência de device físico/emulador
- **Evidência e limite:** RQ-03: evidência local registrada; homologação de staging da experiência final ainda pendente. Origem dinâmica difere de mostrar posição; alternativa predefinida aceita. Decisão em ECO-2603 e integração em ECO-2609.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2311 — Escolher no mapa

- **Estado / horizonte / alteração:** PARCIAL / Condicional nesta versão / CONDICIONAL.
- **Dependências ou sucessoras:** ECO-2309.
- **Conclusão / aceite:** Remediação concluída em 2026-08-26: consumo estrito de feature_flags.dynamic_routing via AppContext e fail-closed; ocultação e bloqueio de "Escolher no mapa" e seleção de origem quando flag for false; preservação integral de seleção interativa, dragend, preview efêmero via TanStack Query memory cache, WCAG (foco, aria-live, teclado web) e 3 origens fixas quando flag for true; fallback com preservação de rota oficial válida em caso de erro/timeout; zero coordenadas em URLs ou persistência; Web VERIFIED; Android/iOS mantido PARTIAL por ausência de device físico/emulador
- **Evidência e limite:** RQ-03: evidência local registrada; homologação de staging da experiência final ainda pendente. Origem dinâmica difere de mostrar posição; alternativa predefinida aceita. Decisão em ECO-2603 e integração em ECO-2609.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2312 — Pins na geometria dinâmica

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2306, ECO-2309.
- **Conclusão / aceite:** VERIFIED em 2026-08-25: isolamento estrito por region_id em find_corridor_actors_by_geometry, semântica canônica de camadas ADR 0011 (route_corridor, citywide_essential, both), ordenação estável e limite STATIC_MAP_MAX_PINS (200), consumo e repasse de pins/legend/city_bounds pelo RouteMapPreview, expansão de mapa com preservação de contexto efêmero via TanStack Query cache, zero persistência em banco e 387 testes backend + 182 testes frontend aprovados
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; isso não comprova toda a versão implantada.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2313 — Benchmark e decisão de provedor

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2308, ECO-2309.
- **Conclusão / aceite:** Gate H3 revisado pelo Owner em 2026-08-25: Google Routes API v2 `ComputeRoutes Essentials` substitui OSRM Self-Hosted; gasto variável pago não autorizado; ADR 0013 aceito (VERIFIED)
- **Evidência e limite:** ADR 0010/0011/0012/0013 aceito; CODE documental.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2314 — Conector real e guardrails

- **Estado / horizonte / alteração:** CONCLUÍDA STAGING LIMITADA / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2313, H3.
- **Conclusão / aceite:** Conector sob limites, falha fechada e evidência local/staging separada; nova chamada só com GO.
- **Evidência e limite:** Status de 05/09 registra 79 testes backend + 12 Jest, live/ready 200 e smoke Google único; flag restaurada false. Commit 2d39005 contém alterações relacionadas, sem equivaler a prova de deploy.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** 2d39005 (parcial relacionado).

#### ECO-2315 — Verificação final

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2608, ECO-2609, ECO-2615, ECO-2630.
- **Conclusão / aceite:** Homologar mapa Web atualizado com dados das dez rotas, seleção/pins/posição/origens, catálogo sincronizado e caminhos de falha; registrar configuração real; DEVICE separado.
- **Evidência e limite:** RQ-03: evidência local registrada; homologação de staging da experiência final ainda pendente.
- **Referência:** [mapa_dinamico/tasks.md](mapa_dinamico/tasks.md). **Commit:** Não vinculado.

#### ECO-2501 — Auditoria reproduzível dos datasets e taxonomias

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** nenhuma nova.
- **Conclusão / aceite:** relatório com hashes, contagens, campos, categorias e lacunas
- **Evidência e limite:** RQ-03 reconcilia implementação local; alegações antigas de homologação total não comprovam staging.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2502 — ADR de autoridade, retenção e publicação das fontes

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2501.
- **Conclusão / aceite:** H25.1: owner/jurídico aceita SEMTUR × editorial × Google
- **Evidência e limite:** ADR 0014/0015/0016 aceito; rever políticas afetadas em ECO-2603 antes de alterar produto.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2503 — ADR de taxonomia hierárquica e camadas espaciais

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2501, ADR 0010/0011.
- **Conclusão / aceite:** H25.2: grupos, tipos, aliases, ícones e escopos aceitos
- **Evidência e limite:** ADR 0014/0015/0016 aceito; rever políticas afetadas em ECO-2603 antes de alterar produto.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2504 — Schema, contratos de proveniência e taxonomia

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2502, ECO-2503.
- **Conclusão / aceite:** migrations/test alinhados, RLS/grants/advisors verdes
- **Evidência e limite:** RQ-03 reconcilia implementação local; alegações antigas de homologação total não comprovam staging.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2505 — Importação integral e idempotente da SEMTUR

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2504.
- **Conclusão / aceite:** `VERIFIED` — 674 lidos e contabilizados; raw, refs, proveniência e tipologia nível-2 preservados
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; revalidar caminho remoto aplicável ao novo release.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2506 — Associação espacial e calibração por origem

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2505.
- **Conclusão / aceite:** `VERIFIED` — relatório 0,5/1/2/3 km e vínculos PostGIS aceitos por origem (312 Porto, 156 Aeroporto, 209 Rodoviária)
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; revalidar caminho remoto aplicável ao novo release.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2507 — ADR Google Maps/Places, mídia, custo e atribuição

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2501, ECO-2502.
- **Conclusão / aceite:** `VERIFIED` — ADR 0016 aceito pelo Owner; Gate H25.3 concluído com sucesso
- **Evidência e limite:** ADR 0014/0015/0016 aceito; rever políticas afetadas em ECO-2603 antes de alterar produto.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2508 — Conector Places API (New) e guardrails

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2507.
- **Conclusão / aceite:** `VERIFIED` — conector seguro, mocks/fixtures contratuais completos, feature flag `FEATURE_GOOGLE_PLACES_SYNC=false`, circuit breaker, cost guard e 0 rede no CI
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; revalidar caminho remoto aplicável ao novo release.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2509 — Matching SEMTUR ↔ Google e fila editorial

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2505, ECO-2508.
- **Conclusão / aceite:** `VERIFIED` — matching determinístico em camadas, fuzzy enfileirado sem auto-merge, proveniência e decisões auditáveis/reversíveis
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; revalidar caminho remoto aplicável ao novo release.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2510 — Fotos Google por proxy e atribuições

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2508, ECO-2509.
- **Conclusão / aceite:** `VERIFIED` — expiração, autoria, Google Maps URI e fallback verificados
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; revalidar caminho remoto aplicável ao novo release.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2511 — API de catálogo/mapa e selo de origem

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Base da versão Web / PRESERVADA.
- **Dependências ou sucessoras:** ECO-2506, ECO-2509, ECO-2510.
- **Conclusão / aceite:** `VERIFIED` — OpenAPI/tipos sem drift e payload proporcional
- **Evidência e limite:** RQ-03 registra LOCAL_TEST; revalidar caminho remoto aplicável ao novo release.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2512 — Pins, filtros, cards, selo SEMTUR e galeria

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2511.
- **Conclusão / aceite:** Pins/cards/galeria, acessibilidade e estados remotos verificados por plataforma; mudanças da versão pelas sucessoras.
- **Evidência e limite:** WEB_LOCAL registrado; carrosséis/ordenação/tags novos em ECO-2610/2611/2612, sem aprovação nativa.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

#### ECO-2513 — Homologação final e decisão de promoção

- **Estado / horizonte / alteração:** PARCIAL / Base da versão Web / EDITADA.
- **Dependências ou sucessoras:** ECO-2610, ECO-2611, ECO-2612, ECO-2613, ECO-2630.
- **Conclusão / aceite:** Homologar catálogo real das dez rotas, vínculos, filtros, mídia, contatos e ordenação; proveniência e atribuição corretas; sem aprovar apenas mocks.
- **Evidência e limite:** RQ-03 reconcilia implementação local; alegações antigas de homologação total não comprovam staging.
- **Referência:** [catalogo_territorial/tasks.md](catalogo_territorial/tasks.md). **Commit:** Não vinculado.

### Manutenção, mobile e evoluções posteriores

#### ECO-2102 — E2E Android, acessibilidade e rede degradada

- **Estado / horizonte / alteração:** ADIADA / Mobile depois da Web / ADIADA.
- **Dependências ou sucessoras:** ECO-2002/2004, ECO-2101 e perfil EAS aprovado..
- **Conclusão / aceite:** execução reproduzível em API Android mínima e atual definidas; foco/labels/ordem corretos; sem perda/corrupção após reconexão; crash-free; comando oficial `npm run e2e:android` ou equivalente documentado.
- **Evidência e limite:** MOBILE_LATER; testes simulados não equivalem a DEVICE.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2103 — E2E iOS, acessibilidade e links universais

- **Estado / horizonte / alteração:** ADIADA / Mobile depois da Web / ADIADA.
- **Dependências ou sucessoras:** ECO-2002/2004, ECO-2101 e conta/perfil Apple aprovados..
- **Conclusão / aceite:** matriz mínima/atual aprovada passa; links abrem contexto correto; nenhuma barreira crítica de VoiceOver; crash-free; comando oficial E2E e build ID documentados.
- **Evidência e limite:** MOBILE_LATER; testes simulados não equivalem a DEVICE.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2204 — Publicação controlada Android e iOS

- **Estado / horizonte / alteração:** ADIADA / Mobile depois da Web / ADIADA.
- **Dependências ou sucessoras:** Gate 7 `VERIFIED`, artefatos ECO-2201, contas e metadados de lojas aprovados..
- **Conclusão / aceite:** builds iguais ao manifesto; stores aceitam metadados; instalação/upgrade/smoke passam; rollout pode ser pausado; status por loja registrado.
- **Evidência e limite:** MOBILE_LATER; testes simulados não equivalem a DEVICE.
- **Referência:** [finalization/tasks.md](finalization/tasks.md). **Commit:** Não vinculado.

#### ECO-2401 — Baseline protegida e inventário rastreável

- **Estado / horizonte / alteração:** A RECONCILIAR / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** autorização do owner.
- **Conclusão / aceite:** H24.1 verificado; nenhuma alteração perdida
- **Evidência e limite:** Baseline não presumida; mínimo necessário à versão em ECO-2602.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2402 — Fonte única de status e backlog aberto

- **Estado / horizonte / alteração:** CONCLUÍDA DOCUMENTAL / Manutenção pós-evento / ESTENDIDA.
- **Dependências ou sucessoras:** ECO-2401.
- **Conclusão / aceite:** contradições identificadas; status atual aprovado
- **Evidência e limite:** Consolidação anterior registrada; inventário completo desta conversa é ECO-2601.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2403 — Planos concluídos arquivados com índices

- **Estado / horizonte / alteração:** ADIADA / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-2402, H24.2.
- **Conclusão / aceite:** links válidos; histórico preservado
- **Evidência e limite:** Backlog de manutenção preservado; não executar remoções sem matriz/aprovação.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2404 — Política de artefatos gerados e evidências

- **Estado / horizonte / alteração:** PARCIAL / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-2401.
- **Conclusão / aceite:** outputs regeneráveis ignorados; evidências selecionadas mantidas
- **Evidência e limite:** Saídas Playwright isoladas, mas artefatos ainda aparecem no Git; tratamento mínimo em ECO-2602, política ampla posterior.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2405 — Legado OSRM/runtime e arquivos órfãos tratados

- **Estado / horizonte / alteração:** ADIADA / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-2402, H24.2, H24.3.
- **Conclusão / aceite:** nenhum consumidor; regressão verde; snapshots preservados
- **Evidência e limite:** Backlog de manutenção preservado; não executar remoções sem matriz/aprovação.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2406 — Configuração de deploy e wrappers redundantes consolidados

- **Estado / horizonte / alteração:** ADIADA / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-2402, H24.2.
- **Conclusão / aceite:** Render/Vercel/CI coerentes e smoke aplicável verde
- **Evidência e limite:** Backlog de manutenção preservado; não executar remoções sem matriz/aprovação.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2407 — Assets duplicados governados por origem e checksum

- **Estado / horizonte / alteração:** ADIADA / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-2402, H24.2.
- **Conclusão / aceite:** builds independentes preservados; nenhuma imagem quebrada
- **Evidência e limite:** Backlog de manutenção preservado; não executar remoções sem matriz/aprovação.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2408 — Checks automáticos de saúde implementados

- **Estado / horizonte / alteração:** ADIADA / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-2403–ECO-2407 aplicáveis.
- **Conclusão / aceite:** comando único local e CI sem falsos positivos críticos
- **Evidência e limite:** Backlog de manutenção preservado; não executar remoções sem matriz/aprovação.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2409 — Fronteiras arquiteturais protegidas por testes

- **Estado / horizonte / alteração:** ADIADA / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-2408.
- **Conclusão / aceite:** violações intencionais falham; suíte normal passa
- **Evidência e limite:** Backlog de manutenção preservado; não executar remoções sem matriz/aprovação.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2410 — Auditoria final e handoff de manutenção

- **Estado / horizonte / alteração:** ADIADA / Manutenção pós-evento / ADIADA.
- **Dependências ou sucessoras:** ECO-2401–ECO-2409.
- **Conclusão / aceite:** verificação independente e backlog residual explícito
- **Evidência e limite:** Backlog de manutenção preservado; não executar remoções sem matriz/aprovação.
- **Referência:** [repository_health/tasks.md](repository_health/tasks.md). **Commit:** Não vinculado.

#### ECO-2691 — Postagens sociais incorporadas com curadoria

- **Estado / horizonte / alteração:** ADIADA / Futuro/opcional / NOVA.
- **Dependências ou sucessoras:** Nova priorização do owner.
- **Conclusão / aceite:** Avaliar embed oficial por plataforma, direitos/privacidade, remoção e performance; links e mídia autorizada podem atender antes; não bloquear evento.
- **Evidência e limite:** Pedido/sugestão desta conversa; nenhuma implementação autorizada por esta linha.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2692 — Comentários e conteúdo enviado por usuários

- **Estado / horizonte / alteração:** ADIADA / Futuro/opcional / NOVA.
- **Dependências ou sucessoras:** Nova priorização do owner.
- **Conclusão / aceite:** Definir moderação, autorização, privacidade e aceites antes de implementar; owner excluiu da primeira versão.
- **Evidência e limite:** Pedido/sugestão desta conversa; nenhuma implementação autorizada por esta linha.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2693 — Voz e orientação curva a curva

- **Estado / horizonte / alteração:** CANCELADA NO ESCOPO / Futuro/opcional / RETIRADA.
- **Dependências ou sucessoras:** Nova priorização do owner.
- **Conclusão / aceite:** Owner confirmou que não deseja essa experiência para a versão; não iniciar nem considerar dívida obrigatória. Só reabrir com nova demanda.
- **Evidência e limite:** Pedido/sugestão desta conversa; nenhuma implementação autorizada por esta linha.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2694 — Gestão de perfis Google Business Profile autorizados

- **Estado / horizonte / alteração:** ADIADA / Futuro/opcional / NOVA.
- **Dependências ou sucessoras:** Nova priorização do owner.
- **Conclusão / aceite:** Somente perfis autorizados de parceiros; não usar como catálogo público geral; contratos/permissões e benefício devem justificar implementação.
- **Evidência e limite:** Pedido/sugestão desta conversa; nenhuma implementação autorizada por esta linha.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

#### ECO-2695 — Definir política de ilustrações IA nos cadastros

- **Estado / horizonte / alteração:** DECISÃO PENDENTE / Futuro/opcional / NOVA.
- **Dependências ou sucessoras:** Nova priorização do owner.
- **Conclusão / aceite:** Aprovar ou rejeitar uso identificado como ilustração, sem representar fachada/produtos inventados como foto real e sem bônus de foto real. Fallback neutro permite lançar sem esta decisão.
- **Evidência e limite:** Pedido/sugestão desta conversa; nenhuma implementação autorizada por esta linha.
- **Referência:** [direcionamento_versao_web_evento.md](direcionamento_versao_web_evento.md). **Commit:** Não vinculado.

### Reconciliações já registradas

#### RQ-01 — Reconciliação ECO-13xx–19xx

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Histórico / PRESERVADA.
- **Dependências ou sucessoras:** Nenhuma execução nova.
- **Conclusão / aceite:** Reconciliação histórica preservada; não transfere aprovação a novos requisitos.
- **Evidência e limite:** Aprovação anterior registrada em project_status; CODE/LOCAL_TEST; sem handoff individual localizado nesta consolidação.
- **Referência:** [project_status.md](project_status.md). **Commit:** Não vinculado.

#### RQ-02 — Reconciliação ECO-2001–2005

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Histórico / PRESERVADA.
- **Dependências ou sucessoras:** Nenhuma execução nova.
- **Conclusão / aceite:** Reconciliação histórica preservada; não transfere aprovação a novos requisitos.
- **Evidência e limite:** Aprovação anterior registrada: 150 testes, Ruff/mypy; escopo local, não homologação completa de staging.
- **Referência:** [project_status.md](project_status.md). **Commit:** Não vinculado.

#### RQ-03 — Reconciliação mapa e catálogo Web

- **Estado / horizonte / alteração:** CONCLUÍDA LOCAL / Histórico / PRESERVADA.
- **Dependências ou sucessoras:** Nenhuma execução nova.
- **Conclusão / aceite:** Reconciliação histórica preservada; não transfere aprovação a novos requisitos.
- **Evidência e limite:** Relatório RQ-03 registra 635 pytest, 219 Jest e Playwright 4/4; status posterior cita 660/240. Snapshots diferentes, não reexecutados nesta sessão.
- **Referência:** [registro de evidências desta consolidação](project_status.md). **Commit:** Não vinculado.

### Integração original — IDs substituídos e sucessores

#### ECO-0001 — Congelar baseline funcional

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1302, ECO-1303, ECO-1304, ECO-1305, ECO-1306.
- **Conclusão / aceite:** baseline reproduzível e falhas conhecidas registradas.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0002 — Resolver versão do Expo

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1302, ECO-1303, ECO-1304, ECO-1305, ECO-1306.
- **Conclusão / aceite:** versão e documentação normativa registradas.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0003 — Aprovar decisões de produto pendentes

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1302, ECO-1303, ECO-1304, ECO-1305, ECO-1306.
- **Conclusão / aceite:** ADRs curtos adicionados à spec.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0004 — Congelar contrato OpenAPI v1

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1302, ECO-1303, ECO-1304, ECO-1305, ECO-1306.
- **Conclusão / aceite:** arquivo OpenAPI validado e revisado pelo frontend.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0101 — Criar projeto FastAPI

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1401, ECO-1402, ECO-1403, ECO-2001.
- **Conclusão / aceite:** servidor inicia localmente e documentação `/docs` responde.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0102 — Provisionar projetos Supabase

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1401, ECO-1402, ECO-1403, ECO-2001.
- **Conclusão / aceite:** consulta de smoke test cria/consulta `Point` e `LineString`; nenhuma credencial de produção está disponível no ambiente de IA.
- **Evidência e limite:** Checkbox antigo aberto; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0103 — Configurar SQLAlchemy e migrations Supabase

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1401, ECO-1402, ECO-1403, ECO-2001.
- **Conclusão / aceite:** schema vazio recebe todas as migrations em ordem; lista de migrations remota coincide com o repositório.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0104 — Configurar qualidade e testes

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1401, ECO-1402, ECO-1403, ECO-2001.
- **Conclusão / aceite:** CI local verde com teste mínimo.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0105 — Configurar erros, CORS e request ID

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1401, ECO-1402, ECO-1403, ECO-2001.
- **Conclusão / aceite:** erros 4xx/5xx não vazam detalhes internos.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0106 — Criar `.env.example` e política de segredos

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1401, ECO-1402, ECO-1403, ECO-2001.
- **Conclusão / aceite:** nenhum segredo real versionado; scanner de segredos no CI.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0107 — Configurar segurança base do Supabase

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1301, ECO-1401, ECO-1402, ECO-1403, ECO-2001.
- **Conclusão / aceite:** tabelas novas não ficam acessíveis por `anon`/`authenticated` sem decisão explícita e teste negativo.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0201 — Modelar regiões, rotas, origens e geometrias

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1403, ECO-1602, ECO-1603, ECO-1702.
- **Conclusão / aceite:** constraints impedem origem duplicada e geometria inválida.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0202 — Modelar atores, categorias e acessibilidade

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1403, ECO-1602, ECO-1603, ECO-1702.
- **Conclusão / aceite:** ator pode pertencer a várias rotas sem duplicação.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0203 — Modelar alertas e mídia

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1403, ECO-1602, ECO-1603, ECO-1702.
- **Conclusão / aceite:** consulta de alertas ativos respeita janela temporal.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0204 — Modelar proveniência e ingestão

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1403, ECO-1602, ECO-1603, ECO-1702.
- **Conclusão / aceite:** cada ator importado aponta para ao menos uma fonte.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0205 — Modelar usuário, preferências e favoritos

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1403, ECO-1602, ECO-1603, ECO-1702.
- **Conclusão / aceite:** favoritos são isolados por usuário e idempotentes.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0206 — Modelar viagens, visitas e selos

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1403, ECO-1602, ECO-1603, ECO-1702.
- **Conclusão / aceite:** métricas podem ser recalculadas a partir dos eventos persistidos.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução. Impacto/selos pessoais retirados pelo ADR 0009.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0207 — Implementar e testar RLS/policies

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1403, ECO-1602, ECO-1603, ECO-1702.
- **Conclusão / aceite:** matriz `anon`, usuário A, usuário B e backend cobre SELECT/INSERT/UPDATE/DELETE e prova ausência de acesso cruzado.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0301 — Inventariar e hashear fontes

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1501, ECO-1502, ECO-1503, ECO-2505, ECO-2509.
- **Conclusão / aceite:** importação detecta alteração não aprovada da fonte.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0302 — Criar importador OSRM

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1501, ECO-1502, ECO-1503, ECO-2505, ECO-2509.
- **Conclusão / aceite:** Porto 45,229 km; Aeroporto 41,452 km; Rodoviária 42,319 km dentro da tolerância definida.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0303 — Criar importador SEMTUR

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1501, ECO-1502, ECO-1503, ECO-2505, ECO-2509.
- **Conclusão / aceite:** relatório soma 674 registros entre importados, rejeitados e candidatos.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0304 — Criar importador do recorte Pindobal

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1501, ECO-1502, ECO-1503, ECO-2505, ECO-2509.
- **Conclusão / aceite:** nenhuma coordenada válida é silenciosamente descartada.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0305 — Importar snapshot Google legado

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1501, ECO-1502, ECO-1503, ECO-2505, ECO-2509.
- **Conclusão / aceite:** relatório soma 737 registros e identifica os que não têm ID externo persistível.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0306 — Implementar reconciliação SEMTUR × Google

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1501, ECO-1502, ECO-1503, ECO-2505, ECO-2509.
- **Conclusão / aceite:** casos ambíguos entram em fila, sem merge destrutivo.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0307 — Relacionar atores às geometrias com PostGIS

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1501, ECO-1502, ECO-1503, ECO-2505, ECO-2509.
- **Conclusão / aceite:** amostra comparada aos CSVs e tolerância documentada.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0308 — Criar seed publicável de Pindobal

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1501, ECO-1502, ECO-1503, ECO-2505, ECO-2509.
- **Conclusão / aceite:** duas execuções produzem o mesmo estado e contagens.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0401 — Implementar cliente Google Places (New)

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2508, ECO-2510, ECO-2314.
- **Conclusão / aceite:** testes usam servidor simulado; nenhuma chamada externa no CI.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0402 — Corrigir persistência de Place ID

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2508, ECO-2510, ECO-2314.
- **Conclusão / aceite:** nova ingestão preserva o ID do fornecedor ponta a ponta.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0403 — Criar job incremental de atualização de POIs

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2508, ECO-2510, ECO-2314.
- **Conclusão / aceite:** falha parcial pode retomar sem duplicar registros.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0404 — Implementar `OsrmConnector`

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2313, ECO-2314; snapshots existentes preservados.
- **Conclusão / aceite:** contrato não expõe detalhes específicos do fornecedor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0405 — Preparar conector Google Business Profile

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2694.
- **Conclusão / aceite:** feature flag desligada até aprovação do Google e do estabelecimento.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0406 — Implementar Supabase Storage

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2508, ECO-2510, ECO-2314.
- **Conclusão / aceite:** avatar e imagem editorial funcionam usando publishable key/JWT ou URL assinada, sem expor secret/service key.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0501 — Implementar regiões e bootstrap

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2511.
- **Conclusão / aceite:** região ativa inválida recebe fallback explícito.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0502 — Implementar lista de rotas

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2511.
- **Conclusão / aceite:** combinações `q`, `saved` e `verified` testadas.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0503 — Implementar detalhe de rota

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2511.
- **Conclusão / aceite:** 404 padronizado e sem fallback silencioso para outra rota.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0504 — Implementar geometria e mapa

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2511.
- **Conclusão / aceite:** resposta é enxuta e coordenadas são válidas.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0505 — Implementar alertas

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2511.
- **Conclusão / aceite:** severidade `info`, `warning`, `critical` preservada.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0506 — Implementar catálogo e detalhe de ator

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2511.
- **Conclusão / aceite:** ator inexistente retorna 404; dados Google têm atribuição/proveniência apropriada.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0601 — Implementar anonymous sign-in do Supabase

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1902, ECO-1904, ECO-2606, ECO-2607.
- **Conclusão / aceite:** ownership por `auth.uid()` funciona; reinstalação, logout e expiração têm comportamento documentado.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0602 — Integrar Supabase Auth e validação no FastAPI

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1902, ECO-1904, ECO-2606, ECO-2607.
- **Conclusão / aceite:** testes de token ausente, inválido, expirado, usuário A/B, refresh concorrente, vínculo e logout.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0603 — Implementar perfil e avatar

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1902, ECO-1904, ECO-2606, ECO-2607.
- **Conclusão / aceite:** validação de arquivo, policy de ownership e rollback de upload falho.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0604 — Implementar preferências

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1902, ECO-1904, ECO-2606, ECO-2607.
- **Conclusão / aceite:** PATCH parcial e restauração no bootstrap.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0605 — Implementar favoritos idempotentes

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1902, ECO-1904, ECO-2606, ECO-2607.
- **Conclusão / aceite:** testes concorrentes e isolamento por usuário.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0606 — Implementar viagens, visitas e impacto

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1902, ECO-1904, ECO-2606, ECO-2607.
- **Conclusão / aceite:** números do perfil derivam do servidor, não de constantes.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução. Impacto/selos pessoais retirados pelo ADR 0009.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0607 — Implementar conteúdo de suporte

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1902, ECO-1904, ECO-2606, ECO-2607.
- **Conclusão / aceite:** links e contatos são validados e atualizáveis sem nova versão do app.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0701 — Criar client HTTP tipado

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-1903, ECO-2101.
- **Conclusão / aceite:** nenhum componente chama `fetch` diretamente.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0702 — Gerar/sincronizar tipos do OpenAPI

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-1903, ECO-2101.
- **Conclusão / aceite:** CI detecta quebra de contrato.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0703 — Configurar cache de servidor

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-1903, ECO-2101.
- **Conclusão / aceite:** troca de região não mistura resultados.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0704 — Refatorar AppContext

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-1903, ECO-2101.
- **Conclusão / aceite:** `mockData.ts` não participa de runtime fora de story/teste.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0705 — Implementar estados padrão

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-1903, ECO-2101.
- **Conclusão / aceite:** componentes são acessíveis e reutilizados nas seis telas.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0706 — Armazenar tokens com segurança

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-1903, ECO-2101.
- **Conclusão / aceite:** access/refresh token não aparece em logs nem armazenamento inseguro; restauração e logout funcionam.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0801 — Implementar bootstrap do aplicativo

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2614.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0802 — Implementar seletor global de região

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2614.
- **Conclusão / aceite:** escolha persiste e invalida consultas corretas.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0803 — Integrar homepage

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2614.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0804 — Integrar tela de rotas

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2614.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0805 — Implementar favorito otimista de rota

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1901, ECO-2614.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0901 — Integrar detalhe de rota

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2304, ECO-2307, ECO-2315, ECO-2608, ECO-2609.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0902 — Integrar simulador de origem

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2304, ECO-2307, ECO-2315, ECO-2608, ECO-2609.
- **Conclusão / aceite:** Porto/Aeroporto/Rodoviária exibem seus valores reais.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0903 — Implementar MapAdapter real

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2304, ECO-2307, ECO-2315, ECO-2608, ECO-2609.
- **Conclusão / aceite:** linha, bounds e pins da Pindobal são visualmente verificados.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0904 — Ativar zoom e câmera

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2304, ECO-2307, ECO-2315, ECO-2608, ECO-2609.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0905 — Integrar pins, filtros e bottom sheet

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2304, ECO-2307, ECO-2315, ECO-2608, ECO-2609.
- **Conclusão / aceite:** filtros não escondem o pin selecionado de modo inconsistente.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0906 — Preservar ator/origem na navegação

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2304, ECO-2307, ECO-2315, ECO-2608, ECO-2609.
- **Conclusão / aceite:** preview → mapa → catálogo mantém contexto e foco.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-0907 — Corrigir retry da rota não encontrada/erro

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2304, ECO-2307, ECO-2315, ECO-2608, ECO-2609.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1001 — Integrar catálogo

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2512, ECO-2610, ECO-2613.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1002 — Criar tela endereçável de ator

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2512, ECO-2610, ECO-2613.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1003 — Tornar ActorCard funcional

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2512, ECO-2610, ECO-2613.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1004 — Implementar favorito otimista de ator

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2512, ECO-2610, ECO-2613.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1005 — Implementar contatos externos

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2512, ECO-2610, ECO-2613.
- **Conclusão / aceite:** esquemas inválidos são bloqueados e erro é compreensível.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1101 — Integrar perfil e impacto

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1903, ECO-1904, ECO-2607.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução. Impacto/selos pessoais retirados pelo ADR 0009.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1102 — Criar tela de rotas salvas

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1903, ECO-1904, ECO-2607.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1103 — Criar tela de atores favoritos

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1903, ECO-1904, ECO-2607.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1104 — Criar histórico de viagens e visitas

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1903, ECO-1904, ECO-2607.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1105 — Criar preferências de acessibilidade

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1903, ECO-1904, ECO-2607.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1106 — Integrar configurações regionais

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1903, ECO-1904, ECO-2607.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1107 — Criar suporte e operação editorial

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1903, ECO-1904, ECO-2607.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1108 — Auditar falsos botões do perfil

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-1903, ECO-1904, ECO-2607.
- **Conclusão / aceite:** todos navegam/executam ação ou deixam de ter semântica interativa.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1201 — Testes E2E dos fluxos críticos

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1202 — Auditoria de acessibilidade

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1203 — Testes de rede degradada/offline

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1204 — Revisão de segurança e LGPD

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1205 — Revisão das políticas Google e atribuições

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1206 — Observabilidade e orçamento

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1207 — Pipeline CI/CD e ambientes

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1208 — Carga e desempenho

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** Aceite histórico preservado na referência; execução transferida ao sucessor.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1209 — Homologação da matriz de telas

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** evidência em Android, iOS e web conforme escopo aprovado; nenhuma interação incompleta.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

#### ECO-1210 — Remover mocks de produção e publicar

- **Estado / horizonte / alteração:** SUBSTITUÍDA / Histórico / SUBSTITUÍDA.
- **Dependências ou sucessoras:** ECO-2101, ECO-2104, ECO-2203.
- **Conclusão / aceite:** build de produção não contém fallback silencioso para dados fictícios.
- **Evidência e limite:** Checkbox antigo marcado; não comprova execução.
- **Referência:** [archive/planning/2026-08-12/backend_integration_tasks.md](archive/planning/2026-08-12/backend_integration_tasks.md). **Commit:** Não vinculado.

## Evidências preservadas e limites desta consolidação

- O status anterior registrava RQ-01/RQ-02/RQ-03 aprovadas localmente; isso foi
  preservado. Não se converteu uma reconciliação agregada em aprovação individual
  de cada ambiente/tarefa. Não foram executados testes de produto ou acessos remotos
  nesta edição documental.
- O arquivo local `docs/relatorio_reconciliacao_rq03.md` foi lido como evidência
  complementar, mas não integra este commit; sua existência em outra cópia não é
  presumida. O resumo necessário ao acompanhamento foi preservado neste documento.
- RQ-03 tem snapshots de 635/660 pytest, 219/240 Jest e 95/124 arquivos mypy em
  documentos de momentos distintos. A quantidade não é prova de revisão idêntica;
  baseline/artefato e comandos precisam acompanhar futuras entregas.
- ECO-2314 tem registro de smoke Google único aprovado e flag restaurada false.
  Isso não significa origem dinâmica habilitada nem rotas Google desenhadas no Leaflet.
- Código de painel existente foi inspecionado em sessão anterior; lacunas não
  desapareceram por adiá-lo. O fluxo de ingestão da equipe deve preservar controle
  editorial e autorização mesmo sem painel completo.
- Documentos antigos contêm frases como ausência de Git/backend/painel e checklists
  de lojas/Docker incompatíveis com decisões mais recentes. São snapshots históricos,
  não instruções para reconstruir o projeto ou bloquear a Web indevidamente.
- A revisão local desta conversa aprovou typecheck e openapi:check na inspeção anterior;
  isso não prova segurança, carga das dez rotas nem desempenho remoto desta nova versão.

## Como atualizar este documento após cada task

1. Atualizar o registro pelo ID, sem copiá-lo para outro backlog.
2. Registrar resultado, plataforma/ambiente, revisão, comando/evidência e limitações.
3. Marcar conclusão somente no nível comprovado; separar reabertura por novo requisito.
4. Registrar o hash do commit funcional após revisão e autorização aplicável. Nunca
   usar commit como substituto de teste nem fazer commit de artefatos/segredos por arrasto.
5. Atualizar a próxima task da ordem; abrir correção vinculada se houver bloqueador.
6. Datas/owner/GO de operação remota são específicos; não presumir autorização por
   orçamento, credencial disponível ou aprovação de documentação.

Orientações complementares: [briefing do evento](direcionamento_versao_web_evento.md),
[spec](backend_integration_spec.md), [aceites](acceptance_criteria.md),
[playbook](ai_task_playbook.md), [fluxo diário](ai/README.md) e ADRs em `adr/`.
O briefing explica decisões, não mantém uma fila concorrente.
