# Plano de implementação — mapa por camadas e origens dinâmicas

Versão: 1.0  
Data: 23/08/2026  
Status: proposto

## 1. Resultado pretendido

O mapa deverá:

- usar categoria, cor e ícone consistentes no backend, web, Android e iOS;
- separar locais próximos do percurso de serviços essenciais da cidade;
- manter Porto, Aeroporto e Rodoviária como origens verificadas;
- permitir `Minha localização` e `Escolher no mapa` sem persistir coordenadas;
- apresentar rota dinâmica como sugestão não verificada;
- continuar utilizável quando GPS ou provedor dinâmico estiver indisponível;
- crescer sem consultar Google Places a cada abertura do mapa.

## 2. Modelo mental do produto

O mapa tem três camadas independentes:

1. **Percurso:** geometria entre origem e destino.
2. **Ao longo da rota:** alimentação, hospedagem, atrativos, artesanato e apoio de
   transporte dentro de um corredor espacial aprovado.
3. **Serviços da cidade:** saúde, segurança e infraestrutura essencial, mesmo fora
   do corredor.

O enquadramento padrão continua focado no percurso. Um modo explícito `Ver cidade`
mostra a camada territorial sem reduzir automaticamente a rota a uma linha ilegível.

## 3. Decisões que precedem código

### Gate H1 — ADR de roteamento dinâmico

O owner deve aceitar ou rejeitar uma proposta que defina:

- origem temporária e não persistência;
- diferença entre rota verificada e sugestão dinâmica;
- destino/entrada oficial de cada rota;
- provedor primário, fallback e possibilidade de troca;
- orçamento, quotas, rate limit e comportamento offline;
- política de logs, telemetria, retenção e consentimento.

### Gate H2 — Taxonomia territorial

O owner deve confirmar:

- categorias públicas, labels, cores e ícones;
- separação de `emergência` em `saúde` e `segurança`;
- regra de `outros` não publicável;
- quais categorias são `route_corridor`, `citywide_essential` ou `both`;
- relação entre atores e região para consultar serviços da cidade inteira;
- raios iniciais do corredor, ainda sujeitos a calibração com dados reais.

### Gate H3 — Provedor real e orçamento

Somente depois de benchmark e autorização explícita podem existir chave Google real,
provedor contratado ou tráfego de produção. Sem H3, o fluxo funciona apenas com
fixtures/mocks e as três geometrias verificadas existentes.

Decisão vigente: ADR 0013 aprova Google Routes API v2 `ComputeRoutes Essentials` e
revoga a seleção anterior de OSRM Self-Hosted. Gasto variável pago e produção não
foram autorizados.

## 4. Trilhas e sessões

Cada linha corresponde a uma única sessão e possui um prompt próprio.

| Task | Sessão | Resultado observável | Dependências | Gate/estado |
|---|---|---|---|---|
| ECO-2301 | Decisão de taxonomia visual | categorias, labels, slugs, cores, ícones, ordem e `outros` oculto | contrato Pindobal | para em H2 |
| ECO-2302 | Schema e normalização da taxonomia | migration/fixture, importador e API de categorias sincronizados | ECO-2301 aceito | local/test apenas |
| ECO-2303 | Contrato visual do mapa v2 | OpenAPI/tipos com legenda, cor, ícone e contagens; sem UI | ECO-2302 | contrato congelado |
| ECO-2304 | Pins e legenda no frontend | web/nativo consomem o contrato visual e removem cores fixas | ECO-2303 | evidência multiplataforma |
| ECO-2305 | Decisão de camadas espaciais | corredor × cidade, raios, vínculo ator–região e bounds | ECO-2301 | para em H2 |
| ECO-2306 | Backend de camadas estáticas | migration necessária, PostGIS, filtros, contagens e bounds | ECO-2305 aceito, ECO-2303 | sem Google runtime |
| ECO-2307 | UI Rota × Cidade | modos de câmera, filtros e limitação/clustering proporcional | ECO-2306, ECO-2304 | evidência visual |
| ECO-2308 | ADR de origens dinâmicas | proposta sobre origem efêmera, privacidade, provedor, quota e fallback | ADR 0003, spec, auditoria | para em H1 |
| ECO-2309 | Preview dinâmico com fake | `POST /preview`, schemas, interface de provedor e fake determinístico | ECO-2308 aceito | nenhuma rede externa |
| ECO-2310 | Minha localização | `expo-location`, foreground permission e origem temporária | ECO-2309 | device gate parcial |
| ECO-2311 | Escolher no mapa | toque/arraste/confirmação; preview somente após confirmar | ECO-2309 | web+nativo |
| ECO-2312 | Pins na geometria dinâmica | corredor transitório + serviços da cidade usando provedor fake | ECO-2306, ECO-2309 | sem persistência |
| ECO-2313 | Benchmark e decisão de provedor | comparação reproduzível e recomendação ao owner | ECO-2308, ECO-2309 | para em H3 |
| ECO-2314 | Conector real e guardrails | um único provedor aprovado sob feature flag | H3 aceito, ECO-2313 | sem produção automática |
| ECO-2315 | Integração e verificação final | três origens, GPS, manual, privacidade, E2E, rede e desempenho | ECO-2307, ECO-2310–2314 | staging/device |

