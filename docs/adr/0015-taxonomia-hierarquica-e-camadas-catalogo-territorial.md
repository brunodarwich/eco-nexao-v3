# ADR 0015 — Taxonomia Hierárquica, Tipos Específicos, Aliases e Comportamento Espacial do Catálogo Territorial (SEMTUR, Google e ECOnexão)

- **Status:** proposto (Aguardando homologação do Owner no Gate H25.2 — `BLOCKED`)
- **Data:** 27/08/2026
- **Autores:** Equipe de Arquitetura ECOnexão / Antigravity
- **Decisor:** Bruno Darwich, Proprietário do Produto (Owner)
- **Task Relacionada:** ECO-2503 (Taxonomia Hierárquica do Catálogo Territorial)
- **Dependências:** ECO-2501 (Auditoria dos Datasets — `VERIFIED`), ADR 0010 (Taxonomia Visual do Mapa — `aceito`), ADR 0011 (Camadas Espaciais do Mapa — `aceito`), ADR 0014 (Governança de Fontes, Retenção e Publicação — `aceito`)
- **Gate de Conclusão:** Gate Humano H25.2 — Grupos visuais, tipos específicos, aliases, ícones, escopos e regras de publicação aceitos pelo Owner.

---

## 1. Contexto e Problema

Na modernização do catálogo geoespacial da ECOnexão (Marcos 2 e 3), a integração do inventário institucional da Secretaria Municipal de Turismo de Santarém (**SEMTUR**, com 674 registros auditados na ECO-2501) e da base de descoberta comercial (**Google Places / Legado**, com 737 registros auditados) trouxe um desafio taxonômico fundamental:

1. **Heterogeneidade e Fragmentação de Vocabulário:**
   - O inventário SEMTUR apresenta **41 categorias originais** com sobreposições geográficas (ex: *"restaurantes e bares em Santarém"*, *"restaurantes e bares em Alter do Chão"*, *"Carapanari"*, *"Ponta de Pedras"*), modais fluviais especializados (*"catraias em alter do chão"*, *"lanchas em alter do chão e rios amazonas e tapajós"*, *"transporte fluvial em Santarém"*) e categorias de infraestrutura urbana (*"mercado"*, *"cartórios"*, *"cidadania"*, *"edificações e arquiteturas"*, *"feiras "*).
   - O recorte da Rota Pindobal possui **25 categorias originais** e **17 categorias normalizadas legadas** (*"combustível"*, *"farmácia"*, *"agência turismo"*, *"serviço público"*, *"religioso"*, *"serviços para eventos"*, etc.).
   - A base Google possui **2 macro-grupos** e **12 tipos operacionais** (*"posto de gasolina"*, *"farmácia"*, *"conselho tutelar"*, *"hospital/UPA"*, *"posto de saúde"*, *"delegacia"*, *"bombeiros"*, *"mercadinho/conveniência"*, etc.).
2. **Restrições de Acessibilidade Visual e Cognitiva (WCAG 2.1 AA e ADR 0010):**
   - O ADR 0010 fixou **8 grupos visuais protegidos** (`alimentacao`, `atrativos`, `hospedagem`, `artesanato`, `transporte`, `saude`, `seguranca`, `outros`) com paleta cromática de alto contraste e ícones unívocos para evitar dependência exclusiva de cor.
   - Criar 15 a 20 categorias de topo no mapa geraria sobrecarga cognitiva severa (*choice overload*), barra de filtros intransponível em telas de smartphones e impossibilidade matemática de manter distinção de cores acessível sob sol amazônico intenso (reflexo na praia e na estrada).
3. **Comportamento Espacial e Bounding Box (ADR 0011):**
   - Nem todos os tipos de estabelecimento pertencem à mesma camada espacial. Estabelecimentos de lazer e alimentação pertencem ao corredor da rota (`route_corridor`), serviços de socorro médico e segurança pertencem à malha regional da cidade (`citywide_essential`), enquanto modais e postos de combustível atuam em ambos os contextos (`both`).

Faz-se necessária uma arquitetura formal de taxonomia hierárquica em 2 níveis que acomode 100% dos dados auditados, preserve a acessibilidade e defina o comportamento espacial e editorial de cada tipo.

---

## 2. Análise Comparativa das Opções Arquiteturais

