# Pacote de Dados e Revisão Editorial — Rota Pindobal (Exemplo de Referência)

Versão: 1.1 (Revisão estrita de evidências)  
Data de Consolidação: 2026-09-05  
Status da Rota: `draft` (Em estruturação e validação editorial; **NÃO HOMOLOGADA / NÃO PUBLICÁVEL** como rota final)  
Status de Homologação: `PARTIAL` (Estrutura e geometrias comprovadas; dados editoriais e mídia operam como exemplos ilustrativos)  
Responsável Editorial Provisório: Bruno Darwich (Owner do Produto / ADR 0006)  
Revisor Técnico: Equipe de Engenharia / Antigravity  

---

## 1. Identificação e Ficha Geral da Rota

| Campo | Valor Normativo | Regra / Proveniência |
|---|---|---|
| `route_id` | `771966a3-05c0-431a-96cf-71d3d63309a6` | UUID v4 estável gerado na promoção de base |
| `route_slug` | `rota-pindobal` | Identificador único URL-safe |
| `title` | Rota Pindobal — Praias e Encantos do Tapajós | Nome oficial da rota para exibição no aplicativo |
| `summary` | Rota ecoturística saindo de Santarém rumo à Praia de Pindobal em Belterra, contornando o Rio Tapajós e passando pelo vilarejo histórico de Alter do Chão. O trajeto oferece rica gastronomia tapajônica, praias fluviais de areias brancas, comunidades tradicionais produtoras de cuias e artesanato indígena, além de opções de hospedagem integrada à natureza. | Resumo editorial curado para a tela inicial e cards de catálogo |
| `region_slug` | `santarem-belterra` | Vínculo com a região homologada no banco (`regions.slug`) |
| `region_name` | Santarém / Belterra | Polo municipal de atuação |
| `city` | Belterra | Município de destino da praia |
| `state_code` | PA | Estado do Pará |
| `status` | `draft` | Estado estrito da máquina de estados (ADR 0006). Não marcar published/review até homologação de dados reais. |
| `is_verified` | `false` | A rota em si não está homologada para publicação pública final. |
| `best_season` | Período de seca dos rios amazônicos (agosto a janeiro), quando surgem as extensas faixas de areia branca no Rio Tapajós. | Informação editorial descritiva |
| `connectivity` | Sinal 4G/3G nas saídas urbanas de Santarém e na vila de Alter do Chão; sinal intermitente ou ausente em trechos da rodovia e ramais de acesso. | Informação de utilidade pública |
| `road_access` | Pavimentado via Rodovia Everaldo Martins (PA-457) até proximidades de Alter do Chão, seguido de ramal de terra até a praia. | Infraestrutura viária |
| `payment_info` | Estabelecimentos maiores aceitam cartões e Pix; recomenda-se portar dinheiro em espécie para comunidades tradicionais e barracas isoladas. | Orientação ao viajante |

---

## 2. Origens Homologadas e Pontos de Saída

Origens fixas cadastradas no contrato de rota, com coordenadas exatas em WGS84:

| Código (`origin_code`) | Nome da Origem | Descrição do Ponto de Partida | Latitude (WGS84) | Longitude (WGS84) | Ordem (`sort_order`) |
|---|---|---|:---:|:---:|:---:|
| `porto` | Porto de Santarém | Terminal Hidroviário / Porto Fluvial de Santarém (Cais) | `-2.428482` | `-54.701835` | 1 |
| `aeroporto` | Aeroporto de Santarém | Aeroporto Maestro Wilson Fonseca (Terminal de Passageiros) | `-2.424780` | `-54.785830` | 2 |
| `rodoviaria` | Rodoviária de Santarém | Terminal Rodoviário de Santarém | `-2.443185` | `-54.730652` | 3 |

---

## 3. Geometrias por Origem, Bounds e Proveniência

Todas as três origens possuem trajeto finalizado no ponto comum da Praia de Pindobal (`latitude: -2.558521`, `longitude: -54.978506`), estritamente vinculadas aos arquivos e hashes SHA-256 do snapshot imutável `teste-rota`:

| Origem | Provedor | CRS | Extensão Linear | Duração Ref. | Qtd. Pontos | Bounds Estrito (`route_bounds`) | Arquivo Fonte Snapshot | SHA-256 da Fonte |
|---|---|:---:|---:|---:|---:|---|---|---|
| `porto` | OSRM / PostGIS | 4326 | 45.22905 km | ~55 min | 884 | `[-54.978506, -2.558521, -54.701835, -2.424780]` | `rota_porto_OSRM_01.csv` | `15c557a406bc6ebd87d4f8706d15c80127fc98b416d535ae57b4454fc991b6cb` |
| `aeroporto` | OSRM / PostGIS | 4326 | 41.45154 km | ~50 min | 777 | `[-54.978506, -2.558521, -54.730652, -2.424780]` | `rota_aeroporto_OSRM_01.csv` | `8cae67ad9d00d6056733787ed41c940d1ba68490dc5bd5e60c6cb1c1f1d15776` |
| `rodoviaria` | OSRM / PostGIS | 4326 | 42.31851 km | ~52 min | 866 | `[-54.978506, -2.558521, -54.701835, -2.424780]` | `rota_rodoviaria_OSRM_01.csv` | `fd21e0df95368553aa81aaff22d630e9cffd00c1ef3d0feef6fb5573fc08c70b` |

