# ECO-2501 — auditoria reproduzível dos datasets

Status: `VERIFIED`  
Data: 27/08/2026  
Fonte física: `C:\Users\Bruno\Downloads\teste-rota` (somente leitura)

## Resultado e método

`[FATO]` O auditor versionado em `scripts/audit_eco_2501.py` abriu os arquivos apenas
para leitura, calculou SHA-256 antes e depois da análise e obteve
`source_unchanged=true`, `validation_errors=[]`. Não houve rede, importação, correção
de fonte, decisão de taxonomia ou escrita fora do repositório.

`[FATO]` As três contagens de controle foram reproduzidas tanto no CSV quanto na
representação JSON: **674 SEMTUR**, **303 recorte Pindobal** e **737 Google legado**.
No Google, `593 + 144 = 737`.

## Manifesto integral

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `data.json` | 172947 | `b597eb1ed56caf4f7e655976d878d5baaf4c90fab4cd62ee365f5b3d5343e018` |
| `data_semtur.json` | 358434 | `0a384b8bcda64744cf3db9bd07a62826d2617bc66b80b9ae6671d051c7ff18d1` |
| `empresas_infraestrutura_rotas.csv` | 311479 | `23c7a8c0998e0d6b2036640959c92e0ebf36f7822e4623c5fc906c7c51ad874b` |
| `inventario_semtur.csv` | 310926 | `9b4bdf682a83facbbfdb76176810f0ebcc3efba7efbe848fcfafa4d156e7eabb` |
| `inventario_semtur.html` | 324131 | `25982ad8da059a0c19239836bbd4c59037a5a6759ba67eb119a8d93c5b660dee` |
| `mapa.html` | 196310 | `f0c4fb65b4cccfe46b62c2268cd662029734db392bdc5ff56e499cafbf9ba8cc` |
| `pois_data.js` | 414323 | `f2c50d31128850e81f661f744c22b69b1dbddb649a5615c0bcb36f12b468fc74` |
| `pois_data.json` | 490219 | `8875a1eaa2e6bc8bdd0d2a8cce9a10ae4ba742042c41effebbd0725c9a5fecea` |
| `rota_aeroporto_OSRM_01.csv` | 117739 | `8cae67ad9d00d6056733787ed41c940d1ba68490dc5bd5e60c6cb1c1f1d15776` |
| `rota_porto_OSRM_01.csv` | 133946 | `15c557a406bc6ebd87d4f8706d15c80127fc98b416d535ae57b4454fc991b6cb` |
| `rota_rodoviaria_OSRM_01.csv` | 131265 | `fd21e0df95368553aa81aaff22d630e9cffd00c1ef3d0feef6fb5573fc08c70b` |
| `rotas_pindobal.html` | 237500 | `2de7553e9e63674e899438dba946aec40ae270e547ef63ce886e153c3aa0ebfa` |
| `santarem-pindobal.csv.csv` | 221156 | `75e0552320409447771134566e93657487bcd7d74fe192a2a496a9a42a2a6999` |
| `scratch/__pycache__/build_html.cpython-313.pyc` | 28482 | `459e482c4b8de6e9a31547feb8e15041219eb0846b728d2d67eeea656c54d679` |
| `scratch/audit_all_coords.py` | 4287 | `d82951617f753f3ae8db9a0e4e581b13db5006b8514d238290a1faa15b487b47` |
| `scratch/audit_locations.py` | 4120 | `7a8db92ae5569722cd4747781764c51d75d2d5a466caf178d43b6d3220bd7b4a` |
| `scratch/build_html.py` | 15923 | `963a45ec35213eabd20f8d92b75c0cd648e1b96410c391a2017cdce2dcdea7cf` |
| `scratch/check_duplicates.py` | 966 | `adab88f1f4b01b863b2810622f17cb23240c65587da52468050b0a36e8b9ae2a` |
| `scratch/check_endpoints.py` | 692 | `bae8b49967a936a99946f9850e60d6e484126bf3177c95fd34247386232ae3ce` |
| `scratch/deep_audit.py` | 5717 | `29200cf13029b72054512c61c658f595cc46f602650c10674fef54c8b89a99c8` |
| `scratch/fetch_pois_to_csv.py` | 13693 | `00f36df62289a3f18694915c1912c5aedd74c7e265b901941b0db08533d3baa2` |
| `scratch/fix_and_rebuild.py` | 1849 | `19454f5fc595f318667f6109f9621333e62a71c83761daebe1e516d6bc17a025` |
| `scratch/generate_rotas_html.py` | 28032 | `2d4a2c7b3ad4b391e8dbae0a89ffe1b55ed2e96088daf4f53fb8b4392fbc31a6` |
| `scratch/inspect_csv.py` | 1923 | `279bf0719d09bbe517219c60a4e5f2688cc0be6667e2770a484f1fa0def77492` |
| `scratch/process_semtur.py` | 3654 | `6904aec96a42a544428e06503118a2f0aa03197c85f0ead845e4a66cf4a01064` |

