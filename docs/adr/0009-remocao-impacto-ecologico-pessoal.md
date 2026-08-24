# ADR 0009 — Remoção de impacto ecológico e selos pessoais

Status: aceito
Data: 23/08/2026
Task relacionada: ECO-1904

## Contexto

O perfil apresentava contadores sob o título “Meu Impacto Ecológico”, uma estimativa de CO₂ evitado e um “Selo Consciente” pessoal. O produto não registrará nem validará essas informações. A fórmula existente (pontuação por viagens/visitas e CO₂ fixo por viagem) não possuía metodologia aprovada e criava risco de alegação ambiental indevida.

## Decisão

- Remover do perfil o painel “Meu Impacto Ecológico” e o selo pessoal.
- Usar “Visitante” como nome padrão da sessão anônima quando o perfil não tiver nome.
- Remover `GET /api/v1/me/impact`, seus schemas `UserImpact*`, cálculos de score/CO₂ e a tabela `app_private.user_badges` por migration progressiva.
- Preservar `trips`, `trip_actor_visits`, histórico de viagens, registro de visitas e CTA de iniciar viagem.
- Preservar `green_badge_status` e o “Selo Verde” editorial de atores/rotas. Esses atributos descrevem conteúdo territorial verificado e não uma conquista do usuário.

Esta decisão substitui somente a seção 3 do ADR 0004 no que se refere a selos conquistados pelo usuário e ao selo exibido no perfil. O comportamento editorial de selos de estabelecimentos e rotas permanece vigente.

## Consequências

- O perfil fica restrito a identidade, favoritos, histórico, preferências, suporte e gestão da conta.
- Clientes que ainda chamarem `/me/impact` receberão `404` após a atualização da API; app e backend devem ser promovidos de forma coordenada.
- A migration elimina dados de `user_badges` ao ser promovida. Não há rollback automático que recrie esses dados; restauração exigiria backup e nova decisão de produto.
- Nenhuma migration histórica é reescrita.
