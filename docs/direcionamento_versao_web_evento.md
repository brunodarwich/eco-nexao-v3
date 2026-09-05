# Direcionamento da versão Web para testes e evento

Data: 2026-09-05.
Estado: requisitos e decisões complementares registrados; tasks consolidadas e
revisadas em project_status.md. Reconciliação de ADRs/contratos pendente na ECO-2603.
Este documento é um briefing de produto, não um segundo backlog ativo.
`project_status.md` é a fonte única de ordem e estado das tasks.

## Objetivo e prazo

Entregar uma versão Web utilizável por equipe, parceiros e primeiros usuários em uma
semana, preparando o evento informado para aproximadamente quinze dias. Confirmar
datas exatas; não transformar esta janela em promessa de conclusão sem gates.
Teto informado: R$ 500/mês para o projeto, buscando gastar menos. Público do evento:
aproximadamente 300 pessoas, seguido de acessos por compartilhamentos, sem teto de
visitantes conhecido. Isso não equivale a 300 usuários simultâneos. O orçamento não
autoriza contratação, deploy, migration ou escrita remota.

## Requisitos confirmados pelo owner

- Web primeiro, inclusive navegador de celular; nativo depois.
- Rotas confiáveis, mapa e navegação fluidos, sem demora excessiva nas informações.
- Pins bonitos e distinguíveis, sem agrupamentos numéricos (clusters) e sem poluição.
- Logo ECOnexão no topo e cards das rotas na inicial e na aba Rotas.
- Seletor de origem compacto; origens dependem do destino (porto, centro, aeroporto,
  rodoviária etc.). Minha localização e escolha no mapa são desejadas, mas o owner
  aceita limitar a origens predefinidas se necessário.
- Atores com dados públicos verificáveis: localização, contatos, serviços/produtos,
  redes sociais e imagens quando disponíveis e permitidos. Ausência não autoriza IA
  a inventar conteúdo nem indica que a API Google ofereça todos esses campos.
- Catálogo em seções por categoria, com cards deslizáveis horizontalmente; cores
  coerentes entre categoria, pin e card. Cores específicas ainda não aprovadas:
  alimentação vermelha foi apenas exemplo.
- Filtros por experiência, como pôr do sol, domingo em família e trilha ecológica,
  além das categorias de atividade.
- Login Google, favoritos e histórico de viagens; iniciar, pausar e encerrar.
  Retomar é dependência funcional proposta para a pausa, a confirmar nos aceites.
- Comentários, conteúdo enviado pelo público, painel administrativo completo e apps
  nativos ficam para depois desta entrega. Preservar o código administrativo existente.
- Inserção inicial feita pela equipe/desenvolvedores com auxílio da IA.
- Commits locais em marcos importantes após comprovação de funcionamento.

## Conteúdo pretendido

Santarém/entorno: Pindobal como referência, Praia do Amor, Vila Socorro, Ponta de
Pedras e Eramanai (confirmar grafia, coordenadas e identidade editorial).
Altamira: cinco rotas ainda a definir. Owner se comprometeu a entregar informações
das dez rotas até sexta-feira (data absoluta a confirmar; na data desta nota, a
próxima sexta é 11/09/2026). A programação deve avançar antes dessa entrega, usando
Pindobal e fixtures representativas. A homologação das dez rotas depende da carga
real e revisão posterior. Não publicar cards com aparência de rota pronta sem dados.
Owner informa possuir localizações e inventário turístico de Santarém; disponibilidade,
licença, atualidade e adequação de cada campo ainda serão verificadas.

## Decisões de produto e recomendações de implementação

As aprovações abaixo foram dadas pelo owner em comentários a este direcionamento.
Sugestões de implementação permanecem propostas quando não explicitamente aprovadas.
ADRs/contratos afetados devem ser reconciliados antes da implementação correspondente.

### Mapa e origens

APROVADO: exploração do trajeto dentro do ECOnexão, com geometria, origem, destino,
atores e acompanhamento da posição em primeiro plano. Voz e orientação curva a
curva não são desejadas nem condição de lançamento. Acompanhar posição não implica
calcular uma nova rota a partir dela; origem dinâmica continua sujeita a homologação.

Uma linha "Saindo de: Aeroporto — Alterar" abre as opções, sem ocupar o card com
todas as alternativas. Origem sempre explícita; não substituir a escolha em silêncio.
Fora do território do destino, sugerir seus pontos de chegada. Dentro de uma área
operacional validada, permitir origem atual se o fluxo dinâmico passar homologação.
Coordenadas imprecisas, negadas ou antigas levam à seleção manual. A área não deve
ser definida por raio arbitrário: conferir rede viária, rios e acessos da rota.