`[FATO]` Os nove arquivos manifestados pelo contrato coincidem em bytes e hash.
`[FATO]` O contrato já inclui os dois arquivos Google; não inclui HTML, JS nem scripts.
`[INFERÊNCIA]` HTML/JS são visualizações/embeddings derivados; os scripts são
ferramentas históricas. Eles não foram somados como datasets independentes.

## Schemas e nulidade

Nulidade abaixo significa célula vazia no CSV; não havia célula apenas com whitespace.
`distintos` conta valores não vazios sem normalizar semântica.

### SEMTUR institucional — 674

Schema CSV: `pagina, categoria, titulo, coordenadas_geograficas, endereco, telefone,
email, instagram, site, funcionamento, servicos_instalacoes, forma_pagamento,
contingente, projetos_sociais, observacoes_criticas, observacoes, texto_bruto`.

Schema JSON derivado: `id, pagina, categoria, titulo, lat, lng, endereco, telefone,
email, instagram, site, funcionamento, servicos, pagamento, contingente,
projetos_sociais, observacoes`.

| Campo | Vazios | Distintos |
|---|---:|---:|
| categoria | 0 | 41 |
| contingente | 673 | 1 |
| coordenadas_geograficas | 145 | 521 |
| email | 497 | 174 |
| endereco | 201 | 454 |
| forma_pagamento | 661 | 4 |
| funcionamento | 592 | 77 |
| instagram | 610 | 63 |
| observacoes | 673 | 1 |
| observacoes_criticas | 674 | 0 |
| pagina | 1 | 159 |
| projetos_sociais | 673 | 1 |
| servicos_instalacoes | 487 | 186 |
| site | 633 | 41 |
| telefone | 243 | 413 |
| texto_bruto | 0 | 673 |
| titulo | 0 | 670 |

### Recorte Pindobal — 303

Schema CSV: os 17 campos SEMTUR, mais `local, forma_de_acesso, rota_saida,
fonte_pesquisa, id, latitude, longitude, status_coord, categoria_normalizada,
categoria_id, dist_rota_m, km_rota, segmento_rota, ponto_projetado_rota`.

Schema JSON derivado: `id, titulo, categoria, cat_orig, lat, lng, endereco, local,
telefone, email, instagram, site, funcionamento, servicos, pagamento, obs`.

| Campo | Vazios | Distintos | Campo | Vazios | Distintos |
|---|---:|---:|---|---:|---:|
| categoria | 0 | 25 | categoria_id | 0 | 17 |
| categoria_normalizada | 0 | 17 | contingente | 302 | 1 |
| coordenadas_geograficas | 0 | 298 | dist_rota_m | 0 | 293 |
| email | 176 | 124 | endereco | 12 | 287 |
| fonte_pesquisa | 289 | 5 | forma_de_acesso | 6 | 19 |
| forma_pagamento | 289 | 6 | funcionamento | 250 | 51 |
| id | 0 | 303 | instagram | 262 | 40 |
| km_rota | 0 | 187 | latitude | 0 | 292 |
| local | 0 | 6 | longitude | 0 | 293 |
| observacoes | 281 | 22 | observacoes_criticas | 303 | 0 |
| pagina | 0 | 87 | ponto_projetado_rota | 0 | 191 |
| projetos_sociais | 303 | 0 | rota_saida | 0 | 3 |
| segmento_rota | 0 | 91 | servicos_instalacoes | 163 | 140 |
| site | 269 | 33 | status_coord | 0 | 1 |
| telefone | 100 | 197 | texto_bruto | 8 | 295 |
| titulo | 0 | 302 |  |  |  |