## 5. Ordem recomendada

```text
ECO-2301 -> H2 -> 2302 -> 2303 -> 2304 ────────────────────────────────┐
       └────────> 2305 -> H2 -> 2306 -> 2307 ─────────────────────────┤
ECO-2308 -> H1 -> 2309 -> 2310 ───────────────────────────────────────┤
                         ├-> 2311 ─────────────────────────────────────┤
                 2306 + 2309 -> 2312 ─────────────────────────────────┤
                 2308 + 2309 -> 2313 -> H3 -> 2314 ───────────────────┤
                                                                        └-> ECO-2315
```

Apesar de existirem duas trilhas, nesta cópia do projeto elas devem ser executadas
sequencialmente até que Git/worktrees e reserva de arquivos estejam comprovadamente
seguros. `docs/openapi.yaml`, `app.json`, lockfiles e migrations nunca são editados
simultaneamente por sessões diferentes.

## 6. Limites de escopo por fase

### Fase A — valor imediato, sem roteamento real

ECO-2301 a ECO-2307 entregam cores, legenda, camadas e câmera usando as três origens
atuais. Não dependem de billing Google.

### Fase B — experiência dinâmica sem fornecedor real

ECO-2308 a ECO-2312 entregam ADR, contrato, interface, GPS, escolha manual e pins
dinâmicos com respostas simuladas e nenhuma chamada externa em teste.

### Fase C — provedor e integração real

ECO-2313 a ECO-2315 dependem de decisão humana, orçamento/infraestrutura, staging e
homologação física. Não podem ser marcadas `VERIFIED` apenas com mocks.

### Revisão do Gate H3 — 2026-08-25

O Owner substituiu OSRM Self-Hosted por Google Routes API v2 `ComputeRoutes
Essentials`, conforme ADR 0013. Não haverá provisionamento OSRM. A ECO-2314 deve
substituir a implementação OSRM, manter a feature desligada por padrão e provar
guardas de SKU, quota mensal, privacidade e staging antes de avançar.

## 7. Critérios globais de aceite

- Cor nunca é o único meio de identificar categoria.
- Toda interação funciona por toque, teclado quando aplicável e leitor de tela.
- Toda consulta possui loading, vazio, erro, timeout/offline e retry.
- Trocar origem preserva rota, ator e categoria nas navegações aplicáveis.
- Falha dinâmica mantém a última rota válida ou oferece as três origens fixas.
- Rota dinâmica aparece como `não verificada`/`sugestão`.
- Nenhuma coordenada precisa aparece em URL, banco, log, Sentry ou fixture.
- Testes e CI não chamam Google, OSRM externo ou production.
- Places continua sendo ingestão controlada; não é chamado a cada abertura do mapa.
- OpenAPI e tipos gerados não apresentam drift.
- Consultas espaciais usam índices, limites e payload proporcional ao zoom/uso.

## 8. Estratégia de rollback

- Categorias/schema: migration forward posterior; nunca editar migration aplicada.
- Contratos: manter compatibilidade durante uma janela de transição ou reverter o
  consumidor junto do produtor antes de promoção.
- UI dinâmica: feature flag desabilita GPS/ponto manual e mantém origens fixas.
- Provedor: circuit breaker/fallback aprovado; sem fallback silencioso para mock em
  produção.
- Dados Google: despublicar/reconciliar mantendo proveniência; não sobrescrever fonte
  editorial superior.

## 9. Condição de encerramento

A iniciativa só termina quando ECO-2315 tiver evidência em web e dispositivos móveis,
revisão cruzada, privacidade verificada e decisão humana sobre limitações conhecidas.
Até lá, cada task deve registrar `VERIFIED`, `PARTIAL`, `BLOCKED` ou `NOT_VERIFIABLE`
com evidência, nunca apenas “código concluído”.