Atores seguem o corredor do trajeto selecionado. Serviços essenciais da cidade
podem ter seção separada e identificada, sem fingir que estão no caminho.

APROVADO: sem clusters, menos pins ao afastar, mais ao aproximar/filtrar e destaque
permanente do empreendimento selecionado. Implementação proposta: ícone e cor por
categoria, prioridade do item selecionado e controle
de colisão/densidade conforme zoom. Itens omitidos visualmente continuam acessíveis
no catálogo; tornar perceptível que o mapa exibe uma seleção. Não deslocar pins de
forma a representar localização falsa. Mais zoom e filtros revelam outros pontos.

### Catálogo e experiências

APROVADO: relevância editorial por categoria, sem embaralhar a cada atualização,
com opção de ordenação alfabética. Confirmar prioridades
entre alimentação, atrativos, hospedagem e acesso rápido a saúde/segurança.
Carrosséis precisam também de controles acessíveis por teclado.

APROVADO: regras das tags de experiência definidas e registradas pela equipe durante
a revisão dos pontos da rota, como variável da criação/edição. Na primeira entrega,
isso ocorre no pacote de dados, sem depender do painel futuro. Registrar definição,
critério de inclusão, pontos associados, evidência, revisor e data; IA apenas sugere.
Começar com poucas tags de experiência, curadas pela equipe e baseadas em evidência.
"Domingo em família" não pode implicar abertura aos domingos ou acessibilidade sem
verificação. Busca/filtros devem ter semântica definida e estado vazio útil.

### Dados e Google

Armazenar conteúdo próprio, institucional ou autorizado com fonte, data e licença.
O pedido de baixar Google para atualização periódica é intenção de rapidez; não é
autorização para espelhar conteúdo com restrições de armazenamento.
Places restringe cache/persistência, com exceções como Place IDs. Fotos devem seguir
atribuição e acesso à fonte; não copiar em massa para Storage. Google Business Profile
é integração de gestão de perfis, não substituto de descoberta pública via Places.
Conteúdo Google em mapa exige desenho compatível; Routes exibido em mapa requer
Google Map. O Leaflet atual não resolve essa exigência.

APROVADO como base: fotos Google sob demanda ao abrir o perfil do empreendimento,
com atribuição, carregamento independente e fallback. Preferência adicional do owner:
fotos Google também nos cards se custo e desempenho couberem no orçamento. A opção
não está ainda liberada operacionalmente; medir antes de ativar. Carregar somente
cards visíveis, não todas as imagens dos carrosséis/rotas, nem toda a galeria no detalhe.
Não garantir custo zero: mapa, detalhes e fotos têm cotas/SKUs distintos.

Qualidade do cadastro e presença de fotos são critérios de classificação solicitados
pelo owner. Proposta: primeiro pertinência à rota/categoria e dados verificados; depois
completude/atualidade e foto real autorizada; desempate estável. Isso classifica a
qualidade do cadastro, não certifica a qualidade do estabelecimento. Não ocultar
serviços essenciais por falta de foto. Pesos/critério precisam ser documentados e testados.

Owner sugeriu imagens IA quando não houver fotos. Recomendação: apenas ilustração
claramente identificada, sem simular fachada/interior/produto como registro real do
estabelecimento. Não dar bônus de foto real a imagem sintética. Preferir imagem neutra
da categoria ou foto fornecida pelo parceiro. Esta recomendação ainda requer aceite.

Conteúdo social: owner propôs postagens incorporadas com curadoria humana. Preparar
referência da postagem, plataforma, responsável pela revisão e autorização quando
aplicável. Priorizar link e mídia fornecida com direitos; incorporação oficial no detalhe
é melhoria condicionada a teste de disponibilidade, privacidade e desempenho. Curadoria
não substitui direitos de reutilização. Não baixar postagens automaticamente nem tornar
a conclusão da primeira versão dependente de uma nova integração social. Documentação
Meta não pôde ser consultada nesta revisão; requisitos atuais de incorporação permanecem
a verificar, sem presumir necessidade ou dispensa de token/revisão de app.

### Cenários de custo e continuidade

Tabela Google consultada em 05/09/2026: SKU Places API Place Details Photos tem
franquia de 1.000 eventos mensais e US$ 7 por 1.000 eventos na primeira faixa paga.
Exemplos apenas desse SKU, supondo franquia integral disponível, uma solicitação
por imagem, sem novas tentativas e sem outros consumos na conta:

| Cenário mensal | Solicitações de fotos | Parcela estimada de fotos |
|---|---:|---:|
| 300 visitantes x 3 imagens | 900 | US$ 0 |
| 300 visitantes x 20 imagens | 6.000 | US$ 35 |
| 3.000 visitantes x 20 imagens | 60.000 | US$ 413 |

