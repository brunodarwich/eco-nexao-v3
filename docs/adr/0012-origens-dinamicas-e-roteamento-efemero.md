# ADR 0012 — Origens Dinâmicas, Roteamento Efêmero e Privacidade de Localização

* **Status:** aceito  
* **Data:** 2026-08-24  
* **Decisores:** Equipe de Desenvolvimento ECOnexão / Owner do Projeto (Gate H1)  
* **Tasks Relacionadas:** ECO-2308, ECO-2309, ECO-2310, ECO-2311, ECO-2312, ECO-2313, ECO-2314  

> **Emenda normativa:** a escolha de provider do Gate H3 foi substituída em
> 2026-08-25 pelo ADR 0013. Google Routes API `ComputeRoutes Essentials` é o provider
> real vigente; referências a OSRM abaixo permanecem como comparação/histórico.

---

## 1. Contexto e Problema

Na versão 1 do ECOnexão, a exploração de percursos turísticos (como a Rota Pindobal) opera com origens fixas e homologadas pela equipe editorial (e.g., Porto Fluvial, Aeroporto Maestro Wilson Fonseca e Rodoviária de Santarém). Estas origens representam nós de entrada verificados e possuem geometrias pré-calculadas e armazenadas em banco (`route_origins` e `route_geometries`).

Contudo, turistas reais frequentemente iniciam seus deslocamentos a partir de suas posições atuais (via GPS — *"Minha Localização"*) ou de pontos arbitrários selecionados no mapa (*"Escolher no mapa"*), como pousadas, hotéis ou pontos de encontro no centro urbano.

A introdução de origens arbitrárias sob demanda apresenta quatro desafios arquiteturais e normativos:
1. **Integridade Editorial vs. Efemeridade:** Origens e trajetos gerados dinamicamente não podem poluir o catálogo de rotas oficiais verificadas nem serem persistidos no banco de dados relacional.
2. **Privacidade e LGPD (Lei nº 13.709/2018):** Coordenadas geográficas precisas do usuário constituem dados pessoais quando associadas a identificadores de sessão. O tráfego e tratamento desses dados exigem transporte estritamente seguro, vedação de registro em logs/URLs e descarte imediato em memória após o cálculo.
3. **Custo, Escalabilidade e Termos dos Provedores:** Serviços de cálculo de rotas (e.g., Google Routes API, OSRM) possuem regimes de custo, latência, quotas e termos de uso drasticamente distintos. O modelo deve prever tolerância a falhas, rate limiting, caching em conformidade com as licenças e substituição transparente do provedor sem alterar os contratos do cliente.
4. **Resiliência e Fallback:** Falhas de rede, recusa de permissão de GPS ou indisponibilidade de APIs externas não podem degradar o app ou impedir o usuário de explorar a rota por meio das origens oficiais.

---

## 2. Decisão Formal do Owner (Gate H1)

### 2.1 Distinção de Interface: Aviso Discreto de Rota Dinâmica e Selo SEMTUR nos Atores

Adota-se um modelo harmonizado de apresentação visual que combina fluidez de navegação com transparência de governança e segurança para o turista:

1. **Rotas Oficiais / Verificadas (`verified: true`):**
   - Vinculadas às origens catalogadas em `route_origins` (Porto, Aeroporto, Rodoviária).
   - Geometrias perenes auditadas e armazenadas em `route_geometries`.
   - Servem como base de referência imutável e **fallback permanente**.

2. **Rotas Dinâmicas Sugeridas (`verified: false`):**
   - Geradas em tempo de execução a partir de coordenadas temporárias (GPS ou pin manual).
   - **Estritamente efêmeras:** jamais persistidas nas tabelas de banco `route_origins` ou `route_geometries`.
   - **Aviso Informativo Discreto:** A interface do aplicativo (Expo Android/iOS/Web) apresentará uma mensagem/aviso sutil e não intrusivo no cabeçalho ou rodapé do preview dinâmico informando que o trecho inicial até o destino oficial é uma estimativa de trajeto (e.g., *"Trajeto sugerido a partir do seu ponto de partida"*).

