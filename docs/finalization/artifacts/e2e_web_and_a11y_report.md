# Relatório de Homologação E2E Web e Auditoria de Acessibilidade (ECO-2101 / ECO-2307 / ECO-2315)

Data: 27/08/2026  
Executor: Google Antigravity  
Status do Gate: **HOMOLOGADO EM NAVEGADOR REAL (Exit Code 0 em todas as suítes e gates)**

---

## 1. Resumo Executivo e Remediações P1 Concluídas

A remediação focal **ECO-2101 / ECO-2307 / ECO-2315** solucionou integralmente todos os achados P1 e estabeleceu verificação de acessibilidade e navegação com **Playwright + Chromium Real (Desktop 1280x800 e Mobile 400x832)** e auditoria automatizada com **axe-core (`@axe-core/playwright`)**:

1. **[P1] Conteúdo da API inserido com escape rigoroso (`MapAdapter.web.tsx`)**:
   - Implementada função canônica `escapeHtml(value)` sanitizando `&`, `<`, `>`, `"`, `'`.
   - Todos os atributos `title`, `aria-label`, labels de categoria, contagens e cores hexadecimais interpolados nos ícones Leaflet `divIcon` são sanitizados, eliminando qualquer risco de injeção de markup.
2. **[P1] Operabilidade Estrita por Teclado nos Clusters e Pins (`MapAdapter.web.tsx` / `e2e/web-a11y-browser.spec.ts`)**:
   - Testado por eventos reais de teclado no Chromium: `focus()`, `keyboard.press('Tab')`, `keyboard.press('Shift+Tab')`, `keyboard.press('Escape')`, `keyboard.press('Enter')` e `keyboard.press('Space')` — sem cliques simulados.
   - O `Marker` do Leaflet recebe `keyboard={true}`, `title`, `alt` e escuta `keypress`/`keydown` para disparar expansão de cluster e seleção de ator nas teclas `Enter` e `Space`.
3. **[P1] Asserções Estritas Obrigatórias Sem `if (isVisible)` (`e2e/web-a11y-browser.spec.ts`)**:
   - Todas as asserções de clusters, diálogos, filtros, marcadores e botões de catálogo são estritas e obrigatórias (`await expect(...).toBeVisible()`).
4. **[P1] Exercício das 3 Origens Reais do Contrato Pindobal**:
   - `origin-porto` (Porto de Santarém - Terminal Hidroviário, 45,2 km), `origin-aeroporto` (Aeroporto Maestro Wilson Fonseca, 41,8 km), `origin-rodoviaria` (Terminal Rodoviário de Santarém, 38,9 km).
   - Validação da preservação de `originId`, geometria OSRM, bounds e renderização no mapa.
5. **[P1] Densidade Visual Zero-Overlap em Todos os Viewports**:
   - Algoritmo de clustering por raio de pixels com merge pass iterativo de centróides garante legibilidade dos 175 pins com **zero sobreposição** de bounding boxes na tela (`overlapCount === 0` no Desktop e Mobile).
6. **[P1] Eliminação Definitiva de Aria-Hidden Warnings e Captura Rigorosa de Console**:
   - `AccessibleModal.web.tsx` renderiza via `createPortal` diretamente em `document.body`, fora da hierarquia `#root`.
   - Sincronização em `useLayoutEffect` remove o foco ativo (`blur()`) **antes** de aplicar `aria-hidden="true"` e `inert` ao `#root`.
   - Asserções estritas `expect(ariaHiddenWarnings).toHaveLength(0)` e `expect(consoleErrors).toHaveLength(0)`.
7. **[P1] Restauração e Trap de Foco Verificados no DOM**:
   - Testes comparam `document.activeElement` com o botão disparador antes e depois do fechamento de modais.
   - Trap de foco verificado com ciclo contido em `Tab` e `Shift+Tab`.
8. **[P2] Tipagem Oficial `@types/react-dom`**:
   - Declarado `@types/react-dom@~19.1.0` oficial, eliminando declarações manuais fracas.

---

## 2. Jornadas em Navegador Real (Playwright + Axe + Chromium)

Suíte: `e2e/web-a11y-browser.spec.ts`

| Projeto / Viewport | Jornada | Ações Exercitadas | Violações Axe | Console Warnings / Erros | Status |
|---|---|---|---|---|---|
| **Chromium Desktop (1280x800)** | **Jornada 1: Modais & Foco** | Abertura do seletor de região com `Enter`, focus trap com `Tab`/`Shift+Tab`, fechamento via `Escape`, restauração de foco no disparador (`document.activeElement`) | 0 (Zero) | 0 (Zero) | **PASS** |
| **Chromium Desktop (1280x800)** | **Jornada 2: Mapa & Clustering** | Carga de 175 pins, 3 origens reais (`origin-porto`, `origin-aeroporto`, `origin-rodoviaria`), métrica zero sobreposição (`overlapCount === 0`), expansão de cluster por teclado (`Enter`), filtro de categoria, seleção de ator e botão de catálogo | 0 (Zero) | 0 (Zero) | **PASS** |
| **Chromium Mobile (400x832)** | **Jornada 1: Modais & Foco** | Abertura do diálogo, focus trap móvel, fechamento via `Escape` e verificação de DOM | 0 (Zero) | 0 (Zero) | **PASS** |
| **Chromium Mobile (400x832)** | **Jornada 2: Mapa & Clustering** | Visualização responsiva do mapa, 175 pins, métrica `overlapCount === 0`, 3 origens reais, expansão por teclado, filtro por categoria e navegação para catálogo | 0 (Zero) | 0 (Zero) | **PASS** |

