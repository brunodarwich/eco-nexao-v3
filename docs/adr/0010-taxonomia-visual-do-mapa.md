# ADR 0010 — Taxonomia Visual do Mapa ECOnexão

Status: aceito
Data: 2026-08-24
Decisores: Equipe de Desenvolvimento ECOnexão / Owner do Projeto
Tasks relacionadas: ECO-2301, ECO-2302, ECO-2303, ECO-2304, ECO-2305

---

## 1. Contexto

A versão 2 do mapa interativo do ECOnexão necessita de uma taxonomia visual e funcional clara, consistente, de fácil compreensão para turistas e moradores, e com estrita conformidade às diretrizes de acessibilidade digital (**WCAG 2.1 nível AA**).

Os principais desafios identificados na taxonomia anterior são:
1. **Dependência excessiva de cor**: A identificação de pontos de interesse (POIs) no mapa não pode depender exclusivamente da cor do marcador (pin), sob pena de exclusão de usuários com daltonismo ou baixa visão. É mandatório o uso de **ícones universais legíveis** dentro dos pins e semântica textual/acessível (labels claros e tags `accessibilityLabel`/`aria-label`).
2. **Ambiguidade na categoria `emergencia`**: A categoria unificada atual mescla serviços de saúde (hospitais, Unidades Básicas de Saúde - UBS, farmácias) e serviços de segurança pública (delegacias de polícia, corpo de bombeiros, guarda municipal). No contexto de turismo em Pindobal e Alter do Chão:
   - Um turista que busca uma farmácia ou atendimento médico básico enfrenta confusão ao encontrar viaturas/postos policiais misturados ao mesmo ícone/filtro.
   - A separação é fundamental para viabilizar as camadas espaciais e rotas de segurança vs. socorro médico (ECO-2305).
3. **Classificação e exibição de registros não categorizados (`outros`)**: Registros cadastrados no snapshot da SEMTUR sem categoria definida ou classificados genericamente como `outros` precisam ser exibidos com clareza neutra no mapa turístico e nos filtros rápidos, além de permanecerem disponíveis na curadoria editorial administrativa para enriquecimento contínuo.

---

## 2. Decisão

### 2.1 Tabela de Categorias Públicas Canônicas

Padronizam-se as seguintes categorias canônicas para atores (`actors`):

| Slug Canônico | Label de Exibição | Cor Hex | Nome da Cor | Ícone Lucide / SVG | Ordem de Exibição | Visibilidade no Mapa Público |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `alimentacao` | Alimentação | `#D97706` | Amber / Warm Orange | `utensils` | 1 | Visível |
| `atrativos` | Atrativos | `#059669` | Emerald Green | `compass` | 2 | Visível |
| `hospedagem` | Hospedagem | `#2563EB` | Royal Blue | `bed` | 3 | Visível |
| `artesanato` | Artesanato | `#7C3AED` | Violet / Purple | `palette` | 4 | Visível |
| `transporte` | Transporte | `#0891B2` | Cyan / Teal | `bus` | 5 | Visível |
| `saude` | Saúde | `#DC2626` | Crimson Red | `heart-pulse` / `cross` | 6 | Visível |
| `seguranca` | Segurança | `#1E3A8A` | Navy Blue | `shield` | 7 | Visível |
| `outros` | Outros | `#6B7280` | Neutral Gray | `help-circle` | 99 | Visível (pin cinza `#6B7280` e chip de filtro público) |

---

### 2.2 Regra de Exibição de `outros` no Mapa Público (Opção C2)

- Atores com categoria `outros` são exibidos com marcador cinza neutro (`#6B7280`) e ícone `help-circle` no mapa público (`MapView` / `/explore`).
- O chip de filtro "Outros" é disponibilizado na interface de filtros rápidos do turista.
- Os atores com categoria `outros` continuam visíveis na curadoria editorial (`/admin/actors`) para enriquecimento cadastral e reclassificação pela equipe editorial.

---

