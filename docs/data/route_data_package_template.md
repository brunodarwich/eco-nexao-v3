# Template Normativo — Pacote de Dados e Revisão de Rota

Versão: 1.0  
Finalidade: Padronizar o levantamento, a curadoria editorial, a validação de dados e o checklist de publicação de cada rota turística do ecossistema ECOnexão, permitindo que a equipe humana ou assistentes de IA preparem a base para ingestão segura e idempotente sem inventar conteúdo.

---

## 1. Identificação e Ficha Geral da Rota

| Campo | Obrigatório? | Descrição / Regra | Preenchimento |
|---|:---:|---|---|
| `route_id` | Sim | UUID estável gerado ou atribuído na ingestão | `[UUID v4 ou "gerado_na_ingestao"]` |
| `route_slug` | Sim | Identificador textual URL-safe minúsculo (ex: `rota-pindobal`) | `[slug-da-rota]` |
| `title` | Sim | Nome oficial/editorial da rota para exibição no app | `[Título da Rota]` |
| `summary` | Sim | Resumo descritivo da experiência (1 a 3 parágrafos curtos) | `[Texto descritivo]` |
| `region_slug` | Sim | Slug da região à qual a rota pertence (`regions.slug`) | `[slug-da-regiao]` |
| `region_name` | Sim | Nome legível da região (ex: `Santarém / Belterra`) | `[Nome da Região]` |
| `city` | Sim | Município polo / principal de destino | `[Município]` |
| `state_code` | Sim | UF com 2 caracteres (ex: `PA`) | `[UF]` |
| `status` | Sim | Estado da rota (`draft`, `review`, `published`, `archived`) | `draft` |
| `is_verified` | Sim | Flag booleana de verificação técnica da rota | `false` |
| `best_season` | Não | Melhor época/estação para visitação | `[Texto ou "VALOR_AUSENTE"]` |
| `connectivity` | Não | Cobertura de sinal de telefonia/internet móvel no percurso | `[Texto ou "VALOR_AUSENTE"]` |
| `road_access` | Não | Condições de rodovia/acesso (asfalto, terra, ramal, fluvial) | `[Texto ou "VALOR_AUSENTE"]` |
| `payment_info` | Não | Informações gerais sobre aceitação de cartões/Pix/dinheiro | `[Texto ou "VALOR_AUSENTE"]` |

---

## 2. Origens Homologadas e Pontos de Saída

Cada rota possui um conjunto fechado de origens homologadas (pontos de chegada e nós de transporte conhecidos). Toda origem deve possuir coordenadas verificadas em WGS84 (`Point`, SRID 4326).

| Código (`origin_code`) | Nome da Origem (`origin_name`) | Descrição do Ponto de Partida | Latitude (WGS84) | Longitude (WGS84) | Ordem (`sort_order`) |
|---|---|---|:---:|:---:|:---:|
| `[codigo_origem_1]` | `[Nome Amigável 1]` | `[Descrição do terminal/ponto]` | `[Lat]` | `[Lng]` | 1 |
| `[codigo_origem_2]` | `[Nome Amigável 2]` | `[Descrição do terminal/ponto]` | `[Lat]` | `[Lng]` | 2 |
| `[codigo_origem_3]` | `[Nome Amigável 3]` | `[Descrição do terminal/ponto]` | `[Lat]` | `[Lng]` | 3 |

*Regra de Ouro:* Origens canônicas fixas são pontos geográficos reais de partida. Não inventar coordenadas de origens; se ausente, registrar `VALOR_AUSENTE` e bloquear publicação da origem correspondente.

---

## 3. Geometrias por Origem, Bounds e Proveniência

Para cada origem cadastrada na Seção 2, deve haver a definição do trajeto até o ponto de destino comum da rota.