3. **Selo Institucional SEMTUR nos Atores Verificados:**
   - Para garantir total segurança e confiança ao visitante sobre a infraestrutura dos pontos de parada, todo ator turístico auditado e homologado pelo órgão público municipal receberá um **selo oficial SEMTUR** visível no mapa, no bottom sheet e na tela de detalhes (`/actor/[actorId]`).
   - Atores sem verificação institucional permanecem identificados normalmente por suas categorias canônicas (ADR 0010), sem o selo.

---

### 2.2 Ponto de Destino e Âncora Territorial Fixa

O cálculo de roteamento dinâmico no ECOnexão adota o conceito de **Âncora Territorial Fixa**:
- Toda rota possui uma entrada oficial ou centróide de destino fixo homologado editorialmente (para a Rota Pindobal: Portal de Entrada de Pindobal / Praia de Pindobal, Belterra/PA).
- A origem dinâmica conecta a coordenada arbitrária do usuário diretamente ao ponto de entrada oficial da rota (`destination_point`), garantindo que o corredor turístico e os atrativos catalogados permaneçam consistentes.

---

### 2.3 Modos de Transporte (*Travel Modes*)

O serviço de roteamento suportará perfis modais explícitos:
- **`DRIVE` (Automóvel / Condução - Padrão Primário):** Perfil obrigatório no lançamento inicial. Focado na malha rodoviária (ex: PA-457 / Rodovia Everaldo Martins e BR-163).
- **`WALKING` (Pedestre) e `BICYCLE` (Cicloturismo / Trilha):** Modos secundários/futuros. Devido às condições amazônicas de intempérie, ausência de acostamento em trechos intermunicipais e risco de segurança, estes modos só serão ativados após homologação de malha específica e benchmark de altimetria/segurança.

---

### 2.4 Privacidade, Segurança e Conformidade LGPD

Para garantir conformidade incondicional com a LGPD e o ADR 0008:

1. **Transporte via `POST` Body:**
   - O cálculo de rota dinâmica é solicitado via `POST /api/v1/routes/{id}/preview`.
   - As coordenadas (`latitude`, `longitude`, `travel_mode`) trafegam **exclusivamente no corpo da requisição JSON (HTTP Request Body)** via TLS/HTTPS, **nunca** em query parameters (`?lat=...&lng=...`) ou path parameters, impedindo vazamentos em históricos de navegadores, proxies reversos e logs de CDN.

2. **Sanitização Estrita de Logs e Telemetria:**
   - O middleware de logging do FastAPI, Sentry e ferramentas de APM têm redação obrigatória de payloads espaciais transitórios.
   - Logs registram apenas: `request_id`, `route_id`, `travel_mode`, `provider`, tempo de resposta e status HTTP. Coordenadas brutas não entram em nenhum stream de log persistente.

3. **Ciclo de Vida na Memória (Zero Persistência):**
   - As coordenadas temporárias vivem exclusivamente no escopo da requisição do FastAPI.
   - Não há gravação em banco, tabelas temporárias ou filas assíncronas persistentes.
   - Finalizado o cálculo ou gerado o erro, a memória é imediatamente liberada pelo garbage collector.

---

### 2.5 Comparação Técnica e Financeira de Provedores de Roteamento

Analisam-se três alternativas para atendimento da demanda de roteamento:

| Critério | Opção A: Mock / Fake Determinístico | Opção B: OSRM Auto-hospedado (Cloud Run / VPS) | Opção C: Google Routes API (`ComputeRoutes`) |
| :--- | :--- | :--- | :--- |
| **Descrição** | Gerador algorítmico server-side de polylines interpoladas e estimativas determinísticas sem chamadas de rede. | Instância dedicada do Open Source Routing Machine com malha OpenStreetMap (extrato Norte/Pará). | API corporativa sob demanda do Google Maps Platform (nova geração). |
| **Qualidade da Malha (Santarém/Belterra)** | Nula para navegação real (apenas mockup de trajeto). | Média a Alta (depende do detalhamento OSM em vicinais e ramais de praia). | Altíssima (atualização frequente de geometria e fechamentos). |
| **Custo de Licença / Transação** | **R$ 0,00** | **Custo fixo de infraestrutura:** R$ 35,00 a R$ 120,00/mês (Cloud Run / VPS básica 2GB RAM / 2 vCPU). | **Custo variável:** US$ 5,00 a US$ 10,00 por 1.000 requisições (após créditos gratuitos). Risco de estouro em caso de surto de tráfego. |
| **Termos de Caching e Armazenamento** | Livre. | **100% Livre:** licença permissiva ODbL/OSRM permite cache ilimitado de geometrias e respostas. | **Restrito:** Termos Google Maps Platform proíbem armazenamento/cache de trajetos por mais de 30 dias e limitam prefetching. |
| **Tráfego Offline / Privacidade** | 100% isolado. | Totalmente isolado sob controle da infraestrutura do ECOnexão. | Dados trafegam para servidores Google (exige termo de privacidade claro). |
| **Complexidade Operacional** | Mínima (código Python puro). | Média (exige container Docker, atualização periódica de extratos `.pbf` e pipeline de compilação). | Baixa no backend (SDK/HTTP client), mas alta gestão financeira e de quotas. |

**Recomendação Técnica:**
1. **Fase de Desenvolvimento e Testes (ECO-2309 a ECO-2312):** Utilizar **Opção A (Fake Determinístico)** como provedor padrão, assegurando que nenhum custo ou dependência de rede bloqueie a entrega das interfaces e fluxos de GPS/mapa.
2. **Benchmark e Decisão de Produção (ECO-2313 / Gate H3):** Submeter benchmark empírico comparando a acurácia da malha OSM regional do OSRM frente ao Google Routes API para decisão final do Owner.

---

### 2.6 Políticas de Quotas, Rate Limit, Caching e Resiliência

1. **Rate Limiting por Usuário/IP:**
   - `POST /api/v1/routes/{id}/preview`: limitado a **10 requisições por minuto por usuário autenticado/anônimo** (ou IP), evitando consumo abusivo de quotas de provedores.

2. **Estratégia de Caching Geográfico Discreto (Grid Caching):**
   - Para evitar chamadas repetidas para origens geograficamente idênticas, o backend implementará normalização espacial de coordenadas em grade (*grid snapping* de ~50 metros / 3 casas decimais).
   - Respostas do provedor serão cacheadas em Redis/memória em conformidade com as regras do provedor selecionado (OSRM: até 24h; Google: transitório / max 30 dias).

3. **Timeouts e Circuit Breaker:**
   - **Timeout estrito:** Chamadas ao conector de roteamento externo terão timeout máximo de **3,5 segundos**.
   - **Circuit Breaker:** Em caso de 5 falhas consecutivas do conector externo, o circuito abre por 60 segundos, retornando imediatamente erro tipado de roteamento (`ROUTING_PROVIDER_UNAVAILABLE`) sem travar as threads do FastAPI.

---

### 2.7 Feature Flag e Fallback Resiliente

1. **Feature Flag `ENABLE_DYNAMIC_ROUTING`:**
   - Controlada no backend (`settings.ENABLE_DYNAMIC_ROUTING = False` por padrão em
     ambientes implantados até staging autorizado) e exposta ao frontend no payload
     de `/bootstrap`.
   - Quando desativada (`false`), a interface do Expo oculta os botões *"Minha Localização"* e *"Escolher no mapa"*, operando exclusivamente com as origens oficiais.

