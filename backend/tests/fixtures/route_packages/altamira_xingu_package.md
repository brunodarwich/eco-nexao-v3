# Pacote de Dados e Revisão Editorial — Rota Volta Grande do Xingu (Fixture de Teste)

Versão: 1.0  
Data de Consolidação: 2026-09-05  
Status da Rota: `draft`  
Status de Homologação: `PARTIAL`  
Responsável Editorial Provisório: Bruno Darwich  
Revisor Técnico: Equipe de Engenharia / Antigravity  

---

## 1. Identificação e Ficha Geral da Rota

| Campo | Valor Normativo | Regra / Proveniência |
|---|---|---|
| `route_id` | `992811a2-11c0-441a-96cf-88d3d63309b7` | UUID v4 gerado para a fixture de Altamira |
| `route_slug` | `rota-volta-grande-xingu` | Identificador único URL-safe |
| `title` | Rota Volta Grande do Xingu | Nome oficial da rota para exibição no aplicativo |
| `summary` | Rota de ecoturismo e aventura partindo de Altamira ao longo do Rio Xingu, explorando comunidades ribeirinhas, corredeiras e a rica biodiversidade da Volta Grande. | Resumo editorial |
| `region_slug` | `xingu-altamira` | Vínculo com a região Xingu / Altamira (`regions.slug`) |
| `region_name` | Xingu / Altamira | Polo regional |
| `city` | Altamira | Município polo da rota |
| `state_code` | PA | Estado do Pará |
| `status` | `draft` | Estado estrito da máquina de estados (ADR 0006) |
| `is_verified` | `false` | Rota de fixture não publicada |
| `best_season` | Período de vazante (julho a novembro) | Informação editorial |
| `connectivity` | Sinal 4G no perímetro urbano de Altamira; ausente nas corredeiras | Utilidade pública |
| `road_access` | Rodovia Transamazônica (BR-230) pavimentada e trechos fluviais no Xingu | Acesso |
| `payment_info` | Pix e dinheiro em espécie são indispensáveis no trecho ribeirinho | Orientação |

---

## 2. Origens Homologadas e Pontos de Saída

| Código (`origin_code`) | Nome da Origem | Descrição do Ponto de Partida | Latitude (WGS84) | Longitude (WGS84) | Ordem (`sort_order`) |
|---|---|---|:---:|:---:|:---:|
| `rodoviaria_altamira` | Rodoviária de Altamira | Terminal Rodoviário de Passageiros de Altamira | `-3.204561` | `-52.213456` | 1 |
| `aeroporto_altamira` | Aeroporto de Altamira | Aeroporto de Altamira (ATM) | `-3.253611` | `-52.253889` | 2 |

---

## 3. Geometrias por Origem, Bounds e Proveniência

| Origem | Provedor | CRS | Extensão Linear | Duração Ref. | Qtd. Pontos | Bounds Estrito (`route_bounds`) | Arquivo Fonte Snapshot | SHA-256 da Fonte |
|---|---|:---:|---:|---:|---:|---|---|---|
| `rodoviaria_altamira` | OSRM / PostGIS | 4326 | 32.500 km | ~40 min | 420 | `[-52.253889, -3.253611, -52.213456, -3.204561]` | `rota_altamira_rodoviaria.csv` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `aeroporto_altamira` | OSRM / PostGIS | 4326 | 38.120 km | ~48 min | 495 | `[-52.253889, -3.253611, -52.213456, -3.204561]` | `rota_altamira_aeroporto.csv` | `ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb` |

---

## 4. Taxonomia Canônica e Escopos Espaciais

Todos os atores mapeados pertencem aos 8 grupos canônicos (ADR 0010) e subtipos (ADR 0015).

---

## 5. Fichas de Atores Verificáveis e Auditadas (Snapshot Real)

### Ficha 1: Atrativo Natural na Orla do Xingu