*Observação Espacial (ADR 0011):* As coordenadas de `route_bounds` acima delimitam estritamente o corredor da rota para controle de câmera do mapa, prevenindo distorção causada por hospitais ou delegacias situados na malha urbana central.

---

## 4. Estatísticas de Atores e Contagens de Controle

Conforme auditado em ECO-2501 e calibrado a 1.000 metros de buffer em ECO-2506:

- **Total de registros brutos SEMTUR no município:** 674 registros auditados (529 com coordenadas válidas; 145 com coordenadas ausentes preservados em raw).
- **Atores associados ao corredor turístico da Rota Pindobal (1.000m):**
  - Origem Porto (45,23 km): 312 atores vinculados;
  - Origem Aeroporto (41,45 km): 156 atores vinculados;
  - Origem Rodoviária (42,32 km): 209 atores vinculados;
  - Atores únicos no corredor (união das origens): 318 estabelecimentos.
- **Serviços Essenciais Regionais (`citywide_essential` — Saúde e Segurança):**
  - Hospitais e UPAs no polo: 38 (exibidos na malha da cidade via `city_bounds`);
  - UBS e postos de saúde: 33;
  - Delegacias e corpos de bombeiros: 20.
- **Deduplicação e Candidatos Reconciliados (ECO-2509):**
  - Correspondências exatas/determinísticas (Tiers 1 a 3): vinculados de forma idempotente em `actor_external_refs`;
  - Candidatos fuzzy ambíguos: 53 casos retidos na fila `reconciliation_candidates` para análise editorial humana, **sem auto-merge**.
  - Registros Google legados sem Place ID: 737 marcados com `external_id_missing: true`.

---

## 5. Fichas de Atores Verificáveis e Auditadas (Snapshot Real)

Abaixo estão fichas de estabelecimentos e pontos de interesse extraídos diretamente do inventário institucional SEMTUR e do recorte verificado de Pindobal, com rastreabilidade explícita a páginas/linhas e nulidade fiel:

### Ficha 1: Hospedagem em Pindobal (SEMTUR Auditado — ID 40)

```yaml
actor:
  slug: "pousada-casa-de-vidro-pindobal"
  name: "Pousada Casa de Vidro"
  description: "Pousada com 08 apartamentos com 20 leitos, 06 chalés com leitos e 06 redes, wi-fi."
  category_slug: "hospedagem"
  type_slug: "pousada_hotel"
  spatial_scope: "route_corridor"
  location:
    latitude: -2.563457
    longitude: -54.974103
    status_coord: "ok"
    source_location: "semtur_inventory" # Extraído de coordenadas_geograficas do snapshot SEMTUR
  address:
    street: "Estrada do Pindobal - Pindobal - Limites com Alter do Chão"
    district: "Praia do Pindobal"
    city: "Belterra"
    state_code: "PA"
  contacts:
    phone_raw: "VALOR_AUSENTE" # Não consta no cadastro original
    phone_e164: "VALOR_AUSENTE"
    email: "paulocruz012@gmail.com" # Verificado no texto_bruto SEMTUR
    website: "VALOR_AUSENTE"
    instagram: "@espacocasadevidropindobal" # Verificado no cadastro SEMTUR
  operational:
    opening_hours_raw: "VALOR_AUSENTE" # Não informado no snapshot SEMTUR
    opening_hours_structured: null
    payment_methods: []
  provenance_and_sources:
    is_semtur_inventory: true
    semtur_external_id: "semtur_p57_id40" # Página 57 / ID 40 do recorte
    google_places_ref:
      place_id: "VALOR_AUSENTE"
      google_maps_uri: "VALOR_AUSENTE"
      google_rating: null
      google_review_count: null
  experience_tags: [] # Nenhuma tag de experiência atestada com evidência física nesta fase
  editorial_media: [] # Mídia real do estabelecimento pendente de envio e licenciamento formal
```

### Ficha 2: Hospedagem no Eixo de Acesso a Pindobal (SEMTUR Auditado — ID 95)