### Google legado — 737

Schema CSV: `grupo, categoria, origem_porto, origem_aeroporto, origem_rodoviaria,
nome, endereco, instagram, telefone, email, horario_funcionamento, site, latitude,
longitude, distancia_porto_km, distancia_aeroporto_km, distancia_rodoviaria_km,
url_google_maps`.

Schema JSON derivado/compactado: `id, g, c, p, a, r, n, e, i, t, em, h, s, lat,
lng, dp, da, dr, url`.

| Campo | Vazios | Distintos | Campo | Vazios | Distintos |
|---|---:|---:|---|---:|---:|
| categoria | 0 | 12 | grupo | 0 | 2 |
| nome | 0 | 710 | endereco | 0 | 621 |
| telefone | 316 | 408 | site | 545 | 170 |
| email | 737 | 0 | instagram | 737 | 0 |
| horario_funcionamento | 316 | 286 | latitude | 0 | 722 |
| longitude | 0 | 722 | url_google_maps | 0 | 737 |
| origem_porto | 0 | 2 | origem_aeroporto | 0 | 2 |
| origem_rodoviaria | 0 | 2 | distancia_porto_km | 0 | 476 |
| distancia_aeroporto_km | 0 | 630 | distancia_rodoviaria_km | 0 | 556 |

`[FATO]` Os caracteres de substituição `�` já estão presentes no snapshot UTF-8
Google; a auditoria não os corrigiu.

## Coordenadas e rotas

| Conjunto | Válidas | Par ausente | Inválidas/faixa | BBox (lat min/max; lon min/max) | Grupos de coordenada duplicada |
|---|---:|---:|---:|---|---:|
| SEMTUR JSON | 529 | 145 | 0 | -2,989167/-1,921089; -55,724361/-54,364083 | 0 |
| Recorte | 303 | 0 | 0 | -2,563457/-2,417972; -54,978443/-54,700722 | 3 (8 linhas) |
| Google | 737 | 0 | 0 | -2,563623/-2,415286; -54,980200/-54,687353 | 9 (23 linhas) |

`[FATO]` Todos os 303 registros do recorte têm `status_coord=ok`. Isso comprova o
status gravado e a validade WGS84 básica, não a correção geográfica da entidade.

| Rota | Pontos | Início | Fim | Distância final km | Ordem única/progressiva | Acumulada monotônica |
|---|---:|---|---|---:|---|---|
| Porto | 884 | -2,428482/-54,701835 | -2,558521/-54,978506 | 45,229046638414246 | sim/sim | sim |
| Aeroporto | 777 | -2,424780/-54,785830 | -2,558521/-54,978506 | 41,4515422779165 | sim/sim | sim |
| Rodoviária | 866 | -2,443185/-54,730652 | -2,558521/-54,978506 | 42,31850853980259 | sim/sim | sim |

As diferenças contra o contrato são menores que `1e-9%`; não há coordenada fora da
faixa. A Rodoviária possui seis pares consecutivos/repetidos (12 linhas), sem quebrar
ordem ou monotonicidade.

## Categorias e tipos originais

`[FATO]` SEMTUR possui 41 valores originais. Frequências:

```text
Igrejas e Templos 56; agências 42; agências de passagens aéreas 2;
artesanato 12; atrativos naturais 14; balneários/chácaras 4; bibliotecas 10;
cartórios 4; casa de shows 4; casas de temporada 15; catraias em alter do chão 1;
cidadania 4; clubes sociais, desportivos e de lazer 6; edificações e arquiteturas 10;
feiras[espaço final] 5; hospedagem 141; ilhas 2; instituições culturais 1;
lanchas em alter do chao e rios amazonas e tapajós 1; lanchas em alter do chão 1;
locadoras de veículos 15; mercado 9; obras de arte 10; praias fluviais 12;
restaurantes e bares em Alter do Chão 45; Carapanari 3; Pajuçara 2;
Ponta de Pedras 12; Santarém 100; Praia do Maracanã 5; seguranca 11; serras 3;
serviços/equipamentos de lazer 14; para eventos 36; shopping/lojas de departamento 2;
transporte fluvial em Santarém 34; transporte intermunicipal/interestadual/urbano 4;
táxi aéreo em santarem e regioes 6; unidade de conservação 2;
vans e micro-ônibus 9; área de proteção ambiental 5.
```

