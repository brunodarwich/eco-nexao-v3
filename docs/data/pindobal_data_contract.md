# Contrato de dados — Rota Pindobal

Versão: 1.0  
Fonte física: `C:\Users\Bruno\Downloads\teste-rota`  
Regra: somente leitura; nenhuma rotina altera os arquivos originais.

## 1. Resultado esperado

Produzir de forma idempotente:

- Uma região Santarém/Belterra e uma rota Pindobal publicável.
- Três origens com geometrias OSRM, distância, bounds e proveniência.
- Atores normalizados de SEMTUR e Google, sem merge ambíguo.
- Relações espaciais ator–rota calculadas em PostGIS.
- Relatório com importados, atualizados, rejeitados, duplicatas e candidatos editoriais.

## 2. Manifesto imutável do snapshot

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `inventario_semtur.csv` | 310926 | `9b4bdf682a83facbbfdb76176810f0ebcc3efba7efbe848fcfafa4d156e7eabb` |
| `data_semtur.json` | 358434 | `0a384b8bcda64744cf3db9bd07a62826d2617bc66b80b9ae6671d051c7ff18d1` |
| `santarem-pindobal.csv.csv` | 221156 | `75e0552320409447771134566e93657487bcd7d74fe192a2a496a9a42a2a6999` |
| `data.json` | 172947 | `b597eb1ed56caf4f7e655976d878d5baaf4c90fab4cd62ee365f5b3d5343e018` |
| `empresas_infraestrutura_rotas.csv` | 311479 | `23c7a8c0998e0d6b2036640959c92e0ebf36f7822e4623c5fc906c7c51ad874b` |
| `pois_data.json` | 490219 | `8875a1eaa2e6bc8bdd0d2a8cce9a10ae4ba742042c41effebbd0725c9a5fecea` |
| `rota_porto_OSRM_01.csv` | 133946 | `15c557a406bc6ebd87d4f8706d15c80127fc98b416d535ae57b4454fc991b6cb` |
| `rota_aeroporto_OSRM_01.csv` | 117739 | `8cae67ad9d00d6056733787ed41c940d1ba68490dc5bd5e60c6cb1c1f1d15776` |
| `rota_rodoviaria_OSRM_01.csv` | 131265 | `fd21e0df95368553aa81aaff22d630e9cffd00c1ef3d0feef6fb5573fc08c70b` |

Se um hash divergir, o importador interrompe por padrão. Nova versão do snapshot exige atualização revisada deste manifesto.

## 3. Autoridade das fontes

| Fonte | Autoridade | Pode sobrescrever automaticamente? |
|---|---|---|
| Edição ECOnexão aprovada | máxima | sim, mantendo histórico |
| SEMTUR | institucional | sim para campo institucional vazio; conflito vai à revisão |
| Google Places | descoberta/comercial | não sobrescreve validação SEMTUR/editorial |
| OSRM | geometria derivada | sim em nova versão editorial aprovada |
| Inferência/normalização | derivada | somente campos derivados, com versão da regra |

Campos de fontes distintas permanecem rastreáveis em `field_provenance`.

## 4. Contagens de controle

| Conjunto | Esperado |
|---|---:|
| Inventário SEMTUR | 674 registros |
| Recorte associado à rota | 303 registros |
| POIs consolidados Google | 737 registros |
| POIs apoio turístico/comercial | 593 |
| POIs emergência/infraestrutura | 144 |
| Pontos Porto | 884 |
| Pontos Aeroporto | 777 |
| Pontos Rodoviária | 866 |

O relatório deve satisfazer `lidos = importados + atualizados + ignorados + rejeitados + candidatos`, sem descarte silencioso.

## 5. Geometrias OSRM

| Código | Início | Fim comum | Distância esperada |
|---|---|---|---:|
| `porto` | `-2.428482,-54.701835` | `-2.558521,-54.978506` | 45,229046638 km |
| `aeroporto` | `-2.42478,-54.78583` | `-2.558521,-54.978506` | 41,451542278 km |
| `rodoviaria` | `-2.443185,-54.730652` | `-2.558521,-54.978506` | 42,318508540 km |

Regras:

- CSV fornece latitude, longitude; construção PostGIS usa longitude, latitude e SRID 4326.
- Rejeitar latitude fora de `[-90, 90]`, longitude fora de `[-180, 180]`, NaN ou sequência com menos de dois pontos.
- Preservar `ordem` e exigir progressão única.
- `distancia_acumulada_km` deve ser monotônica.
- Diferença entre distância final importada e recalculada deve ficar na tolerância definida pelo teste; inicialmente 1%.
- Armazenar `LineString`, bounds, distância em metros, provedor, data do snapshot e hash da fonte.

## 6. Mapeamento SEMTUR