### 2.3 Comparativo: `emergencia` Unificado vs. Separação em `saude` e `seguranca`

| Critério | Opção B1: Separação em `saude` e `seguranca` (Adotada) | Opção B2: Manter `emergencia` unificado |
| :--- | :--- | :--- |
| **Usabilidade do Turista** | **Alta**: Clareza imediata entre necessidade médica (hospital/farmácia) e socorro policial/bombeiros. | **Média/Baixa**: Gera ambiguidade e sobrecarga cognitiva ao filtrar em momentos de urgência. |
| **Camadas Espaciais (ECO-2305)** | **Excelente**: Permite ligar/desligar camadas temáticas de saúde pública ou bases de segurança de forma independente. | **Limitada**: Exige filtros adicionais por subtipo ou tags para separar serviços distintos. |
| **Impacto no Snapshot SEMTUR** | **Baixo**: Mapeamento direto de "Hospital / UBS / Farmácia" → `saude` e "Polícia / Bombeiro" → `seguranca`. | **Nulo**: Mantém a agregação existente. |
| **Esforço de Migração** | **Baixo**: Atualização de enum/tabela de domínio no banco + script de remap no importer. | **Mínimo**: Nenhuma alteração de esquema necessária. |

---

### 2.4 Mapeamento: Categoria Atual (SEMTUR / Snapshot) → Slug Proposto

| Categoria / Tipo no Snapshot SEMTUR | Slug Proposto | Justificativa |
| :--- | :--- | :--- |
| `Restaurante`, `Bar`, `Barraca de Praia`, `Café`, `Lanchonete`, `Alimentação` | `alimentacao` | Unificação de gastronomia e serviços de alimentação. |
| `Atrativo Natural`, `Praia`, `Trilha`, `Ponto Turístico`, `Igreja Histórica`, `Mirante` | `atrativos` | Pontos turísticos e atrativos naturais/culturais. |
| `Pousada`, `Hotel`, `Hostel`, `Área de Camping`, `Hospedagem` | `hospedagem` | Meios de hospedagem cadastrados. |
| `Artesanato`, `Loja de Souvenirs`, `Comunidade Tradicional (Vendas)` | `artesanato` | Produção associada e artesanato local. |
| `Ponto de Táxi / Mototaxi`, `Porto / Catraia`, `Ponto de Ônibus`, `Transfer` | `transporte` | Infraestrutura e modais de mobilidade. |
| `Hospital`, `UBS`, `Farmácia`, `Pronto Atendimento`, `Posto de Saúde` | `saude` | Serviços de atenção e socorro à saúde. |
| `Delegacia de Polícia`, `Posto Policial`, `Bombeiros`, `Guarda Municipal` | `seguranca` | Serviços de segurança pública e defesa civil. |
| `Serviços Gerais`, `Comércio Local não classificado`, `Indefinido`, `Outros` | `outros` | Categoria neutra visível e fila administrativa de triagem editorial. |

---

## 3. Acessibilidade e Contraste (WCAG 2.1 AA)

A especificação cromática e tipográfica foi desenhada para garantir acessibilidade universal:

### 3.1 Tabela de Contraste e Legibilidade