`[FATO]` O recorte preserva 25 categorias originais e traz 17 valores
`categoria_normalizada`: agência turismo 2, alimentação 76, artesanato 7, cartórios
3, casas de temporada 10, combustível 9, emergência 1, farmácia 2, hospedagem 113,
locadora veículos 9, mercado 7, religioso 30, saúde 1, serviço público 4, serviços
para eventos 16, shopping/lojas 2 e transporte 11. Esses valores são legado, não uma
taxonomia aprovada nesta task.

`[FATO]` Google tem dois grupos: `Apoio Turístico e Comercial` 593 e `Emergência e
Infraestrutura Pública` 144. Seus 12 tipos são: restaurante/alimentação 161,
hospedagem 150, bar/vida noturna 94, mercadinho/conveniência 93, atrativo/centro
turístico 50, farmácia 48, posto de gasolina 45, hospital/UPA 38, posto de saúde 33,
delegacia 17, conselho tutelar 5 e bombeiros 3.

`[DECISÃO PENDENTE]` Qualquer mapeamento entre esses vocabulários, incluindo
acentos/aliases, grupos públicos e escopo espacial, pertence à ECO-2503/H25.2.

## Identificadores e duplicatas internas

| Fonte | Identificador observado | Vazios | Únicos | Observação |
|---|---|---:|---:|---|
| SEMTUR | `pagina` | 1 | 159 | 128 grupos repetidos, 642 linhas; auxiliar, não UUID |
| Recorte | `id` | 0 | 303 | único no snapshot; não UUID de domínio |
| Google | `url_google_maps` | 0 | 737 | URL única; não substitui Place ID |

`[FATO]` Não existe coluna `place_id` no CSV Google. O `id` compacto do JSON é
derivado e não foi aceito como Place ID. Nenhum ID foi inferido da URL.

| Fonte | Nome: grupos/linhas | Telefone: grupos/linhas | Site: grupos/linhas | Coordenada: grupos/linhas |
|---|---:|---:|---:|---:|
| SEMTUR | 4/8 | 13/30 | 1/2 | 0/0 |
| Recorte | 1/2 | 4/9 | 1/3 | 3/8 |
| Google | 24/59 | 7/17 | 21/124 | 9/23 |

Esses números são sinais por chave isolada. Site repetido pode ser plataforma ou
rede; telefone/coordenada repetidos podem representar unidades relacionadas. Não são
merges automáticos.

## Matrizes preliminares de correspondência

### SEMTUR ↔ recorte

| Regra | Correspondem | Não correspondem | Interpretação |
|---|---:|---:|---|
| título normalizado exato | 189 | 114 | rastreabilidade preliminar; não prova identidade |

### SEMTUR ↔ Google legado

Blocking reproduzível: nome normalizado exato, telefone normalizado exato ou host do
site exato. Resultado: **67 pares candidatos**, sendo 22 com nome+telefone exatos e
45 com evidência isolada/combinada insuficiente. Nos 45 possíveis: 34 estão até
100 m, 2 entre 101–500 m, 6 acima de 500 m e 3 não têm distância calculável por
ausência de coordenadas SEMTUR.

