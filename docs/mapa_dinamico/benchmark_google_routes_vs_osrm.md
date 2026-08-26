# Benchmark Técnico e Análise de Decisão de Provedor de Roteamento (ECO-2313)

**Documento:** Benchmark & Avaliação de Provedor de Roteamento Dinâmico (Google Routes API vs. OSRM Self-Hosted vs. Gerenciados)  
**Status do Documento:** `GATE H3 REVISADO PELO OWNER — ADR 0013`  
**Data da Avaliação:** 25 de Agosto de 2026  
**Contexto de Aplicação:** ECO-2309 (Preview de Rota Dinâmica), ECO-2313 (Benchmark/Decisão) e ECO-2314 (Conector Real e Guardrails)

---

## 1. Sumário Executivo

Este documento estabelece a análise técnica, jurídica e financeira comparando **Google Routes API (v2 / ComputeRoutes)**, **OSRM (Open Source Routing Machine — Self-Hosted)** e **Fornecedores Gerenciados (SaaS)** para o cálculo de rotas dinâmicas transitórias no ECOnexão (região de Santarém, Belterra, Alter do Chão e Pindobal/PA).

Esta análise atende estritamente às diretrizes de `AGENTS.md` e `docs/mapa_dinamico/prompts/ECO-2313.md`:
1. **Sem billing, contratação de infraestrutura ou chamadas pagas de rede** nesta sessão.
2. **Separação rigorosa entre resultados sintéticos de fixtures offline e medições empíricas de rede.**
3. **Expurgo de alegações de latência ou cobertura territorial não comprovadas por telemetria de campo.**
4. **Retificação do estado do conector no backend:** não há conector `GoogleRoutesConnector` implementado (apenas a interface abstrata `RoutingConnector`, o conector de desenvolvimento `FakeRoutingConnector` e o conector primário candidato `OSRMConnector`).
5. **Apresentação de opções estruturadas e parada mandatória no Gate H3 para decisão explícita do Owner.**

---

## 2. Comparativo de Contratos, Protocolo e Integração

| Critério | Google Routes API (`ComputeRoutes` v2) | OSRM (`osrm-routed` / HTTP) | Provedores Gerenciados OSM (Mapbox / Stadia / LocationIQ) |
|---|---|---|---|
| **Protocolo Principal** | HTTPS POST (REST) ou gRPC | HTTP/1.1 REST (GET) | HTTPS REST (GET/POST) |
| **Autenticação** | API Key (`X-Goog-Api-Key`, `X-Goog-FieldMask`) | Nenhuma (rede privada interna VPC/Docker) | API Key via query param ou Header |
| **Formato de Geometria** | Encoded Polyline (`polyline.encodedPolyline`) | GeoJSON nativo (`LineString` com `coordinates`) | GeoJSON / Polyline (configurável) |
| **Custo Computacional Backend** | Requer algoritmo de decodificação de polyline | Zero processamento adicional (GeoJSON direto) | Mínimo / Nenhum (GeoJSON direto) |
| **Tamanho Médio de Payload** | Compacto (~400 a 900 bytes compactados) | Moderado (~1.5 KB a 4.0 KB com coordenadas) | Moderado (~1.5 KB a 4.0 KB) |
| **Cálculo de Bounds / Viewport** | Fornecido nativamente (`viewport.low/high`) | Calculado no backend via min/max de coordenadas | Nativamente fornecido (`bbox`) |

---

## 3. Cobertura da Malha Regional (Premissas Teóricas e Necessidade de Validação em Campo)

> **Ressalva Metodológica:** As características abaixo refletem premissas conceituais da base OpenStreetMap vs. Google Maps Platform. A acurácia final e navegabilidade em ramais de areia dependerão de validação amostral in loco no plano de homologação territorial de staging.