| Dimensão de Avaliação | **Opção 1: 8 Grupos Visuais Canônicos + `actor_types` Especializados (Hierárquico em 2 Níveis)** *(Proposta / Recomendada)* | **Opção 2: Flat Expandido (15–20 Categorias de Topo no Mapa)** | **Opção 3: Tags Livres Multivalor (Folksonomia N:N)** |
| :--- | :--- | :--- | :--- |
| **Cognição e UX Mobile** | **Excelente**: Barra de filtros primária limpa (8 chips acessíveis). Drill-down e subfiltros nos cards e modais de detalhe. | **Péssima**: Sobrecarga cognitiva; rolagem horizontal excessiva na barra de chips; mapa visualmente caótico. | **Fraca como filtro primário**: Ausência de ancoragem visual; impossível prever qual ícone/cor renderizar no pin. |
| **Acessibilidade (WCAG 2.1 AA)** | **Total conformidade**: 8 cores canônicas com contraste e ícones Lucide unívocos testados. | **Crítica**: Impossível criar 20 cores distintas com contraste AA para texto e distinção para daltônicos. | **Complexa**: Leitores de tela perdem hierarquia semântica estruturada. |
| **Precisão Semântica** | **Máxima**: `group_slug` define estilo/cor do pin; `type_slug` fornece semântica exata (ex: `posto_combustivel`, `catraia`, `conselho_tutelar`). | **Média**: Achata conceitos ricos em classes genéricas para tentar caber no topo. | **Alta flexibilidade, zero consistência**: Proliferação de termos sinônimos despadronizados. |
| **Camadas Espaciais (ADR 0011)** | **Perfeita aderência**: `spatial_scope` (`route_corridor`, `citywide_essential`, `both`) é definido de forma determinística por tipo. | **Inconsistente**: Dificulta a aplicação de buffers de rota vs. malha urbana integral. | **Inviável**: Incompatível com particionamento espacial determinístico PostGIS por camada. |
| **Impacto no Schema e RLS** | **Baixo/Controlado**: Modelo relacional `actors.category_id` (FK `actor_categories`) + `actors.type_id` (FK `actor_types`). | **Médio**: Exige redefinição de todas as tabelas de tema, ícones e cores do frontend. | **Alto**: Tabelas associativas N:N, triggers de validação e consultas pesadas com `JOIN`s no mapa. |

---

## 3. Decisão Proposta

### 3.1 Arquitetura Hierárquica em 2 Níveis (`actor_categories` e `actor_types`)

1. **Nível 1 — Grupos Visuais Canônicos (`actor_categories`):**
   - Preserva estritamente os **8 grupos visuais canônicos** definidos e homologados no ADR 0010:
     - `alimentacao` (`#D97706`, ícone `utensils`)
     - `atrativos` (`#059669`, ícone `compass`)
     - `hospedagem` (`#2563EB`, ícone `bed`)
     - `artesanato` (`#7C3AED`, ícone `palette`)
     - `transporte` (`#0891B2`, ícone `bus`)
     - `saude` (`#DC2626`, ícone `heart-pulse`)
     - `seguranca` (`#1E3A8A`, ícone `shield`)
     - `outros` (`#6B7280`, ícone `help-circle`)
   - O grupo visual determina a **cor do marcador (pin)**, o **chip primário da barra de filtros rápidos** e a cor de destaque temático.

2. **Nível 2 — Tipos Específicos Controlados (`actor_types`):**
   - Cada ator canônico é vinculado a exatamente **1 tipo específico** (`type_id UUID REFERENCES app_private.actor_types(id)`), que por sua vez pertence a exatamente **1 grupo visual** (`category_id UUID REFERENCES app_private.actor_categories(id)`).
   - O tipo específico define o **rótulo legível** nos cards e detalhes (ex: *"Farmácia & Drogaria"*, *"Posto de Combustível"*, *"Praia Fluvial"*), o **ícone secundário especializado** e o **comportamento espacial** (`spatial_scope`).

3. **Indexação por Aliases (`aliases text[]`):**
   - A entidade `actor_types` inclui um array indexado de sinônimos, expressões populares, termos de busca e variações ortográficas para viabilizar:
     - Normalização determinística e automatizada na ingestão de dados brutos (SEMTUR e Google).
     - Busca textual rápida (*full-text search* / fuzzy match) no frontend.

---