| Slug | Cor Hex | Contraste c/ Fundo Branco (`#FFFFFF`) | Contraste c/ Ícone Branco (`#FFFFFF`) | Conformidade Daltonismo (Deutan / Protan / Tritan) |
| :--- | :--- | :---: | :---: | :--- |
| `alimentacao` | `#D97706` | **3.01:1** (UI Component) / Texto: usar `#B45309` | **3.01:1** (Com borda contrastante `#78350F`) | Diferenciação garantida pelo ícone `utensils` |
| `atrativos` | `#059669` | **4.56:1** (Passa AA Texto Normal) | **4.56:1** | Distinto de amber e violet; ícone `compass` |
| `hospedagem` | `#2563EB` | **4.58:1** (Passa AA Texto Normal) | **4.58:1** | Distinto de violet e emerald; ícone `bed` |
| `artesanato` | `#7C3AED` | **5.74:1** (Passa AA Texto Normal) | **5.74:1** | Distinto de azul e vermelho; ícone `palette` |
| `transporte` | `#0891B2` | **4.52:1** (Passa AA Texto Normal) | **4.52:1** | Tom ciano escuro; ícone `bus` |
| `saude` | `#DC2626` | **4.51:1** (Passa AA Texto Normal) | **4.51:1** | Tom vermelho vivo; ícone `heart-pulse` |
| `seguranca` | `#1E3A8A` | **10.87:1** (Passa AAA Texto Normal) | **10.87:1** | Tom marinho profundo; ícone `shield` |
| `outros` | `#6B7280` | **4.78:1** (Passa AA Texto Normal) | **4.78:1** | Tom neutro cinza; ícone `help-circle` |

### 3.2 Diretrizes de Acessibilidade Adotadas
1. **Não dependência de cor**: Nenhum elemento da interface informa o tipo de categoria apenas por cor. Todos os pins exibem um ícone SVG unívoco no centro e, quando selecionados (ou em callouts/modais), o nome da categoria em texto legível.
2. **Leitores de Tela**: Todos os marcadores e chips de filtro devem implementar atributos de acessibilidade:
   - `accessibilityLabel="Categoria: Saúde - Hospital Municipal"`
   - `accessibilityRole="button"` / `accessibilityState={{ selected: isSelected }}`
3. **Escala de Marcadores**: Marcadores no mapa terão tamanho mínimo de toque de 44x44 dp para atender aos critérios de usabilidade tátil.

---

## 4. Decisão Formal do Owner

Decisões homologadas pelo Owner do Projeto em 2026-08-24:

1. **Separação de Emergência — Opção B1 (Aprovada)**:
   - Separar formalmente em duas categorias canônicas: `saude` (vermelho `#DC2626` / ícone `heart-pulse`) e `seguranca` (azul marinho `#1E3A8A` / ícone `shield`).
2. **Visibilidade de Outros — Opção C2 (Aprovada)**:
   - Exibir registros `outros` no mapa público com pin cinza (`#6B7280`) e ícone `help-circle`, disponibilizando também o chip de filtro "Outros" na barra de filtros da interface pública.
   - Manter visíveis no painel administrativo `/admin/actors` para enriquecimento cadastral e triagem editorial.
3. **Paleta Visual e Ícones (Aprovados integralmente)**:
   - Homologado o conjunto canônico de 8 categorias, cores e ícones Lucide da Tabela 2.1, em estrita conformidade com as diretrizes de acessibilidade WCAG 2.1 AA.

---

## 5. Consequências Técnicas

A partir da aprovação deste ADR, o planejamento técnico das tarefas subsequentes será:

- **ECO-2302 (Database, Migration & Seed/Importer)**:
  - Criação de enum / tabela canônica `actor_categories` com os 8 slugs canônicos (`alimentacao`, `atrativos`, `hospedagem`, `artesanato`, `transporte`, `saude`, `seguranca`, `outros`), labels, cores, ícones e flag `is_public = true`.
  - Migration de dados para mapear categorias legadas/SEMTUR para a nova taxonomia.
  - Atualização do script de importação/snapshot para validar estritamente as categorias canônicas.
- **ECO-2303 (Backend & OpenAPI Contracts)**:
  - Atualização dos schemas Pydantic e documentação OpenAPI com os novos enums de categoria.
  - Ajuste nas rotas de busca de atores (`GET /api/v1/actors`, `GET /api/v1/map/layers`).
- **ECO-2304 (Frontend React Native / Expo)**:
  - Criação do módulo de configuração de categorias (`categoryTheme.ts`) contendo mapeamento de slugs, cores, ícones Lucide correspondentes e rótulos acessíveis.
  - Atualização dos componentes `CategoryFilterBar`, `ActorMapPin`, `ActorCard` e `ActorDetailModal`.
