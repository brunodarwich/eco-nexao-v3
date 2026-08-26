# ADR 0011 — Camadas Espaciais do Mapa: Corredor de Rota e Serviços da Cidade

Status: aceito  
Data: 2026-08-24  
Decisores: Equipe de Desenvolvimento ECOnexão / Owner do Projeto  
Tasks relacionadas: ECO-2301, ECO-2305, ECO-2306, ECO-2307, ECO-2312  

---

## 1. Contexto e Problema

Na versão 2 do mapa dinâmico do ECOnexão, a experiência cartográfica precisa harmonizar duas necessidades distintas e potencialmente conflitantes do turista:

1. **Exploração da Rota (Corredor Turístico)**: Ao selecionar uma rota (por exemplo, Santarém → Praia de Pindobal), o usuário deseja focar no trajeto, descobrindo atrativos naturais, barracas de praia, restaurantes, pousadas e pontos de artesanato que estão diretamente acessíveis ao longo do percurso.
2. **Serviços Essenciais e Segurança (Cobertura Regional/Municipal)**: Ao mesmo tempo, o usuário em viagem necessita de acesso imediato a serviços de utilidade pública e socorro emergencial — tais como hospitais, Unidades Básicas de Saúde (UBS), farmácias, delegacias de polícia e bases de bombeiros — que frequentemente estão concentrados na malha urbana central (ex: centro de Santarém ou sede de Belterra), fora do corredor imediato da estrada.

### O Problema do Enquadramento de Câmera (`route_bounds` vs. `content_bounds`)

Se o cálculo de enquadramento (bounding box) da rota expandir-se automaticamente para abraçar todos os pontos de interesse municipais cadastrados na região:
- Um hospital situado a 15 km do trajeto forçará um *zoom-out* excessivo.
- A linha da rota de 45 km tornar-se-á uma linha fina e ilegível no dispositivo móvel, destruindo a clareza e usabilidade da navegação turística.

Portanto, faz-se necessária uma arquitetura espacial formalizada em camadas independentes, que defina claramente os critérios de pertencimento de atores, o isolamento dos limites de câmera e a estratégia de controle de densidade visual.

---

## 2. Decisão Proposta

### 2.1 Classificação das Camadas Espaciais e Categorias

Padronizam-se três comportamentos de camada para os atores (`actors`):

| Comportamento da Camada | Categorias Canônicas Associadas (ADR 0010) | Critério Espacial de Inclusão | Modos de Exibição |
| :--- | :--- | :--- | :--- |
| **`route_corridor`** (Ao longo da rota) | `alimentacao`, `atrativos`, `hospedagem`, `artesanato`, `outros` | Interseção no buffer da rota (`ST_DWithin(actor.location, route_geom, buffer_m)`) vinculado via `route_actors`. | Visível no Modo "Rota" e no Modo "Cidade". |
| **`citywide_essential`** (Serviços da cidade) | `saude`, `seguranca` | Vínculo territorial à região ativa (`actors.region_id = active_region_id`), sem restrição de distância do percurso. | Visível no Modo "Cidade" (e sob demanda/filtro no Modo "Rota" sem distorcer o zoom). |
| **`both`** (Infraestrutura mista / Modais) | `transporte` | No corredor: postos de apoio e paradas na rodovia vinculados à rota.<br>Na cidade: terminais rodoviários, portos, aeroportos e pontos de táxi centrais. | Participa de ambos os modos com semântica contextual. |

---

### 2.2 Relação Ator × Região: Análise Comparativa de Alternativas

Para suportar consultas territoriais da cidade inteira (`citywide_essential` e `both`), foram comparadas quatro abordagens arquiteturais para relacionar um ator (`Actor`) à sua região (`Region`):

