# ADR 0013 — Google Routes API como provedor de roteamento dinâmico

- **Status:** aceito pelo Owner
- **Data:** 2026-08-25
- **Decisor:** Bruno Darwich, Owner do Projeto
- **Tasks relacionadas:** ECO-2313, ECO-2314, ECO-2315
- **Substitui:** seleção de OSRM Self-Hosted registrada anteriormente no Gate H3

## Contexto

O Gate H3 original selecionou OSRM Self-Hosted. Durante a preparação da ECO-2314,
ficou comprovado que essa opção exige contratação, provisionamento, atualização e
monitoramento de infraestrutura dedicada. O Owner reconsiderou a decisão e priorizou
menor carga operacional para o estágio atual do produto.

Google Business Profile (“Meu Negócio”) permanece uma integração distinta para
gestão de perfis autorizados e não calcula trajetos. O serviço de roteamento aprovado
é exclusivamente **Google Routes API v2 — `ComputeRoutes`, SKU Essentials**.

## Decisão

1. Google Routes API `ComputeRoutes Essentials` passa a ser o único provedor real
   aprovado para previews dinâmicos.
2. OSRM Self-Hosted deixa de ser o provedor aprovado; não será contratado nem
   provisionado para esta iniciativa.
3. O backend FastAPI continua como única fronteira. A chave Google é server-side,
   armazenada no secret manager e nunca exposta ao Expo.
4. O contrato público `RoutingConnector` permanece independente do fornecedor.
5. `ENABLE_DYNAMIC_ROUTING=false` continua sendo o default em todos os ambientes
   implantados até staging autorizado e smoke aprovado.
6. Provider desconhecido, ausente ou não aprovado falha fechado. Não existe fallback
   automático para Fake fora de development/test; a experiência restaura uma origem
   oficial verificada.
7. Produção não está autorizada por esta decisão.

## Guardas financeiros

- Rate limit: 10 previews por minuto por identidade/IP, preservado do Gate H3.
- SKU permitido: somente `ComputeRoutes Essentials`; opções que promovam a chamada
  para Pro/Enterprise ficam proibidas sem nova decisão.
- Gasto variável pago: **não autorizado** nesta decisão.
- O backend deve possuir contador mensal compartilhado e bloquear novas chamadas
  antes de ultrapassar a franquia gratuita vigente. A quota do Google Cloud é defesa
  adicional, não substitui o bloqueio interno.
- Alertas devem ocorrer antes do limite e a feature flag deve permitir desligamento
  imediato. Alteração da franquia/preço exige revisão documental antes de ativar.

## Privacidade, cache e contrato

- Coordenadas efêmeras são enviadas ao Google apenas para calcular o trajeto, via
  POST server-side, e não são persistidas nem registradas em logs, métricas ou URLs
  do ECOnexão.
- Política de privacidade e consentimento/contexto de localização devem informar o
  tratamento pelo Google antes do staging com usuários reais.
- Cache, retenção, exibição e atribuição obedecem aos termos vigentes da Google Maps
  Platform. Não se reaproveita a política de cache de 24 horas aprovada para OSRM
  sem validação específica do serviço Google.
- A chamada usa field mask mínima: distância, duração e polyline necessários ao
  contrato; tráfego em tempo real, rotas alternativas e campos adicionais ficam
  desligados para preservar o SKU Essentials e minimizar dados/custo.

## Estado de implementação

A implementação OSRM produzida na ECO-2314 não corresponde mais ao provider
aprovado. ECO-2314 retorna a `BLOCKED` até uma sessão própria substituir o conector,
configuração, testes, métricas e runbook por Google Routes. Nenhuma chave, billing,
chamada real ou produção é autorizada automaticamente por este ADR.

## Condições para retomar ECO-2314

1. Projeto Google Cloud de staging separado e billing configurado pelo Owner.
2. Routes API habilitada e chave server-side restrita à API/ambiente.
3. Confirmação atual de preço, franquia, SKU, termos de cache e atribuição.
4. Guardas mensal e por minuto implementados e testados offline.
5. Política de privacidade atualizada antes de coordenadas reais.
6. Smoke único somente contra staging explicitamente autorizado.

## Registro complementar do Owner — 2026-08-25

- Google Maps foi aprovado para telas que exibam rotas dinâmicas ou rotas oficiais
  calculadas pelo Google. Snapshots oficiais OSRM existentes não se tornam conteúdo
  Google e permanecem disponíveis como fallback.
- Projeto Google Cloud de staging, billing, Routes API e chave restrita à Routes API
  foram confirmados pelo Owner sem compartilhar a credencial.
- Cotas do projeto foram reduzidas para 10 chamadas por minuto e 290 por dia.
- Guardas internos aprovados: alerta em 7.500, bloqueio em 9.000 chamadas mensais e
  nenhum gasto variável pago.
- Autorizada implementação somente em development/test e preparação de staging com
  `ENABLE_DYNAMIC_ROUTING=false`. Produção e chamadas reais permanecem proibidas.
- Permanecem pendentes: secret no backend de staging, política/termos públicos,
  verificação de Google Maps nas plataformas e autorização separada do smoke.