2. **Fluxo de Fallback no Cliente:**
   - Se a requisição dinâmica falhar (timeout, fora da área de cobertura ou erro de rede):
     1. A UI exibe mensagem acessível (*"Não foi possível calcular o trajeto dinâmico. Exibindo ponto de partida oficial mais próximo."*).
     2. A interface automaticamente restaura o enquadramento e a seleção para a origem oficial mais conveniente (ex: Rodoviária ou Porto).

---

## 3. Plano de Benchmark e Gates de Ativação

A transição da proposta documental para a execução e produção seguirá dois marcos formais:

```text
[ECO-2308: Proposta ADR 0012] 
            │
            ▼
      [Gate H1: Aprovação do Modelo de Roteamento] ──> Desbloqueia ECO-2309 (Fake determinístico)
            │
      [ECO-2309 a ECO-2312: UI, GPS, Pins Dinâmicos com Fake]
            │
            ▼
      [ECO-2313: Benchmark Empírico OSRM vs. Google Routes]
            │
            ▼
      [Gate H3: Decisão do Provedor, Infraestrutura e Orçamento] ──> Desbloqueia ECO-2314 (Conector Real)
```

- **Gate H1 (Aprovação deste ADR):**
  - Homologação pelo Owner do modelo efêmero, da separação de rotas verificadas/sugeridas e do protocolo LGPD.
  - Autoriza o início de ECO-2309 com o conector Fake Determinístico.
- **Gate H3 (Aprovação do Provedor Real):**
  - Realizado na conclusão de ECO-2313.
  - Requer apresentação de relatório empírico de latência, cobertura de malha local em Santarém/Belterra e projeção de custo financeiro mensal.
  - Nenhuma chave de produção ou contratação de VPS/Cloud Run é realizada antes do registro do Gate H3.

---

## 4. Consequências Técnicas

### Positivas:
- **Segurança Jurídica e LGPD:** Elimina armazenamento desnecessário de dados de localização do usuário e garante transporte seguro via POST.
- **Isolamento de Banco:** Mantém `route_origins` e `route_geometries` limpos e restritos a dados editoriais homologados.
- **Desacoplamento de Fornecedor:** O aplicativo não conhece se a geometria veio do Google, OSRM ou Fake; consome apenas o contrato unificado do FastAPI.
- **Controle Orçamentário:** Rate limit, timeout e feature flag impedem custos inesperados em faturas de nuvem.

### Negativas / Limitações:
- Rotas sugeridas não verificadas podem sofrer com imprecisões de malha em áreas de praia com maré ou ramais sem pavimentação até que haja validação local contínua.
- Exige implementação de camada de roteamento sob demanda no FastAPI (`RoutingService` / `RoutingConnector`).

---

## 5. Decisões Homologadas pelo Owner (Gate H1 Aprovado em 2026-08-24)

1. **Modelo Efêmero e Privacidade (Opção 1.A - Aprovada):** Coordenadas de usuário trafegam exclusivamente via `POST` body, processadas em memória volátil e com descarte imediato, sem persistência em banco ou rastreamento em logs/telemetria.
2. **Interface Harmonizada com Selo SEMTUR (Opção 2.B Refinada - Aprovada):** Aviso informativo sutil no trajeto dinâmico sugerido, complementado pela exibição de **selo institucional SEMTUR** nos estabelecimentos/atores com vistoria e verificação oficial confirmada.
3. **Modo de Transporte Primário (Opção 3.A - Aprovada):** Modo `DRIVE` (automóvel) como padrão único inicial para segurança do visitante, postergando pedestre e cicloturismo.
4. **Estratégia de Desenvolvimento e Custos (Opção 4.A - Aprovada):** Utilização do conector Fake Determinístico (custo R$ 0,00, sem rede) para as tasks ECO-2309 a ECO-2312, mantendo a contratação de provedor real para o Gate H3 (ECO-2313).