### 3.2 Matriz Completa de Mapeamento: Grupos, Tipos, Aliases, Escopo e Regras de Publicação

Abaixo apresenta-se o mapeamento exaustivo de todos os **41 tipos SEMTUR**, **17 normalizados legados** e **12 tipos Google** auditados:

| `group_slug` (Pai) | `type_slug` (Canônico) | `label` (Exibição) | `icon` (Lucide) | Ordem | `aliases` (Ingestão, Busca e Normalização) | `spatial_scope` (ADR 0011) | `publication_rule` (ADR 0014) | Origem Coberta (SEMTUR / Google / Recorte) |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: | :--- | :--- |
| **`alimentacao`** | `restaurante` | Restaurante & Gastronomia | `utensils` | 10 | `restaurante`, `restaurantes e bares`, `alimentacao`, `culinaria`, `gastronomia`, `comida regional`, `peixaria`, `self-service`, `churrascaria`, `pizzaria`, `bistrô`, `buffet` | `route_corridor` | Público se `published`. Selo SEMTUR se originário do inventário oficial. | SEMTUR: `restaurantes e bares em Santarém` (100), `Alter do Chão` (45), `Ponta de Pedras` (12), `Praia do Maracanã` (5), `Carapanari` (3), `Pajuçara` (2). Google: `restaurante/alimentação` (161). Recorte: `alimentação` (76). |
| **`alimentacao`** | `bar_vida_noturna` | Bar & Vida Noturna | `beer` | 11 | `bar`, `bares`, `botequim`, `pub`, `vida noturna`, `casa de shows`, `musica ao vivo`, `boate`, `cervejaria`, `lounge` | `route_corridor` | Público se `published`. Selo SEMTUR se originário do inventário. | SEMTUR: `casa de shows` (4), `restaurantes e bares...` (bares). Google: `bar/vida noturna` (94). |
| **`alimentacao`** | `barraca_praia` | Barraca de Praia & Quiosque | `umbrella` | 12 | `barraca de praia`, `quiosque`, `cabana de praia`, `restaurante de praia`, `apoio de praia`, `barraca` | `route_corridor` | Público se `published`. Relevância máxima no corredor de praias (Pindobal / Alter). | SEMTUR: barracas em Alter do Chão e Ponta de Pedras. |
| **`alimentacao`** | `cafe_lanchonete` | Café & Lanchonete | `coffee` | 13 | `lanchonete`, `café`, `cafeteria`, `padaria`, `lanches`, `salgaderia`, `doceria`, `sorveteria`, `sucos` | `route_corridor` | Público se `published`. | SEMTUR: lanchonetes e cafés cadastrados. Google: snacks / confeitarias. |
| **`alimentacao`** | `mercado_conveniencia` | Mercado & Conveniência | `shopping-cart` | 14 | `mercado`, `mercadinho`, `conveniencia`, `mercearia`, `supermercado`, `empório`, `armazém`, `quitanda`, `minimercado` | `both` | Público se `published`. Apoio essencial ao turista (abastecimento) no corredor e na cidade. | SEMTUR: `mercado` (9). Google: `mercadinho/conveniência` (93). Recorte: `mercado` (7). |
| **`alimentacao`** | `feira_livre` | Feira & Mercado Produtor | `store` | 15 | `feira`, `feiras`, `feiras `, `feira livre`, `mercado municipal`, `feira do produtor`, `mercado de peixe`, `feira agroecológica` | `both` | Público se `published`. Patrimônio gastronômico e abastecimento. | SEMTUR: `feiras ` (5). |
| **`atrativos`** | `atrativo_natural` | Atrativo Natural & Trilha | `trees` | 20 | `atrativos naturais`, `atrativo natural`, `natureza`, `ponto turistico`, `trilha`, `floresta`, `igarapé`, `lago`, `encontro das águas` | `route_corridor` | Público institucional (`published`). Soberania SEMTUR para patrimônio natural. | SEMTUR: `atrativos naturais` (14). Google: `atrativo/centro turístico` (50). |
| **`atrativos`** | `praia_fluvial` | Praia Fluvial | `sun` | 21 | `praias fluviais`, `praia fluvial`, `praia`, `ponta de pedras`, `pindobal`, `maracanã`, `carapanari`, `ilha do amor`, `cururu` | `route_corridor` | Público institucional (`published`). Soberania SEMTUR. Selo SEMTUR. | SEMTUR: `praias fluviais` (12). |
| **`atrativos`** | `ilha` | Ilha & Bancada de Areia | `waves` | 22 | `ilhas`, `ilha`, `arquipélago`, `bancada de areia`, `banco de areia` | `route_corridor` | Público institucional (`published`). | SEMTUR: `ilhas` (2). |
| **`atrativos`** | `serra_mirante` | Serra & Mirante Panorâmico | `mountain` | 23 | `serras`, `serra`, `mirante`, `morro`, `vista panoramica`, `serra da piroca`, `serra do saubal` | `route_corridor` | Público institucional (`published`). | SEMTUR: `serras` (3). |
| **`atrativos`** | `unidade_conservacao` | Unidade de Conservação & APA | `shield-check` | 24 | `unidade de conservação`, `área de proteção ambiental`, `apa`, `flona tapajós`, `parna`, `resex tapajós-arapiuns`, `parque ambiental`, `uc` | `both` | Público institucional (`published`). Máxima relevância socioambiental. | SEMTUR: `unidade de conservação` (2), `área de proteção ambiental` (5). |
| **`atrativos`** | `patrimonio_cultural` | Patrimônio Cultural & Histórico | `landmark` | 25 | `edificações e arquiteturas`, `obras de arte`, `instituições culturais`, `bibliotecas`, `patrimonio`, `centro cultural`, `museu`, `monumento`, `teatro` | `both` | Público institucional (`published`). Selo SEMTUR. | SEMTUR: `edificações e arquiteturas` (10), `bibliotecas` (10), `obras de arte` (10), `instituições culturais` (1). |
| **`atrativos`** | `templo_religioso` | Igreja & Templo Histórico | `church` | 26 | `igrejas e templos`, `igreja`, `templo`, `religioso`, `catedral`, `capela`, `santuário`, `paróquia`, `matriz` | `both` | Público se `published`. Atração histórico-cultural e referência de comunidade. | SEMTUR: `Igrejas e Templos` (56). Recorte: `religioso` (30). |
| **`atrativos`** | `lazer_balneario` | Balneário & Clube de Lazer | `umbrella` | 27 | `balneários/chácaras`, `balneário`, `chácara`, `clubes sociais, desportivos e de lazer`, `serviços/equipamentos de lazer`, `parque aquático`, `clube` | `route_corridor` | Público se `published`. | SEMTUR: `balneários/chácaras` (4), `clubes sociais...` (6), `serviços/equipamentos de lazer` (14). |
| **`hospedagem`** | `pousada_hotel` | Hotel & Pousada | `bed` | 30 | `hospedagem`, `hotel`, `pousada`, `hostel`, `albergue`, `resort`, `dormitório`, `suítes`, `ecopousada` | `route_corridor` | Público se `published`. Selo SEMTUR se cadastrado na prefeitura. | SEMTUR: `hospedagem` (141). Google: `hospedagem` (150). Recorte: `hospedagem` (113). |
| **`hospedagem`** | `casa_temporada` | Casa de Temporada & Camping | `home` | 31 | `casas de temporada`, `casa de temporada`, `aluguel temporada`, `chalé`, `bangalô`, `flat`, `camping`, `area de camping`, `casa de praia` | `route_corridor` | Público se `published`. Modalidade essencial em Alter do Chão e Pindobal. | SEMTUR: `casas de temporada` (15). Recorte: `casas de temporada` (10). |
| **`artesanato`** | `artesanato_local` | Artesanato & Produção Comunitária | `palette` | 40 | `artesanato`, `artesao`, `trançado`, `cerâmica tapajônica`, `cuia`, `souvenir`, `lembranças`, `associação de artesãos`, `arte indígena`, `biojoias` | `route_corridor` | Público se `published`. Foco em economia solidária e fomento comunitário; selo SEMTUR. | SEMTUR: `artesanato` (12). Recorte: `artesanato` (7). |
| **`transporte`** | `terminal_aeroporto` | Aeroporto & Pistas de Pouso | `plane` | 50 | `aeroporto`, `aeroporto de santarem`, `maestro wilson fonseca`, `pista de pouso`, `taxi aereo`, `táxi aéreo em santarem e regioes`, `aerodromo` | `both` | Público institucional (`published`). Origem canônica do contrato de rota. | SEMTUR: `táxi aéreo em santarem e regioes` (6). Contrato: Origem Aeroporto. |
| **`transporte`** | `terminal_porto` | Porto & Terminal Hidroviário | `anchor` | 51 | `porto`, `terminal hidroviario`, `hidroviaria`, `balsa`, `transporte fluvial em Santarém`, `transporte fluvial`, `cais`, `embarcadouro`, `porto de santarém` | `both` | Público institucional (`published`). Origem canônica do contrato de rota. | SEMTUR: `transporte fluvial em Santarém` (34). Contrato: Origem Porto. |
| **`transporte`** | `terminal_rodoviario` | Rodoviária & Transporte Coletivo | `bus` | 52 | `rodoviaria`, `terminal rodoviario`, `ponto de onibus`, `vans`, `vans e micro-ônibus`, `transporte intermunicipal`, `transfer`, `coletivo` | `both` | Público institucional (`published`). Origem canônica do contrato de rota. | SEMTUR: `transporte intermunicipal/interestadual/urbano` (4), `vans e micro-ônibus` (9). Contrato: Origem Rodoviária. Recorte: `transporte` (11). |
| **`transporte`** | `catraia_travessia` | Catraia & Travessia Fluvial | `ship` | 53 | `catraias em alter do chão`, `catraias`, `catraia`, `catraieiro`, `travessia ilha do amor`, `canoa`, `voadeira`, `barqueiro` | `route_corridor` | Público se `published`. Patrimônio cultural imaterial e transporte local. | SEMTUR: `catraias em alter do chão` (1), `lanchas em alter do chão...` (2). |
| **`transporte`** | `posto_combustivel` | Posto de Combustível | `fuel` | 54 | `posto de gasolina`, `combustível`, `gasolina`, `etanol`, `diesel`, `posto`, `abastecimento`, `posto 24h` | `both` | Público se `published`. **Infraestrutura viária vital** no corredor da rodovia e na cidade. | Google: `posto de gasolina` (45). Recorte: `combustível` (9). |
| **`transporte`** | `locadora_mobilidade` | Locadora de Veículos & Táxi | `car` | 55 | `locadoras de veículos`, `locadora veículos`, `aluguel de carro`, `rent a car`, `taxi`, `mototaxi`, `ponto de taxi` | `both` | Público se `published`. | SEMTUR: `locadoras de veículos` (15). Recorte: `locadora veículos` (9). |
| **`transporte`** | `agencia_turismo` | Agência de Turismo & Receptivo | `briefcase` | 56 | `agências`, `agência turismo`, `agências de passagens aéreas`, `receptivo`, `operadora de turismo`, `guias`, `passeios de barco` | `both` | Público se `published`. | SEMTUR: `agências` (42), `agências de passagens aéreas` (2). Recorte: `agência turismo` (2). |
| **`saude`** | `hospital_upa` | Hospital & Pronto Socorro | `heart-pulse` | 60 | `hospital/UPA`, `hospital`, `upa`, `pronto socorro`, `unidade de pronto atendimento`, `emergencia medica`, `samu`, `hospital municipal`, `hospital regional` | `citywide_essential` | **Serviço Essencial Vital:** Visível na cidade e sob demanda na rota sem esticar zoom. | Google: `hospital/UPA` (38). Recorte: `emergência` (1). |
| **`saude`** | `posto_saude_ubs` | UBS & Posto de Saúde | `cross` | 61 | `posto de saúde`, `posto de saude`, `ubs`, `unidade basica de saude`, `centro de saude`, `posto medico`, `saude da familia`, `ambulatorio` | `citywide_essential` | **Serviço Essencial:** Atenção primária municipal. | SEMTUR: postos de saúde catalogados. Google: `posto de saúde` (33). Recorte: `saúde` (1). |
| **`saude`** | `farmacia` | Farmácia & Drogaria | `pill` | 62 | `farmácia`, `farmacia`, `drogaria`, `medicamentos`, `remédios`, `plantão farmácia`, `drogaria 24h` | `both` | **Serviço de Saúde & Apoio:** Visível na cidade e acessível ao longo da rota em deslocamentos. | Google: `farmácia` (48). Recorte: `farmácia` (2). |
| **`seguranca`** | `seguranca_publica` | Polícia, Delegacia & Bombeiros | `shield` | 70 | `delegacia`, `bombeiros`, `seguranca`, `segurança`, `polícia militar`, `polícia civil`, `corpo de bombeiros`, `guarda municipal`, `defesa civil`, `resgate`, `4 gbm` | `citywide_essential` | **Serviço Essencial de Proteção:** Visível na cidade e sob demanda na rota. Selo SEMTUR se oficial. | SEMTUR: `seguranca` (11). Google: `delegacia` (17), `bombeiros` (3). |
| **`seguranca`** | `conselho_tutelar_protecao` | Conselho Tutelar & Proteção Social | `scale` | 71 | `conselho tutelar`, `proteção social`, `cidadania`, `direitos humanos`, `vara da infância`, `assistência social`, `cras`, `creas` | `citywide_essential` | **Proteção Social & Cidadania:** Serviço público essencial. | Google: `conselho tutelar` (5). SEMTUR: `cidadania` (4). |
| **`outros`** | `servicos_publicos_cartorios` | Serviços Públicos & Cartórios | `landmark` | 90 | `cartórios`, `cartório`, `cartorios`, `serviço público`, `repartição pública`, `prefeitura`, `fórum`, `tabelionato`, `registro civil` | `citywide_essential` | Público institucional (`published`). | SEMTUR: `cartórios` (4). Recorte: `cartórios` (3), `serviço público` (4). |
| **`outros`** | `comercio_eventos` | Comércio & Serviços para Eventos | `store` | 91 | `para eventos`, `serviços para eventos`, `serviços/equipamentos para eventos`, `shopping/lojas de departamento`, `shopping/lojas`, `loja`, `decoração`, `som e iluminação` | `both` | Curadoria Editorial (`review` / `published` se auditado). | SEMTUR: `serviços/equipamentos para eventos` (36), `shopping/lojas de departamento` (2). Recorte: `serviços para eventos` (16), `shopping/lojas` (2). |
| **`outros`** | `nao_classificado` | Não Classificado / Triagem | `help-circle` | 99 | `indefinido`, `desconhecido`, `outros`, `nao classificado`, `a classificar`, `sem categoria` | `route_corridor` | **Retenção na Fila de Triagem Editorial** (`draft` / `review`). Visível no mapa apenas com pin neutro (`#6B7280`) e chip 'Outros' (ADR 0010 C2). | Registros sem categoria clara no raw. |