Não são orçamento total nem previsão de tráfego. Somar obtenção das referências via
Details/Search conforme campos/SKU, mapas, rotas, infraestrutura, câmbio e impostos.
Franquias e consumo são verificados na conta real antes da ativação; não presumir
que cada visitante verá exatamente essa quantidade ou que haja cache persistente permitido.

Proposta operacional: dividir os R$ 500 entre custos fixos, variáveis e reserva após
inventário; limitar uso antes de ultrapassar a parcela disponível. Alerta financeiro
não substitui quota/bloqueio. Esgotado o limite de fotos, manter ficha/mapa utilizáveis
com mídia editorial ou placeholder; medir acessos após o evento e bursts separadamente
do total mensal. Nenhum serviço crítico deve depender de foto Google para carregar.

Fontes oficiais consultadas em 2026-09-05:
- https://developers.google.com/maps/documentation/places/web-service/policies
- https://developers.google.com/maps/documentation/routes/policies
- https://developers.google.com/my-business/content/overview
- https://developers.google.com/maps/billing-and-pricing/pricing

## Alimentação sem painel completo

Definir pacote por rota a partir de Pindobal, composto por ficha editorial, origens,
geometria por origem, atores/referências e mídia autorizada. Campos mínimos: ID/slug,
região, nome, resumo, destino, acesso/modalidade, origens com coordenadas, geometria
com fonte/data, distâncias e durações com proveniência, capa/crédito/licença/alt,
atores/categorias/tags/contatos e estado de revisão. Valores ausentes ficam explícitos.

IA normaliza o pacote e prepara relatório; pessoa responsável confere trajeto e
conteúdo; pipeline existente é adaptado somente onde necessário. Dry-run precede
importação autorizada; provar idempotência, não duplicação e associações corretas.
Dados são carregados no banco; API não lê CSV em runtime. A segunda rota é a prova
de generalização. Expandir para Altamira somente após dados e acessos definidos.

## Acompanhamento das tarefas

O cadastro completo e a única sequência de execução estão em
[project_status.md](project_status.md), incluindo histórico, novas tarefas,
dependências, critérios de conclusão e commits. Este briefing registra objetivos e
justificativas; não deve manter lista paralela de tasks ou status de execução.

As decisões já confirmadas estão incorporadas à consolidação revisada. Pontos
abertos de escopo/arquitetura e orçamento pertencem à ECO-2603, fotos nos cards à
ECO-2616 e política de ilustrações IA à ECO-2695. O owner recebeu a consolidação e
autorizou commit local após revisão técnica. As datas exatas continuam pendentes de confirmação.

## Aceite e política de commits

Proposta de orçamento de desempenho: feedback visual em até 200 ms; conteúdo
principal utilizável em até 3 s e mapa em até 5 s no dispositivo/rede de referência
acordados. Medir primeira abertura, retorno com cache, conexão degradada e API fria.
São metas propostas, não resultados já demonstrados ou garantias para toda conexão.

Nenhum defeito crítico de autenticação, isolamento, trajetória ou perda de favoritos/
viagens pode ser dispensado para cumprir data. Homologar Safari no iPhone e Chrome
Android como Web, além do desktop; isso não comprova funcionamento nativo.

Commit por incremento coerente e testado, com arquivos explicitamente selecionados,
diff revisado e mensagem que descreva comportamento. Não incluir segredos, relatórios
voláteis ou alterações alheias sem revisão. Registrar commit e evidência no handoff.
Autorização para commits locais foi dada pelo owner; push/PR/merge/deploy/carga remota
continuam separados. Nenhum commit existente ou mudança do owner será reescrito.

## Decisões restantes

1. Confirmar datas absolutas do piloto/evento e de sexta-feira; prazo dos assets oficiais.
2. Fechar desenho de origem dinâmica e mapa compatível com o provedor; não confundir
   acompanhamento da posição aprovado com recálculo automático.
3. Medir a composição do orçamento e decidir ativação de fotos nos cards; detalhe
   sob demanda é a base aceita. O teto mensal é R$ 500, público inicial 300 mais compartilhamentos.
4. Aceitar/revisar identificação explícita de imagens IA e escopo opcional de embeds sociais.

Responsabilidades: owner entrega conteúdo das dez rotas até sexta; desenvolvimento
prepara importação, interface e testes antes disso. Não prometer programação concluída
em prazo fixo sem verificar baseline, dependências externas, integrações e dados finais.
O compromisso é executar por marcos verificáveis, comunicar bloqueios cedo e reservar
tempo para carga, homologação e correções após a chegada do conteúdo.

O painel completo deixa de ser condição da entrega inicial por decisão explícita do
owner. O planejamento anterior deve ser reconciliado para refletir isso, sem remover
controles de autorização, publicação e qualidade do conteúdo usado pela equipe.