| Alternativa | Descrição | Vantagens | Desvantagens / Riscos | Avaliação Técnica |
| :--- | :--- | :--- | :--- | :--- |
| **Opção A: `actors.region_id` (Coluna direta com FK)** | Adição da coluna `region_id UUID REFERENCES app_private.regions(id)` na tabela `actors`, com índice `idx_actors_region_id`. | 1. Integridade referencial garantida pelo PostgreSQL.<br>2. Consulta `O(1)` indexada de máxima performance (`SELECT ... WHERE region_id = :id`).<br>3. Consistência com o modelo existente (`routes.region_id`). | Exige migração de schema e atualização no script de ingestão/seed. | **Recomendada (Opção Proposta)** |
| **Opção B: Tabela Associativa `actor_regions` (N:N)** | Criação de tabela relacional `actor_regions (actor_id, region_id)`. | Permite que um ator pertença a múltiplas regiões sobrepostas. | Complexidade relacional desnecessária no estágio atual (as regiões do ECOnexão são polos municipais distintos, e.g., Santarém/Belterra). | Descartada por sobrecarga operacional. |
| **Opção C: Consulta Espacial Pura (`ST_Contains` / Polígono)** | `regions` armazena geometria poligonal `boundary geography(Polygon)` e a associação é feita por contenção espacial em runtime. | Associação puramente geométrica sem dependência de FK relacional. | 1. Exige polígonos vetoriais oficiais delimitados (inexistentes no snapshot SEMTUR).<br>2. Custo computacional elevado em endpoints de alta frequência.<br>3. Risco de falha com coordenadas imprecisas na fronteira fluvial/terrestre. | Descartada para runtime; mantida como possibilidade para pré-processamento offline. |
| **Opção D: Herança Transitiva da Rota (`route_actors` → `routes.region_id`)** | Inferir a região do ator a partir das rotas às quais ele está associado. | Não altera o schema de `actors`. | Atores essenciais da cidade que **não** fazem parte de nenhuma rota turística específica ficariam órfãos e inacessíveis. | Descartada por inconsistência funcional. |

**Proposta**: Adotar a **Opção A** (`actors.region_id`), implementando a respectiva migration SQL em `ECO-2306` com preenchimento retroativo a partir do snapshot institucional.

---

### 2.3 Enquadramento de Câmera: `route_bounds` vs. `content_bounds`

Para evitar distorção visual da rota durante a navegação, estabelece-se a seguinte regra estrita de cálculo de enquadramento:

1. **`route_bounds` (Enquadramento Padrão da Rota)**:
   - Calculado **exclusivamente** a partir das coordenadas da `geometry` da rota (Linestring) somado a uma margem de segurança (*padding*) do corredor turístico.
   - **Regra de ouro**: A presença ou ativação de serviços essenciais de saúde/segurança em pontos distantes da cidade **nunca** altera o valor de `route_bounds`.
2. **`content_bounds` / `city_bounds` (Enquadramento Regional Amplo)**:
   - Calculado a partir da extensão geográfica total de todos os atores e serviços cadastrados na região ativa, ou pelo centro/raio municipal da região.
   - Utilizado **somente** quando o usuário acionar voluntariamente o modo de câmera "Ver Cidade".

O backend entregará ambos os envelopes no payload unificado de mapa (`GET /routes/{id}/map`):
- `bounds`: correspondente a `route_bounds`.
- `city_bounds`: correspondente a `content_bounds` da região.

---

### 2.4 Modos de Câmera e Comportamento de Interface (UX)

O componente de mapa suportará dois modos de câmera explícitos:

1. **Modo 'Rota' (Padrão ao acessar a tela do mapa)**:
   - Câmera ajustada em `route_bounds`.
   - Exibe a linha da rota, as origens verificadas e os marcadores do corredor (`route_corridor`).
   - Se o usuário filtrar por "Saúde" ou "Segurança" enquanto estiver no modo 'Rota', os pins correspondentes visíveis na extensão atual aparecem; se o ponto estiver fora da visão, a interface oferece o botão contextual *"Ver serviços na cidade"*.
2. **Modo 'Cidade' (Acionado pelo seletor "Ver Cidade")**:
   - Transição suave da câmera para `city_bounds`.
   - Mantém a linha da rota desenhada em segundo plano (preservando o contexto).
   - Exibe toda a malha de serviços essenciais da cidade e atrativos regionais.
   - Botão flutuante acessível *"Voltar para a Rota"* restaura imediatamente o enquadramento em `route_bounds`.

---

### 2.5 Parâmetros Editoriais de Raios e Buffers (Sem Números Mágicos)