---

## 4. Acessibilidade, Contraste e Ergonomia Digital (WCAG 2.1 AA)

1. **Prevenção de Sobrecarga Cognitiva e Contraste Estrito:**
   - A fixação em **8 grupos cromáticos canônicos** garante obediência à Lei de Miller e previne indistinguibilidade visual sob luz solar intensa na Amazônia.
   - **Regra de Contraste para `alimentacao` (`#D97706`):**
     - Em superfícies preenchidas (pin no mapa): fundo `#D97706` com ícone branco e borda sutil contrastante `#78350F` (contraste de componente 3.01:1).
     - Em tipografia/chips de texto: utilizar o tom derivado `#B45309` (contraste **4.62:1** sobre fundo branco, passando plenamente no critério WCAG AA para texto normal).
2. **Não Dependência Exclusiva de Cor (WCAG 1.4.1):**
   - Todo marcador exibe ícone semântico vetorizado no centro.
   - O toque ou foco no marcador abre card inferior exibindo claramente o grupo e o subtipo em texto legível.
   - Semântica de Leitor de Tela:
     ```tsx
     accessibilityRole="button"
     accessibilityLabel={`Categoria: ${actor.category.label}, Tipo: ${actor.type.label}, Estabelecimento: ${actor.name}`}
     accessibilityHint="Toque duas vezes para abrir a ficha completa e opções de trajeto"
     accessibilityState={{ selected: isSelected }}
     ```