| Código da Origem | Provedor (`provider`) | CRS / SRID | Ponto Inicial (Lat, Lng) | Ponto Final Comum (Lat, Lng) | Distância Esperada (km ou m) | Duração Estimada (min ou s) | Qtd. de Pontos da Geometria | Bounding Box (`[minLng, minLat, maxLng, maxLat]`) | Arquivo Fonte / Proveniência | Hash SHA-256 da Fonte |
|---|---|:---:|---|---|---:|---:|---:|---|---|---|
| `[codigo_1]` | `osrm` ou `google_routes` | 4326 | `[Lat, Lng]` | `[Lat, Lng]` | `[dist]` | `[dur]` | `[n]` | `[bounds]` | `[nome_arquivo]` | `[sha256]` |
| `[codigo_2]` | `osrm` ou `google_routes` | 4326 | `[Lat, Lng]` | `[Lat, Lng]` | `[dist]` | `[dur]` | `[n]` | `[bounds]` | `[nome_arquivo]` | `[sha256]` |

*Requisitos Técnicos:*
- As sequências de coordenadas formam uma `LineString` no padrão `(longitude, latitude)` em WGS84 (SRID 4326).
- Bounds devem conter `route_bounds` estrito (linha + padding), isolado de serviços urbanos municipais distantes (conforme ADR 0011).
- Fonte da geometria deve ser rastreável por nome de arquivo e hash imutável.

---

## 4. Taxonomia Canônica e Escopos Espaciais

Todos os estabelecimentos e pontos de interesse (atores) associados à rota devem obrigatoriamente pertencer a um dos 8 grupos canônicos protegidos (ADR 0010) e a um subtipo específico homologado (ADR 0015):

1. **`alimentacao`** (cor `#D97706`, ícone `utensils`, escopo `route_corridor`): `restaurante`, `bar_vida_noturna`, `barraca_praia`, `cafe_lanchonete`, `mercado_conveniencia` (escopo `both`), `feira_livre` (escopo `both`).
2. **`atrativos`** (cor `#059669`, ícone `compass`, escopo `route_corridor`): `atrativo_natural`, `praia_fluvial`, `ilha`, `serra_mirante`, `unidade_conservacao` (escopo `both`), `patrimonio_cultural` (escopo `both`), `templo_religioso` (escopo `both`), `lazer_balneario`.
3. **`hospedagem`** (cor `#2563EB`, ícone `bed`, escopo `route_corridor`): `pousada_hotel`, `casa_temporada`.
4. **`artesanato`** (cor `#7C3AED`, ícone `palette`, escopo `route_corridor`): `artesanato_local`.
5. **`transporte`** (cor `#0891B2`, ícone `bus`, escopo `both`): `terminal_aeroporto`, `terminal_porto`, `terminal_rodoviario`, `catraia_travessia` (escopo `route_corridor`), `posto_combustivel`, `locadora_mobilidade`, `agencia_turismo`.
6. **`saude`** (cor `#DC2626`, ícone `heart-pulse`, escopo `citywide_essential`): `hospital_upa`, `posto_saude_ubs`, `farmacia` (escopo `both`).
7. **`seguranca`** (cor `#1E3A8A`, ícone `shield`, escopo `citywide_essential`): `seguranca_publica`, `conselho_tutelar_protecao`.
8. **`outros`** (cor `#6B7280`, ícone `help-circle`, escopo `route_corridor`): `servicos_publicos_cartorios` (escopo `citywide_essential`), `comercio_eventos` (escopo `both`), `nao_classificado`.

*Regra de Integridade:* Não inventar novos grupos principais. Se o ator tiver tipo não previsto, classificá-lo no grupo mais afim ou em `outros` com o subtipo correspondente documentado e submetido à revisão.

---

## 5. Ficha dos Atores e Pontos de Interesse (POIs)

Para cada ator associado à rota ou aos serviços essenciais da cidade de apoio, estruturar a seguinte ficha:

```yaml
actor_entry:
  slug: "exemplo-barraca-do-sol"
  name: "Barraca do Sol"  # Obrigatório (SEMTUR ou Editorial)
  description: "Restaurante e barraca de praia especializada em peixes amazônicos."
  category_slug: "alimentacao"  # Obrigatório (1 dos 8 grupos canônicos)
  type_slug: "barraca_praia"    # Obrigatório (subtipo ADR 0015)
  spatial_scope: "route_corridor" # route_corridor | citywide_essential | both
  location:
    latitude: -2.558123         # Obrigatório para publicação no mapa
    longitude: -54.978456       # Obrigatório para publicação no mapa
    status_coord: "ok"          # ok | ausente | inconsistente
    source_location: "semtur_inventory" # semtur_inventory | editorial_validation. NÃO usar google_places sem evidência de coleta autorizada ponta a ponta
  address:
    street: "Praia de Pindobal, s/n"
    district: "Pindobal"
    city: "Belterra"
    state_code: "PA"
  contacts:
    phone_raw: "(93) 99123-4567"
    phone_e164: "+5593991234567"  # Normalizado quando válido
    email: "contato@barracadosol.com.br" # Se não verificado -> VALOR_AUSENTE
    website: "https://barracadosol.com.br" # Validado http/https. Se não verificado -> VALOR_AUSENTE
    instagram: "@barracadosol"    # @handle ou URL completa. Se não verificado -> VALOR_AUSENTE
  operational:
    opening_hours_raw: "Diariamente das 08h às 18h" # Se não verificado no snapshot/campo -> VALOR_AUSENTE
    opening_hours_structured:
      regular:
        - days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
          open: "08:00"
          close: "18:00"
    payment_methods: ["money", "pix", "credit_card", "debit_card"]
  provenance_and_sources:
    is_semtur_inventory: true      # Somente true se possuir referência concreta de página/linha no inventário oficial
    semtur_external_id: "semtur_pindobal_12" # Referência auditável. Se não constar na SEMTUR -> VALOR_AUSENTE e is_semtur_inventory: false
    google_places_ref:
      place_id: "VALOR_AUSENTE"    # NUNCA inventar. Se não coletado ponta a ponta, marcar VALOR_AUSENTE
      google_maps_uri: "VALOR_AUSENTE" # Proibido criar URIs artificiais com cid=. Marcar VALOR_AUSENTE
      google_rating: null          # Proibido atribuir rating sem Place ID comprovado por conector
      google_review_count: null    # Proibido atribuir review count sem Place ID comprovado por conector
  experience_tags:
    # Tags não aplicáveis devem ser OMITIDAS (não registrar tag com 'não aplicável')
    - tag_slug: "por-do-sol"
      justification: "Local com visão aberta e poente desobstruído sobre o Rio Tapajós"
      evidence_type: "inspecao_em_campo" # inspecao_em_campo | declaracao_institucional | analise_geografica
      reviewed_by: "Equipe Editorial ECOnexão"
      reviewed_at: "2026-09-05"
  editorial_media:
    - media_type: "image"
      storage_path: "editorial-media/routes/rota-pindobal/barraca_do_sol.webp"
      alt_text: "Mesas de madeira sob quiosques de palha à beira da água clara da praia de Pindobal"
      credit: "Fotografia cedida pelo estabelecimento / Acervo SEMTUR"
      license_code: "SEMTUR_INSTITUTIONAL" # CC-BY-4.0 | SEMTUR_INSTITUTIONAL | PROPRIETARY
      is_cover: true
```

---

## 6. Governança das Tags de Experiência

As tags de experiência não são tags livres nem palavras-chave descontroladas. Toda tag adicionada a um ator da rota deve cumprir os seguintes critérios de registro:

| Tag Slug | Label Exibido | Critério Objetivo de Inclusão | Evidência Exigida | Regra de Verificação / Revisor |
|---|---|---|---|---|
| `por-do-sol` | Pôr do Sol | Orla, mirante ou praia voltada para o oeste com horizonte fluvial/terrestre aberto | Verificação geográfica de azimute ou registro fotográfico no entardecer | Confirmado por equipe ou SEMTUR |
| `domingo-em-familia` | Domingo em Família | Acesso seguro para crianças/idosos, área de banho calma ou infraestrutura de apoio | NÃO presumir apenas pelo nome: exige checagem de funcionamento aos domingos e segurança do local | Confirmado por equipe editorial |
| `trilha-ecologica` | Trilha Ecológica | Percurso pedestre ou caminhada natural demarcada com atrativos botânicos/geológicos | Rastreio ou menção explícita no inventário institucional | Confirmado por guia ou SEMTUR |
| `culinaria-regional` | Culinária Tradicional | Oferta ativa de pratos típicos da Amazônia (peixes da bacia, tucupi, macaxeira) | Cardápio verificado ou menção no inventário de gastronomia local | Confirmado por equipe editorial |
| `banho-de-rio` | Banho de Rio | Acesso direto a águas calmas e balneabilidade adequada para turistas | Margem acessível com praia fluvial ou balneário cadastrado | Confirmado por equipe editorial |

---

## 7. Mídia Editorial, Licenciamento e Acessibilidade (Publish Guard)

Toda imagem vinculada à rota ou aos seus atores deve satisfazer os requisitos do ADR 0008 e ADR 0006:

1. **Vedação de Mídia Google:** Nenhuma foto proveniente da Google Places API pode ser gravada ou persistida em repositório local ou Supabase Storage. O conector Google atua exclusivamente por proxy efêmero em tempo de execução.
2. **Campos Obrigatórios de Mídia Editorial:**
   - `storage_path` ou URI da imagem;
   - `alt_text` descritivo e objetivo, orientando usuários com deficiência visual (leitores de tela);
   - `credit` identificando explicitamente o fotógrafo, órgão ou acervo proprietário;
   - `license_code`: código formal de licença (`CC-BY-4.0`, `SEMTUR_INSTITUTIONAL`, `PROPRIETARY`).
3. **Publish Guard:** Mídias com `alt_text` genérico (ex: "foto", "imagem") ou sem crédito são sumariamente rejeitadas na esteira de publicação.

---

## 8. Checklist de Aprovação Editorial e Publicação

Antes de qualquer rota ser submetida para ingestão ou promoção (`status: published`), este checklist deve ser preenchido e assinado:

- [ ] **1. Identificação:** `route_slug`, `title`, `region_slug`, `city` e `summary` preenchidos sem textos de rascunho (*lorem ipsum*).
- [ ] **2. Origens:** Ao menos 1 origem cadastrada com coordenadas WGS84 válidas e testadas no mapa.
- [ ] **3. Geometria:** Trajeto OSRM/Routes com distância, duração, CRS 4326 e arquivo de proveniência rastreável com hash SHA-256 verificado.
- [ ] **4. Atores e Categorias:** 100% dos atores mapeados para os 8 grupos canônicos (ADR 0010) e subtipos válidos (ADR 0015).
- [ ] **5. Sem Invenção de Dados:** Campos ausentes (coordenadas de locais fora do mapa, telefones, redes sociais) marcados explicitamente como `VALOR_AUSENTE`. Nenhum `google_place_id` inventado.
- [ ] **6. Segregação de Fontes:** Atores originários da SEMTUR identificados; selo `SEMTUR` concedido apenas aos registros com vínculo institucional comprovado.
- [ ] **7. Mídia e Acessibilidade:** Imagem de capa da rota com `alt_text`, `credit` e `license_code` preenchidos. Nenhuma foto Google persistida no Storage.
- [ ] **8. Tags de Experiência:** Todas as tags possuem justificativa e tipo de evidência registrados.
- [ ] **9. Responsável Editorial:** Nome do revisor humano, papel RBAC (`editor`/`publisher`), data de revisão e justificativa registrados no cabeçalho de aprovação.