| SEMTUR | Google | Distância m | Evidência | Classe |
|---|---|---:|---|---|
| Buffet Prazeres da Mesa | Buffet Prazeres da Mesa | 13,7 | nome+telefone | forte |
| Churrascaria Sabor do Sul | Churrascaria Sabor do Sul | 144,0 | nome+telefone | forte |
| Churrasco Baião De Dois | Churrasco Baião De Dois | 23,8 | nome+telefone | forte |
| Dom Mani | Dom Mani | 31,0 | nome+telefone | forte |
| Hadouken Sushi | Hadouken Sushi | 14101,6 | nome+telefone | forte com conflito espacial |
| Hostel Manga Rosa | Hostel Manga Rosa | 25,0 | nome+telefone | forte |
| Hotel Horizonte | Hotel Horizonte | 59,6 | nome+telefone | forte |
| Hotel Terra Nativa | Hotel Terra Nativa | 12,3 | nome+telefone | forte |
| Picanha no Bafo | Picanha no Bafo | 28,8 | nome+telefone | forte |
| Pousada Alter | Pousada Alter | 96,5 | nome+telefone | forte |
| Pousada Alter para Todos | Pousada Alter Para Todos | 40,7 | nome+telefone | forte |
| Pousada Alterosa | Pousada Alterosa | 4,3 | nome+telefone | forte |
| Pousada Flor de Alter | Pousada Flor de Alter | 20,6 | nome+telefone | forte |
| Pousada Nosso Canto Alter | Pousada Nosso Canto Alter | 3,3 | nome+telefone | forte |
| Pousada Pedra do Sol | Pousada Pedra do Sol | 7,1 | nome+telefone | forte |
| Pousada Recanto Maguary | Pousada Recanto Maguary | 15,6 | nome+telefone | forte |
| Pousada Serra da Lua | Pousada Serra Da Lua | 8,5 | nome+telefone | forte |
| Pousada Tupaiu | pousada Tupaiú | 27,4 | nome+telefone | forte |
| Restaurante Mutunuy 2 | Restaurante Mutunuy 2 | 331,9 | nome+telefone | forte |
| Restaurante Sabor de casa | Restaurante Sabor de Casa | 107,9 | nome+telefone | forte |
| Salgaderia Imperial | Salgaderia Imperial | 95,6 | nome+telefone | forte |
| Segredo do Beco | Segredo do Beco | 35,7 | nome+telefone | forte |

`[INFERÊNCIA]` “forte” descreve somente a combinação de evidências. O conflito de
14,1 km prova que nem essa classe autoriza merge. Os 67 pares completos permanecem
na saída JSON do auditor e todos têm `action=revisao_editorial`.

`[DECISÃO PENDENTE]` Thresholds, pesos, compatibilidade de categoria e regra de
aceite/rejeição serão calibrados em fixture rotulada na ECO-2509; não foram decididos.

## Fatos, inferências e decisões pendentes

- `[FATO]` SEMTUR é fonte institucional; Google legado é descoberta/comercial. Os
  campos e contagens foram reportados separadamente.
- `[FATO]` `fetch_pois_to_csv.py` usa endpoints Places Legacy, desduplica por
  `place_id` em memória e não o exporta no CSV final. O script não foi executado.
- `[INFERÊNCIA]` `data_semtur.json`, `data.json`, `pois_data.json`, `pois_data.js` e
  HTMLs são representações/visualizações derivadas pelos scripts históricos.
- `[INFERÊNCIA]` duplicatas e candidatos indicam necessidade de curadoria, não
  identidade canônica.
- `[DECISÃO PENDENTE]` direitos SEMTUR, retenção de raw, autoridade/precedência por
  campo e responsável editorial: H25.1/ECO-2502.
- `[DECISÃO PENDENTE]` taxonomia, aliases, tipos, ícones e escopos: H25.2/ECO-2503.
- `[DECISÃO PENDENTE]` política, atribuição, cache, custo e plataforma Google:
  H25.3/ECO-2507.

## Reprodução e validação

```powershell
$env:PYTHONIOENCODING='utf-8'
python docs/catalogo_territorial/scripts/audit_eco_2501.py `
  --source 'C:\Users\Bruno\Downloads\teste-rota'
```

Critério de sucesso: exit code `0`, `validation_errors: []`, contagens
`674/303/737`, representações `674/303/737` e `source_unchanged: true`.

Foram feitas duas execuções independentes do auditor; ambas retornaram exit code 0
e o mesmo resultado determinístico. Não houve verificação Supabase/RLS, Google,
atribuição/custo ou rollback de dados porque não houve banco, rede nem mutation.

Próximas tasks desbloqueadas pela evidência, sem execução nesta sessão: ECO-2502 e
ECO-2503. Seus gates humanos permanecem obrigatórios.