3. **Alvos de Toque e Ergonomia Tátil (WCAG 2.5.5 / 2.5.8):**
   - Marcadores do mapa: hit area mínima de **44x44 dp**.
   - Chips da barra de filtros: altura mínima de **44 dp** com espaçamento de 8 dp.
   - Botões de alternância de modo de câmera ("Ver Cidade" / "Voltar para a Rota"): mínimo de **48x48 dp**.

---

## 5. Comportamento Espacial e Enquadramento de Câmera (Harmonização com ADR 0011)

1. **Isolamento de `route_bounds`:**
   - Durante a navegação no percurso Santarém → Alter do Chão → Pindobal, a câmera do mapa mantém-se enquadrada exclusivamente na geometria da rota selecionada + padding do corredor (`route_bounds`).
   - Serviços municipais categorizados como `citywide_essential` (ex: Hospital Municipal de Santarém, Delegacia Central) **nunca distorcem o zoom da rota**.
2. **Serviços Fora da Visão no Modo Rota:**
   - Se o turista acionar o filtro "Saúde" no modo Rota, os serviços presentes no corredor (ex: farmácias de estrada ou UBS em Alter do Chão) aparecem diretamente.
   - Caso os principais hospitais estejam situados no centro urbano fora da visão atual, o app exibe uma notificação contextual não intrusiva com botão de ação:
     > *"2 hospitais e 1 UPA disponíveis no polo urbano — [Ver no Mapa da Cidade]"*.
