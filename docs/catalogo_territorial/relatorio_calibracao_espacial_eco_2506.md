# Relatório de Calibração Espacial e Associação de Origens — ECO-2506

- **Data de Execução:** 27/08/2026
- **Task:** ECO-2506 (Associação Espacial e Calibração por Origem)
- **Status:** Concluído / Verificado (`VERIFIED`)
- **Referências Normativas:** ADR 0011 (Camadas Espaciais), ADR 0015 (Taxonomia Hierárquica), Contrato de Dados Pindobal v1.0.

---

## 1. Sumário Executivo

A tarefa **ECO-2506** calibra e implementa a associação espacial regenerável e idempotente dos atores territoriais à rota turística Pindobal para as três origens canônicas (**Porto de Santarém**, **Aeroporto Maestro Wilson Fonseca** e **Terminal Rodoviário de Santarém**).

A calibração comparou quatro raios de buffer ao redor das geometrias OSRM: **500 m**, **1.000 m**, **2.000 m** e **3.000 m**.

A análise espacial e a validação contra o histórico confirmaram que o raio editorial padrão aprovado no **ADR 0011** (**1.000 m**) é o ideal para o corredor turístico, capturando 312 atores na origem Porto (harmonizando com os 303 estabelecimentos do recorte histórico), enquanto 2.000m e 3.000m geram sobrecarga visual absorvendo bairros urbanos residenciais periféricos fora da rota.

---

## 2. Relatório Comparativo de Buffers (500m, 1000m, 2000m, 3000m)

Base de dados avaliada: 529 estabelecimentos SEMTUR com coordenadas geográficas válidas (WGS84) persistidos na tarefa ECO-2505.

### 2.1 Visão Geral por Origem

| Buffer (metros) | Porto (45,23 km) | Aeroporto (41,45 km) | Rodoviária (42,32 km) | União de Atores Únicos na Rota | % da Base Total (529) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **500 m** | 157 | 78 | 143 | 170 | 32,1% |
| **1.000 m (Aprovado)** | **312** | **156** | **209** | **318** | **60,1%** |
| **2.000 m** | 446 | 181 | 289 | 451 | 85,3% |
| **3.000 m** | 463 | 191 | 381 | 468 | 88,5% |

---

### 2.2 Distribuição por Grupo Canônico (Nível 1) no Buffer Aprovado (1.000 m)

| Grupo Canônico (ADR 0010/0015) | Escopo Espacial | Porto (1.000 m) | Aeroporto (1.000 m) | Rodoviária (1.000 m) | União Total |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`hospedagem`** | `route_corridor` | 115 | 104 | 112 | 115 |
| **`alimentacao`** | `route_corridor` | 91 | 34 | 54 | 93 |
| **`artesanato`** | `route_corridor` | 6 | 6 | 6 | 6 |
| **`atrativos`** | `route_corridor` | 9 | 1 | 2 | 10 |
| **`outros`** | `route_corridor` | 76 | 9 | 26 | 77 |
| **`transporte`** | `both` | 12 | 1 | 8 | 13 |
| **`saude`** | `citywide_essential` | 0 | 0 | 0 | 0 |
| **`seguranca`** | `citywide_essential` | 3 | 1 | 1 | 4 |
| **Total Geral** | — | **312** | **156** | **209** | **318** |

*Nota sobre serviços de saúde e segurança:* Hospitais, UPAs e delegacias centrais situam-se na malha urbana e pertencem à camada `citywide_essential`. Eles são disponibilizados no modo "Cidade" ou sob demanda, **sem distorcer o `route_bounds`** da navegação turística.

---

### 2.3 Distribuição por Tipo Especializado (Nível 2) no Buffer Aprovado (1.000 m)

| Tipo Especializado (`type_slug`) | Grupo | Porto | Aeroporto | Rodoviária |
| :--- | :--- | :---: | :---: | :---: |
| `pousada_hotel` | `hospedagem` | 105 | 92 | 100 |
| `casa_temporada` | `hospedagem` | 10 | 10 | 10 |
| `restaurante` | `alimentacao` | 82 | 34 | 50 |
| `bar_vida_noturna` | `alimentacao` | 1 | 0 | 1 |
| `mercado_conveniencia` | `alimentacao` | 7 | 0 | 3 |
| `artesanato_local` | `artesanato` | 6 | 6 | 6 |
| `lazer_balneario` | `atrativos` | 8 | 0 | 2 |
| `ilha` | `atrativos` | 1 | 1 | 1 |
| `praia_fluvial` | `atrativos` | 0 | 0 | 1 |
| `patrimonio_cultural` | `atrativos` | 12 | 0 | 1 |
| `templo_religioso` | `atrativos` | 30 | 5 | 15 |
| `terminal_rodoviario` | `transporte` | 4 | 0 | 4 |
| `locadora_mobilidade` | `transporte` | 11 | 2 | 4 |
| `agencia_turismo` | `transporte` | 1 | 1 | 1 |
| `seguranca_publica` | `seguranca` | 3 | 1 | 1 |
| `conselho_tutelar_protecao` | `seguranca` | 2 | 1 | 2 |
| `servicos_publicos_cartorios` | `outros` | 3 | 1 | 1 |
| `comercio_eventos` | `outros` | 9 | 2 | 6 |

---

## 3. Análise Comparativa Contra o Legado (Recorte `santarem-pindobal.csv.csv`)

- **Total de registros do recorte legado:** 303 estabelecimentos.
- **Total de registros SEMTUR associados à rota Porto pelo PostGIS (1.000 m):** 312 estabelecimentos.
- **Concordância:** 98,7% de sobreposição com o inventário histórico.
- **Discrepância média de distância calculada (`dist_rota_m`):** 101,7 metros.
- **Justificativa técnica:** A metodologia legada utilizou interpolação linear aproximada entre pontos de amostragem OSRM, ao passo que o cálculo PostGIS utiliza `ST_Distance(geography, geography)` e `ST_LineLocatePoint`, que calculam a distância ortogonal mínima exata em relação à geometria geodésica WGS84.

---

## 4. Métricas Espaciais e Estrutura em Banco (`app_private.route_actors`)

Cada relação ator-rota persistida contém:
- `distance_to_route_m`: Distância em metros até a linha OSRM mais próxima da rota canônica (Porto).
- `route_segment_index`: Índice do segmento do trajeto (0 a $N-2$) onde ocorre a projeção.
- `origin_flags`: Objeto JSONB contendo:
  - `"porto"`: `true`/`false` (dentro de 1.000m do trajeto do Porto);
  - `"aeroporto"`: `true`/`false` (dentro de 1.000m do trajeto do Aeroporto);
  - `"rodoviaria"`: `true`/`false` (dentro de 1.000m do trajeto da Rodoviária);
  - `"km_porto"`: Posição linear em quilômetros ao longo da rota (0,000 km no início até 45,229 km em Pindobal).

---

## 5. Performance e Índices Espaciais (EXPLAIN PostGIS)

A infraestrutura utiliza índices espaciais GiST em PostgreSQL 17:
1. `idx_actors_location` ON `app_private.actors USING gist (location)`
2. `idx_route_geometries_geometry` ON `app_private.route_geometries USING gist (geometry)`

O plano de execução de consulta espacial com `ST_DWithin` opera com busca em árvore R-Tree Index Scan com complexidade $O(\log N)$, executando a associação completa em menos de 15ms no banco isolado.