```yaml
actor:
  slug: "pousada-acaire-de-alter"
  name: "Pousada Açairé de Alter"
  description: "Dispomos de 08 apartamentos com 28 leitos casais e individual, wi-fi, café da manhã."
  category_slug: "hospedagem"
  type_slug: "pousada_hotel"
  spatial_scope: "route_corridor"
  location:
    latitude: -2.519528
    longitude: -54.953697
    status_coord: "ok"
    source_location: "semtur_inventory"
  address:
    street: "Estrada do Pindobal, 170 (Próximo ao çairodromo)"
    district: "Alter do Chão"
    city: "Santarém"
    state_code: "PA"
  contacts:
    phone_raw: "(93) 98817-1709" # Auditado na SEMTUR
    phone_e164: "+5593988171709"
    email: "VALOR_AUSENTE"
    website: "VALOR_AUSENTE"
    instagram: "@pousadacairedealter" # Auditado na SEMTUR
  operational:
    opening_hours_raw: "VALOR_AUSENTE"
    opening_hours_structured: null
    payment_methods: []
  provenance_and_sources:
    is_semtur_inventory: true
    semtur_external_id: "semtur_p73_id95"
    google_places_ref:
      place_id: "VALOR_AUSENTE"
      google_maps_uri: "VALOR_AUSENTE"
      google_rating: null
      google_review_count: null
  experience_tags: []
  editorial_media: []
```

### Ficha 3: Gastronomia e Alimentação (SEMTUR Auditado — ID 137)

```yaml
actor:
  slug: "restaurante-casa-do-saulo-beloalter"
  name: "Restaurante Casa do Saulo - Beloalter Hotel"
  description: "Espaço gastronômico com capacidade para 150 pessoas, especializado em culinária regional."
  category_slug: "alimentacao"
  type_slug: "restaurante"
  spatial_scope: "route_corridor"
  location:
    latitude: -2.506417
    longitude: -54.944556
    status_coord: "ok"
    source_location: "semtur_inventory"
  address:
    street: "Rua Pedro Teixeira, 500 - Carauary"
    district: "Alter do Chão"
    city: "Santarém"
    state_code: "PA"
  contacts:
    phone_raw: "VALOR_AUSENTE"
    phone_e164: "VALOR_AUSENTE"
    email: "VALOR_AUSENTE"
    website: "VALOR_AUSENTE"
    instagram: "VALOR_AUSENTE"
  operational:
    opening_hours_raw: "7h às 21h (diariamente)" # Constando expressamente no snapshot SEMTUR
    opening_hours_structured:
      regular:
        - days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
          open: "07:00"
          close: "21:00"
    payment_methods: []
  provenance_and_sources:
    is_semtur_inventory: true
    semtur_external_id: "semtur_p96_id137"
    google_places_ref:
      place_id: "VALOR_AUSENTE"
      google_maps_uri: "VALOR_AUSENTE"
      google_rating: null
      google_review_count: null
  experience_tags:
    - tag_slug: "culinaria-regional"
      justification: "Referência gastronômica regional catalogada no inventário municipal da SEMTUR."
      evidence_type: "declaracao_institucional"
      reviewed_by: "Equipe Editorial ECOnexão"
      reviewed_at: "2026-09-05"
  editorial_media: []
```

### Ficha 4: Artesanato Local Comunitário (SEMTUR Auditado — ID 6)

```yaml
actor:
  slug: "arariba-tropical-artesanato"
  name: "Araribá Tropical"
  description: "Comércio de artesanato, moda praia, bijuterias, pedra semipreciosa, sandálias, camisas, bolsas, fibra de buriti e cerâmica tapajônica."
  category_slug: "artesanato"
  type_slug: "artesanato_local"
  spatial_scope: "route_corridor"
  location:
    latitude: -2.503046
    longitude: -54.952359
    status_coord: "ok"
    source_location: "semtur_inventory"
  address:
    street: "Tv. Antônio Agostino Lobato, s/n - Centro"
    district: "Alter do Chão"
    city: "Santarém"
    state_code: "PA"
  contacts:
    phone_raw: "VALOR_AUSENTE"
    phone_e164: "VALOR_AUSENTE"
    email: "contato@araribah.com.br" # Auditado na SEMTUR
    website: "https://www.araribah.com.br" # Normalizado com https
    instagram: "VALOR_AUSENTE"
  operational:
    opening_hours_raw: "VALOR_AUSENTE"
    opening_hours_structured: null
    payment_methods: []
  provenance_and_sources:
    is_semtur_inventory: true
    semtur_external_id: "semtur_p36_id6"
    google_places_ref:
      place_id: "VALOR_AUSENTE"
      google_maps_uri: "VALOR_AUSENTE"
      google_rating: null
      google_review_count: null
  experience_tags: []
  editorial_media: []
```

### Ficha 5: Serviço Essencial de Saúde Regional (`citywide_essential` — Auditado)