1. **Eixo Pavimentado e Urbano (Santarém, PA-457, BR-163):**
   - **Google Maps:** Alta densidade de mapeamento e dados históricos de tráfego.
   - **OSM / OSRM:** Rodovias estaduais, federais e vias urbanas de Santarém mapeadas na base OpenStreetMap.

2. **Ramais de Terra/Areia e Acessos a Praias (Ramal do Pindobal, Eixo Forte, Ponta de Pedras):**
   - **Google Maps:** Pode classificar ramais vicinais de areia como vias inexistentes ou com velocidade estimada irrealista para condução urbana padrão.
   - **OSM / OSRM:** Historicamente detalhado pela comunidade local em projetos abertos (tags `highway=track`, `surface=sand`/`unpaved`), permitindo ajustes em arquivos de perfil de velocidade (`car.lua`).

3. **Cenário Fluvial / Origem Sem Conexão Terrestre (Rio Tapajós):**
   - Ambos os provedores possuem comportamento determinístico tratável: Google retorna `404 NOT_FOUND` / `ZERO_RESULTS`, enquanto OSRM retorna `code: "NoRoute"`.
   - O backend normaliza ambos para a exceção unificada `RoutingNoRouteFoundError` (`code: "NO_ROUTE_FOUND"`).

---

## 4. Estrutura de Custos, Franquias Oficiais e Cenários de Tráfego

### 4.1 Tabela de Preços e Franquias Oficiais (Vigência 2025/2026)

1. **Google Maps Platform — Routes API v2:**
   - *Modelo:* Pay-As-You-Go por mil requisições (CPM) com franquia gratuita por SKU (o crédito unificado de US$ 200/mês foi substituído por cotas fixas por SKU em março/2025).
   - *SKU `Routes: Compute Routes Essentials`:*
     - **Franquia gratuita:** **10.000 requisições / mês** (custo US$ 0,00).
     - **0 a 100.000 reqs:** US$ 5,00 por 1.000 requisições adicionais (US$ 0,005/req).
   - *SKU `Routes: Compute Routes Pro` (Tráfego em tempo real / Otimização de Waypoints):*
     - **Franquia gratuita:** **5.000 requisições / mês** (custo US$ 0,00).
     - **0 a 100.000 reqs:** US$ 10,00 por 1.000 requisições adicionais (US$ 0,010/req).

2. **OSRM Self-Hosted (Container Docker com extrato regional Norte/PA):**
   - *Software:* Open Source (Licença BSD 2-Clause), custo US$ 0,00.
   - *Consumo de Memória do Daemon:* ~350 MB a 550 MB de RAM para o extrato regional (`norte-latest.osm.pbf` = ~152 MB bruto).
   - *Infraestrutura VPS (Hetzner CX22 / AWS Lightsail 2GB):* **US$ 4,00 a US$ 10,00 / mês** (~R$ 23,00 a R$ 57,00/mês).
   - *Opção Co-localizada (Container na mesma VPS do FastAPI):* **Acréscimo marginal de US$ 0,00 a US$ 5,00 / mês**.

3. **Provedores Gerenciados OSM (SaaS):**
   - *Mapbox Directions:* **100.000 requisições / mês gratuitas**; excedente a US$ 2,00 / 1.000 reqs.
   - *LocationIQ:* **5.000 reqs / dia gratuitas** (~150.000/mês com rate limit 2 req/s); planos comerciais a partir de US$ 45,00/mês.
   - *Stadia Maps:* Free tier com 200.000 créditos (~10.000 rotas/mês); planos pagos a partir de US$ 20,00/mês.

---

### 4.2 Simulação Comparativa de Custos por Volume Mensal

