# ECOnexão — Catálogo territorial SEMTUR + Google

Status: planejamento proposto; nenhuma migration, chamada Google ou publicação é
autorizada por este pacote.

## Objetivo

Preservar integralmente e com proveniência os atores do Inventário Turístico da
SEMTUR, normalizá-los como atores canônicos ECOnexão, associá-los espacialmente a
cada origem da Rota Pindobal e enriquecer registros reconciliados com dados públicos
da Places API (New). O mapa não terá navegação nem acompanhamento em tempo real.

## Resultado de produto

- atores SEMTUR permanecem auditáveis por fonte e recebem selo discreto
  `Inventário SEMTUR` nos cards;
- alimentação, hospedagem, atrativos, artesanato, comércio e apoio aparecem quando
  estiverem dentro do corredor configurado da geometria selecionada;
- saúde, segurança e infraestrutura essencial permanecem em camada territorial fixa,
  sem alterar automaticamente o enquadramento da rota;
- categorias públicas têm grupos visuais estáveis e tipos específicos pesquisáveis;
- dados e fotos Google aparecem somente quando reconciliados, atuais, atribuídos e
  permitidos pelas políticas vigentes;
- nenhuma chave Google é exposta no Expo e nenhuma consulta Places ocorre a cada
  abertura do mapa.

## Google Meu Negócio: o que é possível

É possível exibir dados públicos e fotos de estabelecimentos por **Places API
(New)**, sujeitos a field masks, custo, atribuição, links ao Google Maps, validade e
restrições de armazenamento. A **Business Profile API** não permite consultar
livremente qualquer perfil: ela serve para locais que autorizaram a organização a
administrá-los. Integração GBP fica opcional e limitada a parceiros autorizados.

Referências oficiais a rever na sessão de implementação:

- https://developers.google.com/maps/documentation/places/web-service/op-overview
- https://developers.google.com/maps/documentation/places/web-service/policies
- https://developers.google.com/maps/documentation/places/web-service/data-fields
- https://developers.google.com/maps/documentation/places/web-service/place-id
- https://developers.google.com/my-business/content/faq

## Entrada de execução

Comece por `ECO-2501`. Execute uma task por sessão copiando apenas o prompt
correspondente de `prompts/`. Gates humanos impedem alteração de taxonomia, ativação
Google, gasto, publicação e acesso a production.