```yaml
actor:
  slug: "hospital-municipal-de-santarem"
  name: "Hospital Municipal de Santarém"
  description: "Unidade hospitalar de urgência e emergência pública atendendo a região metropolitana e polo regional."
  category_slug: "saude"
  type_slug: "hospital_upa"
  spatial_scope: "citywide_essential"
  location:
    latitude: -2.4251475
    longitude: -54.7144829
    status_coord: "ok"
    source_location: "snapshot_infraestrutura_legado" # Fonte: empresas_infraestrutura_rotas.csv
  address:
    street: "Av. Pres. Vargas, 1539 - Santa Clara"
    district: "Santa Clara"
    city: "Santarém"
    state_code: "PA"
  contacts:
    phone_raw: "(92) 3523-2175" # Constante no snapshot legado
    phone_e164: "+559235232175"
    email: "VALOR_AUSENTE"
    website: "VALOR_AUSENTE"
    instagram: "VALOR_AUSENTE"
  operational:
    opening_hours_raw: "Atendimento 24 horas"
    opening_hours_structured:
      regular:
        - days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
          open: "00:00"
          close: "23:59"
    payment_methods: ["sus_public_service"]
  provenance_and_sources:
    is_semtur_inventory: false # Registro de infraestrutura Google legado, sem vínculo direto comprovado em inventário SEMTUR
    semtur_external_id: "VALOR_AUSENTE"
    google_places_ref:
      place_id: "VALOR_AUSENTE" # Ausente no snapshot legado; requer nova coleta para place_id canônico
      google_maps_uri: "VALOR_AUSENTE" # URI genérica removida por não possuir comprovação contratual
      google_rating: null # Removido por ausência de coleta ponta a ponta
      google_review_count: null
  experience_tags: []
  editorial_media: []
```

---

## 6. Mídias da Rota e Regras de Licença

| Mídia / Finalidade | Caminho Relativo | Alt Text Acessível | Crédito | Licença | Status da Mídia |
|---|---|---|---|---|:---:|
| Capa da Rota (`hero`) | `editorial-media/routes/rota-pindobal/pindobal_capa.webp` | Faixa de areia branca da praia de Pindobal banhada pelas águas azuis-esverdeadas do Rio Tapajós sob sol forte com cabanas de palha | Acervo Fotográfico SEMTUR Santarém | `SEMTUR_INSTITUTIONAL` | Exemplo ilustrativo (binário físico pendente de staging) |
| Card de Feed (`card`) | `editorial-media/routes/rota-pindobal/pindobal_card.webp` | Vista de quiosques de praia em Pindobal com barcos ancorados à beira do rio | Fotografia Editorial ECOnexão | `CC-BY-4.0` | Exemplo ilustrativo |
| Miniatura de Pin (`thumb`) | `editorial-media/routes/rota-pindobal/pindobal_thumb.webp` | Cabana típica de palha na areia clara da praia | Fotografia Editorial ECOnexão | `CC-BY-4.0` | Exemplo ilustrativo |

*Garantia de Conformidade:*
- Mídias descritas representam especificações para a esteira editorial e Publish Guard;
- Nenhuma foto Google foi baixada ou armazenada localmente/no Storage (respeito integral ao ADR 0008 e ADR 0016).

---

## 7. Checklist de Avaliação Editorial — Rota Pindobal

- [x] **1. Identificação Geral:** Ficha preenchida com `status: draft` e `is_verified: false` refletindo que os dados editoriais são exemplos de referência técnica e não rota final homologada.
- [x] **2. Origens Homologadas:** Porto, Aeroporto e Rodoviária validados com coordenadas WGS84 auditadas.
- [x] **3. Geometrias OSRM:** 3 arquivos vinculados ao manifesto imutável por hash SHA-256 e extensões conferidas (45,23 km, 41,45 km e 42,32 km).
- [x] **4. Mapeamento Taxonômico:** 100% dos atores distribuídos entre as 8 categorias canônicas e seus subtipos específicos (ADR 0010 / ADR 0015).
- [x] **5. Valores Ausentes Explícitos:** 100% dos campos sem fonte primária no snapshot foram estritamente marcados como `VALOR_AUSENTE` ou `null` (zero dados alucinados).
- [x] **6. Segregação de Fontes:** Selo `SEMTUR` restrito exclusivamente aos registros originários com referência de página/ID no inventário municipal. Registros de infraestrutura comercial marcados como `is_semtur_inventory: false`.
- [x] **7. Sem URLs Artificiais ou Ratings Google:** Todas as URLs com identificadores comerciais não autorizados e ratings sem Place ID comprovado foram expurgados.
- [x] **8. Tags de Experiência:** Tags não aplicáveis foram omitidas; apenas tags com justificativa e evidência institucional declarada foram mantidas.
- [x] **9. Estado de Conclusão:** O pacote está pronto como especificação técnica, mas a publicação da rota permanece bloqueada aguardando o carregamento dos dados definitivos em ECO-2605 / ECO-2621.