| Volume Mensal de Rotas | OSRM Self-Hosted (VPS Dedicada / Co-localizada) | Google Routes (Essentials) | Mapbox Directions (Gerenciado OSM) | LocationIQ (Gerenciado OSM) |
| :--- | :--- | :--- | :--- | :--- |
| **1.000 req / mês** | US$ 4,00 – US$ 10,00 *(ou US$ 0 co-localizado)* | **US$ 0,00** *(dentro de 10k gratis)* | **US$ 0,00** *(dentro de 100k gratis)* | **US$ 0,00** *(dentro de 150k gratis)* |
| **10.000 req / mês** | US$ 4,00 – US$ 10,00 | **US$ 0,00** *(franquia 10k)* | **US$ 0,00** | **US$ 0,00** |
| **50.000 req / mês** | **US$ 4,00 – US$ 10,00** *(fixo)* | US$ 200,00 *(40k excedentes x $5)* | **US$ 0,00** *(dentro de 100k)* | **US$ 0,00** |
| **100.000 req / mês** | **US$ 4,00 – US$ 10,00** *(fixo)* | US$ 450,00 *(90k excedentes x $5)* | **US$ 0,00** *(limite da franquia)* | **US$ 0,00** |
| **300.000 req / mês (Alta Temporada)** | **US$ 4,00 – US$ 10,00** *(fixo)* | US$ 1.450,00 | US$ 400,00 | US$ 45,00 *(plano comercial)* |

> **Nota de Risco Orçamentário com APIs Pay-As-You-Go:** No Google Routes, loops acidentais no cliente, scraping ou crescimento acelerado geram custos variáveis imediatos sem teto rígido caso não haja hard budget limit configurado no Cloud Console. O OSRM self-hosted oferece previsibilidade orçamentária absoluta (custo fixo).

---

## 5. Termos de Uso, Caching e Conformidade com LGPD / Privacidade

| Aspecto Jurídico / Técnico | Google Routes API (Google Maps Platform) | OSRM Self-Hosted | Provedores Gerenciados OSM (Mapbox / LocationIQ) |
|---|---|---|---|
| **Política de Caching de Geometrias** | **Altamente restrita:** Proibido armazenar polylines ou pré-calcular rotas para evitar chamadas de API. Caching temporário permitido por no máximo **30 dias corridos**. | **100% Livre:** Licença aberta ODbL / BSD permite persistir e cachear geometrias por tempo indeterminado. | Permissivo para cache temporário / tráfego transitório; restrições para montagem de base concorrente offline. |
| **Privacidade & LGPD** | Coordenadas de origem do usuário trafegam para servidores externos do Google (EUA/Global). Exige menção expressa na Política de Privacidade. | **Isolamento Total:** Coordenadas trafegam e são processadas exclusivamente dentro da rede interna/VPC do ECOnexão. | Coordenadas trafegam para o fornecedor do SaaS sob seus respectivos acordos de DPA (Data Processing Agreement). |
| **Sanitização de Logs** | Exige redação estrita para não registrar parâmetros em gateways intermediários. | Total conformidade: logs internos registram apenas `request_id`, `travel_mode` e status, descartando coordenadas em memória. | Exige redação de parâmetros de requisição. |

---

## 6. Performance e Latência (Estimativas Teóricas vs. Plano de Aferição em Staging)

- **OSRM Self-Hosted (Rede Local / Mesma VPC):**
  - *Estimativa Teórica:* Processamento de grafo via MLD em ~2 ms a 15 ms; latência de rede interna < 5 ms.
- **Google Routes API / Provedores SaaS (Chamada WAN via Internet):**
  - *Estimativa Teórica:* Handshake TLS + tráfego WAN + processamento em nuvem em ~150 ms a 450 ms.
- **Protocolo de Aferição Real:** A latência empírica p50/p95/p99 será medida formalmente em ambiente de homologação (Staging) durante os testes de carga da task `ECO-2104`, sem extrapolação prévia.

---

## 7. Validação de Contrato e Ingestão via Harness Offline (Fixtures Sintéticas)

O harness de testes em `backend/tests/test_routing_benchmark_harness.py` comprova a viabilidade dos parsers de contrato e a normalização de exceções em modo puramente offline:

1. **Amostra 1 (Urbano / Misto — Aeroporto STM -> Pindobal):**
   - Fixtures estáticas comparadas em `google_routes_urban_airport.json` e `osrm_urban_airport.json`.
   - Distância simulada: ~35.240m (Google) vs ~35.180m (OSRM) — convergência geométrica dentro de 0,2%.
2. **Amostra 2 (Rural / Ramal de Acesso — Ramal Pindobal -> Praia de Pindobal):**
   - Fixtures: `google_routes_rural_ramal.json` e `osrm_rural_ramal.json`.
   - Distância simulada: ~14.200m (Google) vs ~14.150m (OSRM).
3. **Amostra 3 (Cenário Fluvial / Rota Impossível — Ponto no Rio Tapajós):**
   - Ambas as estruturas de erro são normalizadas uniformemente para `RoutingNoRouteFoundError` (`code: "NO_ROUTE_FOUND"`).
4. **Amostra 4 (Resiliência e Ausência de Vazamento):**
   - Falhas 503/timeout mapeadas para `RoutingProviderUnavailableError`.
   - Teste `test_no_coordinate_leakage_in_exceptions` comprova que coordenadas geográficas de origem/destino **nunca** vazam nas mensagens de exceção ou logs de erro.

---

## 8. Matriz Ponderada de Decisão Multicritério

Pesos de Avaliação (1 a 5, onde 5 é o maior impacto para o projeto ECOnexão):

| Critério | Peso | Google Routes API (1-5) | OSRM Self-Hosted (1-5) | Mapbox / Managed OSM (1-5) | Score Google | Score OSRM | Score Managed OSM |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Previsibilidade Orçamentária / Custo Fixo** | 5 | 2 | 5 | 4 | 10 | 25 | 20 |
| **Soberania de Dados / LGPD / Privacidade** | 4 | 3 | 5 | 3 | 12 | 20 | 12 |
| **Liberdade de Caching & Persistência** | 4 | 2 | 5 | 3 | 8 | 20 | 12 |
| **Fidelidade da Malha em Ramais Regionais** | 4 | 3 | 5 | 4 | 12 | 20 | 16 |
| **Simplicidade de Operação (Zero Ops)** | 3 | 5 | 3 | 5 | 15 | 9 | 15 |
| **Tráfego em Tempo Real / Congestionamentos** | 2 | 5 | 1 | 4 | 10 | 2 | 8 |
| **TOTAL PONDERADO** | — | — | — | — | **67 / 110** | **96 / 110** | **83 / 110** |

---

## 9. Recomendação Técnica e Estrutura de Reversibilidade

### 9.1 Recomendação Técnica Primária
> **Recomendação histórica superada pelo ADR 0013.** O benchmark originalmente
> recomendou **OSRM Self-Hosted** (co-localizado ou em VPS regional dedicada de
> ~US$ 5 a US$ 10/mês). O Owner posteriormente priorizou menor carga operacional e
> aprovou Google Routes API Essentials.

Razões da recomendação histórica:
1. **Previsibilidade Financeira:** Custo fixo imune a picos de requisições ou ataques de negação de serviço.
2. **Conformidade LGPD:** Coordenadas efêmeras de turistas permanecem 100% dentro da infraestrutura do projeto.
3. **Independência de Fornecedor:** Sem limitações contratuais para cache de geometrias calculadas.

### 9.2 Reversibilidade via Padrão `RoutingConnector`
A arquitetura do backend desacopla totalmente a camada de negócio do provedor por meio da interface abstrata `RoutingConnector` (`backend/app/connectors/routing_connector.py`):
- O código do domínio e as rotas da API dependem unicamente da interface abstrata.
- O conector ativo é injetado via `backend/app/services/dependencies.py` orientado pela configuração `ROUTING_PROVIDER`.
- Caso seja necessário alternar entre provedores no futuro, a migração exige apenas a implementação do conector correspondente sob a mesma interface, sem alterações em controllers ou regras de negócio.

---

## 10. Ficha de Decisão — Registro do Gate H3 (Homologado pelo Owner)