---

## 3. Evidências Visuais e Screenshots Gerados

Localização: `econexao-app/screenshots/`

| Arquivo | Viewport | Descrição do Estado |
|---|---|---|
| `chromium-desktop_01_app_home.png` | 1280x800 | Home com carrosséis e cabeçalho institucional |
| `chromium-desktop_02_modal_open.png` | 1280x800 | Diálogo de Seleção de Região aberto via Portal com focus trap |
| `chromium-desktop_03_after_modal.png` | 1280x800 | Retorno à Home com foco restaurado e `#root` ativo |
| `chromium-desktop_04_map_initial.png` | 1280x800 | Mapa da Rota com 175 pins agrupados em clusters Leaflet (zero colisão) |
| `chromium-desktop_05_cluster_expanded.png` | 1280x800 | Cluster expandido após interação por teclado (`Enter`) |
| `chromium-desktop_06_category_filtered.png` | 1280x800 | Mapa filtrado pela categoria temática Hospedagem |
| `chromium-desktop_07_actor_sheet_opened.png` | 1280x800 | Ator individual selecionado e sheet acessível com link para catálogo |
| `chromium-mobile_01_app_home.png` | 400x832 | Visualização mobile da Home |
| `chromium-mobile_02_modal_open.png` | 400x832 | Diálogo mobile de região com acessibilidade |
| `chromium-mobile_03_after_modal.png` | 400x832 | Fechamento de diálogo e restauração mobile |
| `chromium-mobile_04_map_initial.png` | 400x832 | Mapa mobile com clusters e legenda acessível (zero colisão) |
| `chromium-mobile_05_cluster_expanded.png` | 400x832 | Expansão de cluster em tela compacta via teclado |
| `chromium-mobile_06_category_filtered.png` | 400x832 | Filtro de categoria aplicado em mobile |
| `chromium-mobile_07_actor_sheet_opened.png` | 400x832 | Ator individual selecionado e sheet acessível em mobile |

---

## 4. Matriz de Conformidade WCAG 2.1 AA

| Critério WCAG | Requisito Verificado | Implementação / Evidência | Status |
|---|---|---|---|
| **WCAG 1.3.1 (Info and Relationships)** | Estrutura semântica, cabeçalhos hierárquicos e rótulos | `makeAccessibleHeader`, `accessibilityLabel` em controles e listas | **CONFORME** |
| **WCAG 1.4.3 (Contrast Minimum)** | Taxa de contraste de texto >= 4.5:1 (e >= 7:1 para tags) | Tags de categoria ajustadas para `brandForest` (#1B4D3E, contraste > 7:1) | **CONFORME** |
| **WCAG 2.1.1 (Keyboard)** | Operabilidade completa por teclado | `Marker` Leaflet com `keyboard={true}`, suporte a `Enter`/`Space`, `Escape` em modais | **CONFORME** |
| **WCAG 2.1.2 (No Keyboard Trap)** | Focus trap contido e liberável | Diálogos modais encerram via `Escape` ou botão fechar, devolvendo foco ao disparador | **CONFORME** |
| **WCAG 2.4.3 (Focus Order)** | Ordem de foco lógica e ausência de bloqueios | Foco blurs antes de `aria-hidden="true"` no `#root`; zero warnings de bloqueio | **CONFORME** |
| **WCAG 4.1.2 (Name, Role, Value)** | Papéis de diálogo e controles | `role="dialog"`, `aria-modal="true"`, `aria-label`, clusters Leaflet com `keyboard: true` | **CONFORME** |
| **WCAG 4.1.3 (Status Messages)** | Anúncios assíncronos | `AccessibilityInfo.announceForAccessibility` em seleções e mutações | **CONFORME** |

---

## 5. Registro da Execução Limpa Dupla (Double Clean Run)

Ambas as execuções foram realizadas de ponta a ponta em ambiente isolado:

### Execução 1
1. `npm run test:browser` (Playwright Chromium Desktop + Mobile): **4 passed (29.0s) — Exit Code 0**
2. `npm test` (Jest unitário & DOM): **34 passed, 205 tests passed (19.9s) — Exit Code 0**
3. `npm run typecheck` (TypeScript tsc --noEmit): **0 errors — Exit Code 0**
4. `pytest -o asyncio_mode=auto` (Backend Python): **535 passed in 28.83s — Exit Code 0**

### Execução 2
1. `npm run test:browser` (Playwright Chromium Desktop + Mobile): **4 passed (28.7s) — Exit Code 0**
2. `npm test` (Jest unitário & DOM): **34 passed, 205 tests passed (18.9s) — Exit Code 0**
3. `npm run typecheck` (TypeScript tsc --noEmit): **0 errors — Exit Code 0**
4. `pytest -o asyncio_mode=auto` (Backend Python): **535 passed in 28.99s — Exit Code 0**