Os raios do corredor espacial não serão embutidos como números mágicos fixos no código-fonte, mas parametrizados no nível de aplicação/configuração com possibilidade de override editorial:

- **Buffer Padrão Global**: `ROUTE_CORRIDOR_BUFFER_METERS = 1000` (1,0 km de cada lado da linha da rota).
- **Tipologia de Calibração Editorial**:
  - *Corredor Urbano / Alta Densidade*: 500 metros.
  - *Corredor Rodoviário Turístico (Padrão Pindobal)*: 1.000 a 1.500 metros.
  - *Corredor Rural / Ecoturismo Extensivo*: 2.000 a 3.000 metros.
- **Implementação**: O serviço PostGIS aceitará o parâmetro `buffer_m` com fallback para a configuração padrão (`settings.DEFAULT_ROUTE_CORRIDOR_BUFFER_M`).

---

### 2.6 Densidade e Limite Inicial de Pins (Sem Novas Dependências)

Para assegurar alta performance e renderização estável tanto no Expo (Android/iOS) quanto no Web (Leaflet/MapLibre), descarta-se a instalação de bibliotecas externas complexas de clustering neste momento. A gestão de densidade visual será realizada através de:

1. **Teto Server-Side de Pins (`limit = 200`)**: O payload de mapa transporta no máximo 200 marcadores por requisição.
2. **Priorização e Destaque Editorial**: Ordenação por `is_featured DESC`, `green_badge_status DESC`, `sort_order ASC`, garantindo que os estabelecimentos mais relevantes tenham prioridade na renderização caso o teto seja atingido.
3. **Filtragem Rápida por Chips (Client-Side)**: A barra de filtros de categorias (entregue em ECO-2304) permite ao usuário isolar categorias específicas, reduzindo a densidade visual típica para 10 a 30 pins simultâneos.
4. **Padronização Tátil**: Marcadores acessíveis de 44x44 dp com espaçamento e z-index controlado para seleção unívoca.

---

## 3. Consequências Técnicas

A partir da homologação deste ADR:

- **ECO-2306 (Backend de Camadas Estáticas & PostGIS)**:
  - Adição da coluna `region_id UUID` na tabela `actors` via migration versionada Supabase.
  - Atualização do repositório/serviço `TerritorialService` para suportar consultas com buffer dinâmico de rota e consultas de serviços municipais (`citywide_essential`).
  - Atualização do endpoint `GET /api/v1/routes/{id}/map` para retornar `bounds` (rota), `city_bounds` (região), legenda consolidada e flags de camada por pin (`layer: 'corridor' | 'city'`).
- **ECO-2307 (Interface Rota × Cidade no Frontend)**:
  - Implementação do controle de modos de câmera ("Rota" vs. "Cidade") no `MapAdapter`.
  - Transições animadas e botão acessível para alternar/restaurar enquadramentos sem perda de estado.
- **ECO-2312 (Pins na Geometria Dinâmica)**:
  - Reutilização da lógica de corredor e serviços municipais para origens dinâmicas transitórias calculadas em tempo de execução.

---

## 4. Decisões Submetidas à Homologação do Owner (Gate H2b)

Submetem-se à decisão do Owner do Projeto:

1. **Aprovação da Separação de Camadas (Opção Proposta)**:
   - Separar formalmente o mapa em `route_corridor` (alimentação, atrativos, hospedagem, artesanato, outros) e `citywide_essential` (saúde, segurança), com `transporte` em modo híbrido.
2. **Aprovação do Vínculo Relacional `actors.region_id` (Opção A)**:
   - Adicionar chave estrangeira direta entre ator e região para viabilizar serviços municipais sem depender de polígonos complexos ou herança de rotas.
3. **Aprovação do Isolamento de Câmera (`route_bounds` estrito)**:
   - Garantir que serviços da cidade nunca alterem o enquadramento padrão da rota, utilizando `city_bounds` apenas sob solicitação do usuário no modo "Ver Cidade".
4. **Aprovação dos Parâmetros de Buffer e Limite de Pins**:
   - Buffer padrão de 1.000m para a Rota Pindobal e teto de 200 pins sem introdução de novas bibliotecas de clustering.
