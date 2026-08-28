import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOT_DIR = path.resolve(__dirname, '../screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// 8 Categorias Canônicas (ADR 0010)
const CANONICAL_CATEGORIES = [
  { slug: 'alimentacao', label: 'Alimentação', color: '#D97706', icon: 'utensils' },
  { slug: 'atrativos', label: 'Atrativos', color: '#059669', icon: 'compass' },
  { slug: 'hospedagem', label: 'Hospedagem', color: '#2563EB', icon: 'bed' },
  { slug: 'artesanato', label: 'Artesanato', color: '#7C3AED', icon: 'palette' },
  { slug: 'transporte', label: 'Transporte', color: '#0891B2', icon: 'bus' },
  { slug: 'saude', label: 'Saúde', color: '#DC2626', icon: 'heart-pulse' },
  { slug: 'seguranca', label: 'Segurança', color: '#1E3A8A', icon: 'shield' },
  { slug: 'outros', label: 'Outros', color: '#6B7280', icon: 'help-circle' },
];

const MOCK_REGIONS = [
  { id: 'reg-santarem-belterra', name: 'Santarém / Belterra', state_code: 'PA', is_active: true }
];

// 3 Origens Reais do Contrato Territorial Pindobal
const MOCK_ORIGINS = [
  {
    id: 'origin-porto',
    name: 'Porto de Santarém',
    latitude: -2.428482,
    longitude: -54.701835,
    description: 'Terminal Hidroviário de Santarém (45,2 km até Pindobal)',
    distance_m: 45229,
    duration_s: 3600,
  },
  {
    id: 'origin-aeroporto',
    name: 'Aeroporto Internacional de Santarém',
    latitude: -2.424780,
    longitude: -54.785830,
    description: 'Aeroporto Maestro Wilson Fonseca (41,5 km até Pindobal)',
    distance_m: 41451,
    duration_s: 3200,
  },
  {
    id: 'origin-rodoviaria',
    name: 'Terminal Rodoviário de Santarém',
    latitude: -2.443185,
    longitude: -54.730652,
    description: 'Terminal Rodoviário de Santarém (42,3 km até Pindobal)',
    distance_m: 42318,
    duration_s: 3400,
  },
];

const MOCK_ROUTE = {
  id: 'rota-santarem-pindobal',
  region_id: 'reg-santarem-belterra',
  title: 'Rota Santarém → Praia de Pindobal',
  summary: 'Percurso ecoturístico conectando o centro histórico, Alter do Chão e a praia de Pindobal.',
  description: 'Percurso de 45 km ao longo da Rodovia Everaldo Martins (PA-457) e Estrada de Pindobal.',
  distance_km: 45.2,
  duration_hours: 1.0,
  difficulty: 'facil',
  is_active: true,
  city_bounds: {
    min_lat: -2.60,
    max_lat: -2.40,
    min_lng: -55.02,
    max_lng: -54.68,
  },
  bounds: {
    min_lat: -2.57,
    max_lat: -2.42,
    min_lng: -54.99,
    max_lng: -54.70,
  },
  origins: MOCK_ORIGINS,
};

// Fixture sintética representativa de 175 POIs distribuídos no corredor Santarém-Alter-Pindobal
// Zona 1: Santarém Urbana (55 pins) em torno de lat -2.43, lng -54.71
// Zona 2: Alter do Chão (65 pins) em torno de lat -2.505, lng -54.953
// Zona 3: Praia de Pindobal (55 pins) em torno de lat -2.558, lng -54.978
const MOCK_PINS = Array.from({ length: 175 }, (_, i) => {
  const cat = CANONICAL_CATEGORIES[i % CANONICAL_CATEGORIES.length];
  let baseLat = -2.430;
  let baseLng = -54.710;
  let zoneName = 'Santarém';

  if (i >= 55 && i < 120) {
    baseLat = -2.505;
    baseLng = -54.953;
    zoneName = 'Alter do Chão';
  } else if (i >= 120) {
    baseLat = -2.558;
    baseLng = -54.978;
    zoneName = 'Pindobal';
  }

  const isCoincident = i % 8 === 0;
  const latOffset = isCoincident ? 0 : (Math.sin(i * 1.7) * 0.006);
  const lngOffset = isCoincident ? 0 : (Math.cos(i * 1.7) * 0.006);

  return {
    id: `pin-${i + 1}`,
    actor_id: `actor-${i + 1}`,
    name: i === 125 ? 'Pousada Pindobal Encanto' : `${cat.label} ${zoneName} ${i + 1}`,
    category_slug: cat.slug,
    category_label: cat.label,
    color: cat.color,
    icon: cat.icon,
    latitude: baseLat + latOffset,
    longitude: baseLng + lngOffset,
    distance_from_origin_m: 500 + i * 250,
    layer: 'route_corridor',
  };
});

// Legenda derivada dos 175 pins da fixture
const MOCK_LEGEND = CANONICAL_CATEGORIES.map((cat, idx) => {
  const count = MOCK_PINS.filter((p) => p.category_slug === cat.slug).length;
  return {
    category_slug: cat.slug,
    label: cat.label,
    color: cat.color,
    icon: cat.icon,
    count,
    sort_order: idx + 1,
  };
});

// Mock de atores para o catálogo da rota
const MOCK_ACTORS = {
  items: MOCK_PINS.map((p) => ({
    id: p.actor_id,
    name: p.name,
    category_slug: p.category_slug,
    category_label: p.category_label,
    color: p.color,
    icon: p.icon,
    location: { latitude: p.latitude, longitude: p.longitude },
    address: `${p.name}, Margem do Rio Tapajós`,
    description: `Ponto turístico e comunitário registrado na região do Tapajós.`,
    is_verified: true,
  })),
  total: 175,
  page: 1,
  limit: 200,
};

// SVG Tile generator determinístico para os tiles Leaflet
const SVG_TILE = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" fill="#F3EFE6" />
  <path d="M0 60 Q64 40 128 80 T256 60 L256 120 Q192 100 128 140 T0 120 Z" fill="#D5E8D4" opacity="0.7"/>
  <path d="M30 0 C50 70 170 150 210 256" stroke="#E6D7B8" stroke-width="3" fill="none"/>
  <path d="M0 160 C70 170 150 200 256 190" stroke="#BFD9E8" stroke-width="6" fill="none"/>
</svg>`;

async function setupApiMocks(page: import('@playwright/test').Page) {
  // Tile requests -> SVG map tile
  await page.route('**/*.tile.openstreetmap.org/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'image/svg+xml',
      body: SVG_TILE,
    });
  });

  // Supabase Auth
  await page.route('**/auth/v1/**', async (route) => {
    const json = {
      access_token: 'mock-test-jwt-token',
      token_type: 'bearer',
      expires_in: 3600,
      refresh_token: 'mock-refresh-token',
      user: {
        id: 'user-e2e-tester',
        aud: 'authenticated',
        role: 'authenticated',
        email: 'tester@econexao.org.br',
        app_metadata: { provider: 'email' },
        user_metadata: { full_name: 'Turista ECOnexão' },
      },
    };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(json) });
  });

  // API Client Routes
  await page.route('**/api/v1/**', async (route) => {
    const url = route.request().url();
    const pathname = new URL(url).pathname;

    if (pathname === '/api/v1/regions') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: MOCK_REGIONS }),
      });
      return;
    }

    if (
      pathname === '/api/v1/actor-categories' ||
      pathname === '/api/v1/actor_categories' ||
      pathname === '/api/v1/categories'
    ) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: CANONICAL_CATEGORIES }),
      });
      return;
    }

    if (pathname.endsWith('/map')) {
      const urlObj = new URL(url);
      const originId = urlObj.searchParams.get('origin_id') || 'origin-porto';
      const selectedOrigin = MOCK_ORIGINS.find((o) => o.id === originId) || MOCK_ORIGINS[0];

      // Computar pins com distância específica para cada origem selecionada
      const originPins = MOCK_PINS.map((pin, idx) => ({
        ...pin,
        distance_from_origin_m: Math.round(selectedOrigin.distance_m * 0.1 + idx * 200),
      }));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            route_id: 'rota-santarem-pindobal',
            selected_origin_id: originId,
            origin_distance_m: selectedOrigin.distance_m,
            origin_duration_s: selectedOrigin.duration_s,
            bounds: MOCK_ROUTE.bounds,
            city_bounds: MOCK_ROUTE.city_bounds,
            pins: originPins,
            legend: MOCK_LEGEND,
            geometry: {
              id: `geom-${originId}`,
              route_origin_id: originId,
              provider: 'osrm',
              geojson: {
                type: 'LineString',
                coordinates: [
                  [selectedOrigin.longitude, selectedOrigin.latitude],
                  [-54.8500, -2.4800],
                  [-54.9530, -2.5050],
                  [-54.9785, -2.5585],
                ],
              },
              encoded_polyline: null,
              distance_m: selectedOrigin.distance_m,
              duration_s: selectedOrigin.duration_s,
            },
          },
        }),
      });
      return;
    }

    if (pathname.endsWith('/origins')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: MOCK_ORIGINS }),
      });
      return;
    }

    if (pathname.endsWith('/actors')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: MOCK_ACTORS.items, meta: { total: 175, page: 1, limit: 200 } }),
      });
      return;
    }

    if (pathname.startsWith('/api/v1/routes/') && pathname !== '/api/v1/routes') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: MOCK_ROUTE }),
      });
      return;
    }

    if (pathname === '/api/v1/routes') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [MOCK_ROUTE],
          meta: { total: 1, page: 1, limit: 10, total_pages: 1 },
        }),
      });
      return;
    }

    if (pathname.includes('/favorite-actors') || pathname.includes('/favorite-routes')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: [], meta: { total: 0, page: 1, limit: 50 } }),
      });
      return;
    }

    if (pathname.includes('/preferences') || pathname.includes('/me') || pathname.includes('/bootstrap')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: { active_region_id: 'reg-santarem-belterra', favorites: [] } }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ data: {} }),
    });
  });
}

test.describe('Validação em Navegador Real & Acessibilidade WCAG 2.1 AA (ECO-2101 / ECO-2307 / ECO-2315)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
  });

  test('Jornada 1: Modais Acessíveis, Focus Trap, Navegação por Teclado e Restauração de Foco', async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    const ariaHiddenWarnings: string[] = [];

    page.on('console', (msg) => {
      const text = msg.text();
      if (msg.type() === 'error') {
        consoleErrors.push(text);
      }
      if (text.includes('Blocked aria-hidden') || text.includes('aria-hidden because its descendant retained focus')) {
        ariaHiddenWarnings.push(text);
      }
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    // 1. Carregar a aplicação na Home
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const header = page.locator('text=ECOnexão').first();
    await expect(header).toBeVisible({ timeout: 10000 });

    // Salvar Screenshot 01: Home (falha imediatamente se o screenshot falhar)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${testInfo.project.name}_01_app_home.png`) });

    // 2. Localizar o botão de disparo da Região
    const regionTrigger = page.locator('[aria-label*="Região atual"]').first();
    await expect(regionTrigger).toBeVisible();

    // 3. Focar no botão disparador via Teclado e disparar com Enter
    await regionTrigger.focus();
    await page.keyboard.press('Enter');

    // 4. Diálogo modal deve estar visível no DOM
    const modalDialog = page.locator('[role="dialog"]').first();
    await expect(modalDialog).toBeVisible({ timeout: 5000 });

    // Verificar que aria-hidden="true" foi aplicado no #root
    const rootAriaHidden = await page.evaluate(() => {
      const root = document.getElementById('root');
      return root ? root.getAttribute('aria-hidden') : null;
    });
    expect(rootAriaHidden).toBe('true');

    // Salvar Screenshot 02: Modal Aberto
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${testInfo.project.name}_02_modal_open.png`) });

    // 5. Testar Focus Trap Completo com Tab, Shift+Tab e Contenção Estrita
    const isInitiallyInside = await modalDialog.evaluate((d) => d.contains(document.activeElement));
    expect(isInitiallyInside).toBe(true);

    const focusableElements = await modalDialog.locator(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    ).all();
    expect(focusableElements.length).toBeGreaterThanOrEqual(2);

    // Percorrer elementos com Tab e verificar contenção em CADA passo
    for (let step = 0; step < focusableElements.length; step++) {
      await page.keyboard.press('Tab');
      const isInside = await modalDialog.evaluate((d) => d.contains(document.activeElement));
      expect(isInside).toBe(true);
    }

    // Ciclagem do último elemento para o primeiro com Tab
    await focusableElements[focusableElements.length - 1].focus();
    await page.keyboard.press('Tab');
    const isFirstElementFocused = await focusableElements[0].evaluate((first) => document.activeElement === first);
    expect(isFirstElementFocused).toBe(true);

    // Ciclagem do primeiro elemento para o último com Shift+Tab
    await focusableElements[0].focus();
    await page.keyboard.press('Shift+Tab');
    const isLastElementFocused = await focusableElements[focusableElements.length - 1].evaluate((last) => document.activeElement === last);
    expect(isLastElementFocused).toBe(true);

    // 6. Fechar o diálogo com a tecla Escape
    await page.keyboard.press('Escape');
    await page.waitForTimeout(150);

    // 7. Diálogo deve ter desaparecido
    await expect(modalDialog).not.toBeVisible();

    // Verificar que aria-hidden foi removido do #root
    const rootAriaHiddenAfter = await page.evaluate(() => {
      const root = document.getElementById('root');
      return root ? root.getAttribute('aria-hidden') : null;
    });
    expect(rootAriaHiddenAfter).toBeNull();

    // 8. Foco deve estar restaurado exatamente no disparador da região
    const isTriggerFocused = await page.evaluate(() => {
      const active = document.activeElement;
      const trigger = document.querySelector('[aria-label*="Região atual"]');
      return Boolean(active === trigger || trigger?.contains(active));
    });
    expect(isTriggerFocused).toBe(true);

    // Salvar Screenshot 03: Foco Restaurado
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${testInfo.project.name}_03_after_modal.png`) });

    // 9. Auditoria Axe-core no estado da Home
    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    expect(axeResults.violations).toHaveLength(0);

    // 10. Assert rigoroso de console
    expect(ariaHiddenWarnings).toHaveLength(0);
    expect(consoleErrors).toHaveLength(0);
  });

  test('Jornada 2: Mapa, 175 Pins, 3 Origens Reais, Teclado nos Clusters, Filtro e Catálogo', async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    const ariaHiddenWarnings: string[] = [];

    page.on('console', (msg) => {
      const text = msg.text();
      if (msg.type() === 'error') {
        console.log('BROWSER ERROR:', text);
        consoleErrors.push(text);
      }
      if (text.includes('Blocked aria-hidden') || text.includes('aria-hidden because its descendant retained focus')) {
        ariaHiddenWarnings.push(text);
      }
    });
    page.on('pageerror', (err) => {
      console.log('PAGE ERROR:', err.message, err.stack);
      consoleErrors.push(err.message);
    });

    // 1. Navegar diretamente para a tela de mapa da rota
    await page.goto('/route/rota-santarem-pindobal/map');
    await page.waitForLoadState('networkidle');

    // Esperar pelo container do Leaflet e pelos clusters
    const mapContainer = page.locator('.leaflet-container');
    await expect(mapContainer).toBeVisible({ timeout: 10000 });

    // Salvar Screenshot 04: Mapa Inicial com Clusters
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${testInfo.project.name}_04_map_initial.png`) });

    // 2. Verificar que 175 pins da fixture foram agrupados em clusters não sobrepostos
    const clusterMarkers = page.locator('.leaflet-marker-icon.econexao-cluster-icon-wrapper');
    await expect(clusterMarkers.first()).toBeVisible({ timeout: 10000 });
    const clusterCount = await clusterMarkers.count();
    expect(clusterCount).toBeGreaterThanOrEqual(2);
    expect(clusterCount).toBeLessThanOrEqual(10);

    // Métrica visual estrita: Verificar que NENHUM cluster tem bounding box sobreposto na tela
    await page.waitForTimeout(400); // Aguardar posicionamento inicial do Leaflet
    const clusterBoxes = await clusterMarkers.evaluateAll((elements) =>
      elements.map((el) => {
        const rect = el.getBoundingClientRect();
        return {
          left: rect.left,
          right: rect.right,
          top: rect.top,
          bottom: rect.bottom,
          width: rect.width,
          height: rect.height,
          x: rect.x,
          y: rect.y,
        };
      })
    );
    expect(clusterBoxes.length).toBeGreaterThanOrEqual(2);
    expect(clusterBoxes.length).toBeLessThanOrEqual(10);

    let overlapCount = 0;
    for (let i = 0; i < clusterBoxes.length; i++) {
      for (let j = i + 1; j < clusterBoxes.length; j++) {
        const b1 = clusterBoxes[i];
        const b2 = clusterBoxes[j];
        const overlaps =
          !(b1.right < b2.left || b1.left > b2.right || b1.bottom < b2.top || b1.top > b2.bottom);
        if (overlaps) overlapCount++;
      }
    }
    expect(overlapCount).toBe(0);

    // 3. Testar Operabilidade do Cluster por TECLADO (Focus + Enter)
    const targetCluster = clusterMarkers.first();
    await targetCluster.focus();
    await page.keyboard.press('Enter');
    await page.waitForTimeout(600); // Esperar transição de zoom do Leaflet

    // Salvar Screenshot 05: Cluster Expandido
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${testInfo.project.name}_05_cluster_expanded.png`) });

    // 4. Testar Filtro de Categoria Temática
    await page.goto('/route/rota-santarem-pindobal/map');
    await page.waitForLoadState('networkidle');
    const hospedagemChip = page.locator('text=Hospedagem').first();
    await expect(hospedagemChip).toBeVisible({ timeout: 5000 });
    await hospedagemChip.click();
    await page.waitForTimeout(400);

    // Salvar Screenshot 06: Mapa Filtrado por Categoria
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${testInfo.project.name}_06_category_filtered.png`) });

    // 5. Testar as Três Origens Reais do Contrato (Porto, Aeroporto, Rodoviária) com Asserções Estritas
    for (const origin of MOCK_ORIGINS) {
      await page.goto(`/route/rota-santarem-pindobal/map?originId=${origin.id}&actorId=actor-126`);
      await page.waitForLoadState('networkidle');
      await expect(mapContainer).toBeVisible();

      // Verificar que o URL preservou o originId
      const currentUrl = new URL(page.url());
      expect(currentUrl.searchParams.get('originId')).toBe(origin.id);
      expect(currentUrl.searchParams.get('actorId')).toBe('actor-126');

      // Verificar que a distância da origem é renderizada na folha do ator selecionado
      const distanceText = page.locator('text=Distância da origem:').first();
      await expect(distanceText).toBeVisible({ timeout: 5000 });

      // Verificar que o traçado de geometria OSRM no Leaflet está visível
      const polyline = page.locator('.leaflet-overlay-pane svg path').first();
      await expect(polyline).toBeVisible({ timeout: 5000 });
    }

    // 6. Testar Seleção de Ator, Sheet e Navegação para o Catálogo com Preservação de Contexto
    await page.goto('/route/rota-santarem-pindobal/map?originId=origin-rodoviaria&actorId=actor-126');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);

    const actorPin = page.locator('.econexao-map-marker').first();
    await expect(actorPin).toBeVisible({ timeout: 5000 });

    const catalogButton = page.locator('[aria-label*="no catálogo"]').first();
    await expect(catalogButton).toBeVisible({ timeout: 5000 });

    // Salvar Screenshot 07: Ator Selecionado e Sheet Acessível
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${testInfo.project.name}_07_actor_sheet_opened.png`) });

    // Click the catalog button and wait for navigation to the catalog page
    await catalogButton.click();
    // Verify URL contains '/catalog'
    await expect(page).toHaveURL(/catalog/);
    // Give the app a moment to render the new screen
    await page.waitForTimeout(5000);
    // Wait for the catalog header to appear (extended timeout)
    const catalogHeader = page.getByText('Catálogo de Atores');
    await expect(catalogHeader).toBeVisible({ timeout: 60000 });
    // Wait for the search input to appear (extended timeout)
    const searchInput = page.getByLabel('Campo de pesquisa');
    await expect(searchInput).toBeVisible({ timeout: 40000 });
    // Verify the actor card is rendered (extended timeout)
    const actorCard = page.getByText('Pousada Pindobal Encanto').first();
    await expect(actorCard).toBeVisible({ timeout: 30000 });

    // 7. Retornar ao Mapa e Executar Auditoria Axe-core WCAG 2.1 AA SEM NENHUMA EXCLUSÃO (Incluindo todo o Leaflet)
    await page.goto('/route/rota-santarem-pindobal/map?originId=origin-porto');
    await page.waitForLoadState('networkidle');
    await expect(mapContainer).toBeVisible();

    const axeMapResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    expect(axeMapResults.violations).toHaveLength(0);

    // 8. Assert rigoroso de console
    expect(ariaHiddenWarnings).toHaveLength(0);
    expect(consoleErrors).toHaveLength(0);
  });
});