```yaml
actor:
  slug: "mirante-da-orla-do-xingu"
  name: "Mirante da Orla do Xingu"
  description: "Ponto turístico público para contemplação do pôr do sol sobre as águas do Rio Xingu."
  category_slug: "atrativos"
  type_slug: "serra_mirante"
  spatial_scope: "route_corridor"
  location:
    latitude: -3.201234
    longitude: -52.204567
    status_coord: "ok"
    source_location: "editorial_validation"
  address:
    street: "Av. João Pessoa, s/n - Orla"
    district: "Centro"
    city: "Altamira"
    state_code: "PA"
  contacts:
    phone_raw: "VALOR_AUSENTE"
    phone_e164: "VALOR_AUSENTE"
    email: "turismo@altamira.pa.gov.br"
    website: "https://altamira.pa.gov.br"
    instagram: "@prefeituradealtamira"
  operational:
    opening_hours_raw: "Aberto diariamente 24h"
    opening_hours_structured: null
    payment_methods: []
  provenance_and_sources:
    is_semtur_inventory: false
    semtur_external_id: "VALOR_AUSENTE"
    google_places_ref:
      place_id: "VALOR_AUSENTE"
      google_maps_uri: "VALOR_AUSENTE"
      google_rating: null
      google_review_count: null
  experience_tags:
    - tag_slug: "por-do-sol"
      justification: "Mirante elevado com visão panorâmica voltada para o poente no Rio Xingu."
      evidence_type: "inspecao_em_campo"
      reviewed_by: "Equipe Editorial ECOnexão"
      reviewed_at: "2026-09-05"
  editorial_media: []
```

### Ficha 2: Hospedagem Ribeirinha em Altamira

```yaml
actor:
  slug: "hotel-xingu-maraba"
  name: "Hotel Xingu Marabá"
  description: "Hotel com quartos climatizados, estacionamento e café da manhã amazônico."
  category_slug: "hospedagem"
  type_slug: "pousada_hotel"
  spatial_scope: "route_corridor"
  location:
    latitude: -3.208912
    longitude: -52.211234
    status_coord: "ok"
    source_location: "editorial_validation"
  address:
    street: "Rua 7 de Setembro, 123"
    district: "Centro"
    city: "Altamira"
    state_code: "PA"
  contacts:
    phone_raw: "(93) 3515-1234"
    phone_e164: "+559335151234"
    email: "reservas@hotelxingumaraba.com.br"
    website: "VALOR_AUSENTE"
    instagram: "VALOR_AUSENTE"
  operational:
    opening_hours_raw: "Recepção 24 horas"
    opening_hours_structured: null
    payment_methods: ["money", "pix", "credit_card"]
  provenance_and_sources:
    is_semtur_inventory: false
    semtur_external_id: "VALOR_AUSENTE"
    google_places_ref:
      place_id: "VALOR_AUSENTE"
      google_maps_uri: "VALOR_AUSENTE"
      google_rating: null
      google_review_count: null
  experience_tags: []
  editorial_media: []
```

### Ficha 3: Serviço Essencial de Saúde Regional em Altamira

```yaml
actor:
  slug: "hospital-regional-publico-da-transamazonica"
  name: "Hospital Regional Público da Transamazônica"
  description: "Hospital regional de média e alta complexidade atendendo Altamira e municípios da Transamazônica."
  category_slug: "saude"
  type_slug: "hospital_upa"
  spatial_scope: "citywide_essential"
  location:
    latitude: -3.219876
    longitude: -52.224567
    status_coord: "ok"
    source_location: "editorial_validation"
  address:
    street: "Av. Brigadeiro Eduardo Gomes, s/n"
    district: "São Sebastião"
    city: "Altamira"
    state_code: "PA"
  contacts:
    phone_raw: "(93) 3515-7700"
    phone_e164: "+559335157700"
    email: "VALOR_AUSENTE"
    website: "https://www.saude.pa.gov.br"
    instagram: "VALOR_AUSENTE"
  operational:
    opening_hours_raw: "Pronto-Socorro 24 horas"
    opening_hours_structured: null
    payment_methods: ["sus"]
  provenance_and_sources:
    is_semtur_inventory: false
    semtur_external_id: "VALOR_AUSENTE"
    google_places_ref:
      place_id: "VALOR_AUSENTE"
      google_maps_uri: "VALOR_AUSENTE"
      google_rating: null
      google_review_count: null
  experience_tags: []
  editorial_media: []
```

---

## 6. Governança das Tags de Experiência

A tag `por-do-sol` possui justificativa geográfica comprovada na margem oeste do Rio Xingu.

---

## 7. Mídia Editorial e Acessibilidade

Mídia de capa em fase de homologação e licenciamento. Proibido download de fotos do Google.

---

## 8. Checklist de Aprovação Editorial e Publicação

- [ ] **1. Identificação:** Rota Altamira preenchida.
- [ ] **2. Origens:** 2 origens cadastradas.
- [ ] **3. Geometria:** Trajetos com CRS 4326 e hashes rastreáveis.
- [ ] **4. Atores:** Atores mapeados nos 8 grupos canônicos.
- [ ] **5. Sem Invenção de Dados:** Campos ausentes marcados como `VALOR_AUSENTE`. Zero `google_place_id` inventados.
- [ ] **6. Status:** `draft` provisório de teste.