3. **Alternância Suave para `city_bounds`:**
   - O acionamento voluntário do modo "Ver Cidade" transiciona a câmera para `city_bounds`, renderizando toda a malha de serviços essenciais sem perder a linha da rota em segundo plano.

---

## 6. Questões Objetivas Submetidas à Homologação do Owner (Gate H25.2)

Submetem-se ao Owner do Projeto as seguintes decisões estruturais para homologação formal:

```text
[QUESTÃO H25.2-1: Arquitetura Taxonômica em 2 Níveis]
Confirma a adoção da taxonomia hierárquica em 2 níveis (8 grupos visuais canônicos do ADR 0010 + tabela actor_types com slugs específicos, aliases e escopo espacial)?
(A) Sim, aprovar a arquitetura hierárquica em 2 níveis conforme a matriz deste ADR (Recomendado).
(B) Não, desejo alterar a quantidade de grupos primários.

[QUESTÃO H25.2-2: Alocação de Postos de Combustível e Farmácias]
Aprova a classificação de Postos de Combustível no grupo 'transporte' (ícone fuel, escopo both) e Farmácias no grupo 'saude' (ícone pill, escopo both)?
(A) Sim, aprovar alocação de combustível em transporte e farmácias em saúde (Recomendado).
(B) Não, alocar ambos em 'outros' ou criar grupo separado.

[QUESTÃO H25.2-3: Alocação de Proteção Social, Cidadania e Templos Religiosos]
Aprova a alocação de Conselho Tutelar em 'seguranca' (proteção social e cidadania), Cartórios/Serviços Públicos em 'outros' (serviços administrativos) e Igrejas/Templos em 'atrativos' (patrimônio histórico e cultural)?
(A) Sim, aprovar conforme a matriz proposta (Recomendado).
(B) Propor remanejamento específico.

[QUESTÃO H25.2-4: Regra Estrita do Selo SEMTUR para Subtipos]
Confirma que o badge visual 'SEMTUR' é concedido exclusivamente aos estabelecimentos com vínculo institucional comprovado no inventário municipal (actor_external_refs.source_id = 'semtur_inventory'), independentemente do tipo específico, sendo vedada a concessão automática a registros originários apenas do Google Places?
(A) Sim, confirmar regra estrita de proveniência conforme ADR 0014 (Recomendado).
(B) Não, flexibilizar critérios de selo.
```

---

## 7. Consequências Técnicas e Próximos Passos

1. **Estado Atual:** A tarefa **ECO-2503** é finalizada no estado **`BLOCKED`** em conformidade com o protocolo do Gate Humano **H25.2**.
2. **Desbloqueio de Tarefas Subsequentes (após aceite do Owner):**
   - **ECO-2504 (Database Schema & Proveniência):** Criará as tabelas `actor_categories`, `actor_types`, `raw_source_records`, `actor_external_refs` e `reconciliation_candidates` refletindo integralmente esta taxonomia.
   - **ECO-2505 (Ingestão SEMTUR):** Utilizará os `aliases` deste ADR para normalização idempotente dos 674 registros institucionais.
   - **ECO-2506 (Associação Espacial PostGIS):** Aplicará os filtros espaciais baseados em `spatial_scope` (`route_corridor`, `citywide_essential`, `both`).
   - **ECO-2512 (UI de Mapa, Pins e Filtros):** Renderizará os 8 chips primários e os ícones/rótulos dos subtipos com acessibilidade WCAG 2.1 AA.