> **Decisão superada:** a ficha abaixo preserva o registro histórico da seleção
> inicial de OSRM. Em 2026-08-25, após avaliar o custo operacional de provisionar e
> manter servidor próprio, o Owner substituiu essa seleção por Google Routes API v2
> `ComputeRoutes Essentials`. O ADR 0013 é a decisão normativa vigente.

> **Registro histórico superado:** o primeiro Gate H3 homologado pelo Owner em
> 2026-08-25 autorizava OSRM self-hosted. Ele é preservado abaixo apenas para
> rastreabilidade e não autoriza implementação, contratação ou ativação atual.

```markdown
================================================================================
                    FICHA DE REGISTRO DO GATE H3 (DECISÃO FORMAL)
================================================================================
Status Atual: [X] HOMOLOGADO E APROVADO PELO OWNER
Data da Decisão: 25 / 08 / 2026

1. Provedor Primário de Roteamento Selecionado:
   [X] Opção 1: OSRM Self-Hosted (Container dedicado/co-localizado com extrato Norte/PA)
   [ ] Opção 2: Google Routes API (ComputeRoutes v2 - Pay-As-You-Go)
   [ ] Opção 3: Provedor Gerenciado OSM (Mapbox / LocationIQ / Stadia Maps)
   [ ] Opção 4: Manter Provedor Fake / Determinístico (Sem conexão de rede)

2. Estratégia de Fallback e Contingência:
   [X] Fallback para Fake Determinístico em caso de falha/timeout (3.5s / circuit breaker)
   [ ] Fallback para Provedor Secundário sob demanda
   [ ] Nenhum fallback dinâmico (reverter para origens oficiais verificadas)

3. Limite Orçamentário Mensal Autorizado:
   - Teto Máximo de Infraestrutura / API: R$ 60,00 / mês (ou US$ 10,00 / mês)

4. Parâmetros de Guardrails e Quotas Aprovados:
   - Rate Limit por IP: 10 requisições / minuto
   - Timeout de Chamada: 3.500 ms (Circuit Breaker: 5 falhas consecutivas)
   - Política de Cache: Caching efêmero em memória / Redis

5. Ambientes Autorizados para Ativação do Conector Real:
   [X] Ambiente Local / Dev (com Fake e OSRM local)
   [X] Ambiente de Testes / CI (com fixtures offline e mocks)
   [X] Ambiente de Staging / Homologação (com OSRM dedicado / co-localizado)
   [ ] Ambiente de Produção (Requer aprovação final no Gate ECO-2315)

Assinatura do Proprietário do Produto (Owner):
Nome: Bruno Darwich (Owner do Projeto)
Decisão: [X] APROVADO / HOMOLOGADO    [ ] REJEITADO / REVISÃO SOLICITADA
Data da Decisão: 2026-08-25
================================================================================
```

## 11. Revisão formal do Gate H3 — decisão vigente

```markdown
Status: [X] HOMOLOGADO E APROVADO PELO OWNER
Data: 2026-08-25

Provider primário:
[X] Google Routes API v2 — ComputeRoutes Essentials
[ ] OSRM Self-Hosted
[ ] Fake Determinístico

Motivo da revisão:
- eliminar contratação, provisionamento e manutenção de servidor OSRM dedicado;
- priorizar simplicidade operacional no estágio atual do produto.

Guardas:
- 10 previews por minuto por identidade/IP;
- bloqueio interno mensal antes de ultrapassar a franquia gratuita vigente;
- gasto variável pago não autorizado;
- field mask mínima e opções compatíveis com Essentials;
- coordenadas efêmeras, sem persistência/log/telemetria;
- nenhum fallback automático para Fake;
- staging somente com autorização explícita;
- produção não autorizada.

Consequência:
- ECO-2314 volta a BLOCKED até substituir a implementação OSRM pelo conector Google,
  implementar guardas mensais e concluir revisão de termos/privacidade.
```