| Campo fonte | Destino | Regra |
|---|---|---|
| `pagina` | `actor_external_refs.external_id` auxiliar | prefixar namespace SEMTUR; não usar como UUID interno |
| `titulo` | `actors.name` | trim, Unicode normalizado, obrigatório |
| `categoria` | categoria original/proveniência | mapear por tabela versionada |
| `coordenadas_geograficas` ou `latitude/longitude` | `actors.location` | validar e converter para `geography(Point,4326)` |
| `endereco` | `actors.address` | preservar valor original e versão normalizada |
| `telefone` | `actors.phone` | normalizar E.164 quando possível; preservar raw |
| `email` | `actors.email` | lowercase e validação sintática; inválido não é publicado |
| `instagram` | `actors.instagram` | normalizar URL/handle |
| `site` | `actors.website` | somente `http/https`, URL validada |
| `funcionamento` | `actors.opening_hours` | raw + JSON normalizado quando confiável |
| `servicos_instalacoes` | atributos/descrição | não converter automaticamente em acessibilidade verificada |
| `forma_pagamento` | `actors.payment_methods` | vocabulário controlado + raw |
| `projetos_sociais` | conteúdo editorial/proveniência | revisão editorial |
| `observacoes*`, `texto_bruto` | raw/proveniência | não expor automaticamente |

## 7. Mapeamento do recorte de rota

| Campo | Destino/regra |
|---|---|
| `id` | referência externa do snapshot, nunca UUID de domínio |
| `status_coord` | controle de qualidade; somente `ok` entra sem revisão adicional |
| `categoria_normalizada` | candidato a `actor_categories.slug`, via mapa versionado |
| `categoria_id` | referência legada, preservar em raw |
| `dist_rota_m` | valor derivado legado para comparação, não fonte final |
| `km_rota` | posição derivada legada para comparação |
| `segmento_rota` | índice de segmento geométrico, não categoria de ator |
| `ponto_projetado_rota` | candidato derivado; recalcular no PostGIS |
| `forma_de_acesso`, `rota_saida`, `fonte_pesquisa` | proveniência/metadata da relação |

Distância e posição finais serão recalculadas com PostGIS e comparadas ao legado.

## 8. Mapeamento Google legado

| Campo | Destino/regra |
|---|---|
| `nome` | candidato a `actors.name` |
| `grupo`, `categoria` | taxonomia de origem + mapa para categoria interna |
| flags `origem_*` | comparação; recalcular espacialmente |
| `endereco`, `telefone`, `site`, `horario_funcionamento` | campos Google separados/proveniência |
| `latitude`, `longitude` | localização Google |
| `distancia_*_km` | derivado legado para teste |
| `url_google_maps` | `actor_external_refs.source_url` validada |

Limitação crítica: o CSV final não preserva `place_id`, apesar de o coletor usá-lo para deduplicar em memória. Não derivar ID a partir da URL nem inventar valor. Marcar `external_id_missing=true`. Nova coleta Places API (New) deve preservar `places.id` ponta a ponta.

## 9. Taxonomia inicial

Mapeamento mínimo, versionado em código/fixture:

- hospedagem: pousada, hotel, casa de temporada.
- alimentação: restaurante, alimentação, bar, lanchonete.
- transporte: transporte, locadora, posto de combustível quando definido pelo produto.
- artesanato: artesanato/biojoias.
- atrativos: atrativo, centro turístico, religioso quando editorialmente aprovado.
- emergência: hospital, UPA, UBS, posto de saúde, farmácia, polícia, bombeiros.
- outros: não publicar em chip até classificação editorial.

O importador não força categorias desconhecidas para `atrativos`.

## 10. Deduplicação

Ordem:

1. Mesmo `(source, external_id)` válido: mesma referência externa.
2. Mesmo telefone normalizado ou site canônico e nomes compatíveis: candidato forte.
3. Nome normalizado + distância geográfica curta + categoria compatível: candidato fuzzy.
4. Conflitos de coordenada, nome genérico ou categoria incompatível: revisão humana.

Thresholds exatos serão calibrados em fixture rotulada antes de merge automático. Até lá, fuzzy match nunca mescla; apenas cria `reconciliation_candidates` com score e motivos.

## 11. Idempotência e escrita

- UUID interno estável após primeira importação.
- Upsert somente por chave natural/external ref confiável.
- Uma segunda execução com o mesmo snapshot não cria linhas nem altera timestamps de conteúdo sem mudança.
- `--dry-run` executa parsing, validação, deduplicação e relatório sem commit.
- Execução real usa transação por etapa e registra `ingestion_runs`.
- Falha não deixa rota publicada parcialmente.

## 12. Relatório obrigatório

JSON e resumo humano com:

- hashes e arquivos.
- versão do importador e regras.
- contagens por fonte/categoria/status.
- geometrias e distâncias.
- criados, atualizados, inalterados, rejeitados e candidatos.
- erros com linha/ID externo, sem segredos.
- queries de smoke test e resultado.

## 13. Dados de teste

Criar fixtures pequenas versionadas dentro de `backend/tests/fixtures/pindobal/`, sem copiar todo o dataset:

- Um ator SEMTUR válido.
- Um Google válido com Place ID.
- Um snapshot legado sem Place ID.
- Um par duplicado determinístico.
- Um candidato fuzzy ambíguo.
- Uma coordenada inválida.
- Uma geometria curta válida e uma inválida.

Nenhum teste de CI chama Google, OSRM ou Supabase production.
