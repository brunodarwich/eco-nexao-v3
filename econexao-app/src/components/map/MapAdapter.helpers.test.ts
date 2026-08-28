import type { MapPin, RouteGeometry } from '../../api/types';
import {
  SELECTION_PIN_COLOR,
  applyCoincidentOffsets,
  clusterPins,
  filterPinsByModeAndCategory,
  formatCoordinateDisplay,
  getBoundsCoordinates,
  getClusterAccessibilityLabel,
  getFitCoordinates,
  getGeometryCoordinates,
  getInitialRegion,
  getItemAccessibilityLabel,
  getItemCategoryLabel,
  getItemCoordinate,
  getItemPinColor,
  getItemPinIcon,
  getSelectionPinAccessibilityLabel,
  isClusterItem,
} from './MapAdapter.helpers';

const pin: MapPin = {
  id: '11111111-1111-4111-8111-111111111111',
  actor_id: '22222222-2222-4222-8222-222222222222',
  name: 'Ponto Pindobal',
  category_slug: 'hospedagem',
  category_label: 'Hospedagem',
  color: '#2563EB',
  icon: 'bed',
  latitude: -2.63,
  longitude: -54.94,
  layer: 'route_corridor',
};

const geometry: RouteGeometry = {
  id: '33333333-3333-4333-8333-333333333333',
  route_origin_id: '44444444-4444-4444-8444-444444444444',
  provider: 'osrm',
  geojson: {
    type: 'LineString',
    coordinates: [
      [-54.95, -2.64],
      [-54.9, -2.6],
    ],
  },
};

describe('MapAdapter shared geospatial helpers', () => {
  it('converts API pins and GeoJSON [longitude, latitude] safely', () => {
    expect(getItemCoordinate(pin)).toEqual({ latitude: -2.63, longitude: -54.94 });
    expect(getGeometryCoordinates(geometry)).toEqual([
      { latitude: -2.64, longitude: -54.95 },
      { latitude: -2.6, longitude: -54.9 },
    ]);
  });

  it('rejects invalid coordinates rather than placing them at a fake position', () => {
    expect(getItemCoordinate({ ...pin, latitude: 100 })).toBeNull();
    expect(
      getGeometryCoordinates({
        ...geometry,
        geojson: { type: 'LineString', coordinates: [[-54.95, 95]] },
      })
    ).toEqual([]);
  });

  it('uses API bounds as the authoritative fit target', () => {
    const bounds = { min_lat: -2.7, max_lat: -2.5, min_lng: -55, max_lng: -54.8 };
    expect(getBoundsCoordinates(bounds)).toEqual([
      { latitude: -2.7, longitude: -55 },
      { latitude: -2.5, longitude: -54.8 },
    ]);
    expect(getFitCoordinates(bounds, geometry, [pin])).toEqual(getBoundsCoordinates(bounds));
  });

  it('não reconstrói enquadramento local quando bounds autoritativo está ausente', () => {
    expect(getFitCoordinates(null, geometry, [pin])).toEqual([]);
    expect(getFitCoordinates(null, null, [pin])).toEqual([]);
  });

  it('derives a padded initial region from fit coordinates', () => {
    const region = getInitialRegion([
      { latitude: -2.7, longitude: -55 },
      { latitude: -2.5, longitude: -54.8 },
    ]);

    expect(region.latitude).toBeCloseTo(-2.6);
    expect(region.longitude).toBeCloseTo(-54.9);
    expect(region.latitudeDelta).toBeCloseTo(0.25);
    expect(region.longitudeDelta).toBeCloseTo(0.25);
  });

  describe('Contract visual and accessibility helpers', () => {
    it('extracts color and icon directly from contract pin', () => {
      expect(getItemPinColor(pin)).toBe('#2563EB');
      expect(getItemPinIcon(pin)).toBe('bed');
      expect(getItemCategoryLabel(pin)).toBe('Hospedagem');
    });

    it('rejects missing visual metadata instead of inventing production fallbacks', () => {
      const minimalItem = {
        id: '999',
        name: 'Ponto Genérico',
      };
      expect(getItemPinColor(minimalItem)).toBeNull();
      expect(getItemPinIcon(minimalItem)).toBeNull();
      expect(getItemCategoryLabel(minimalItem)).toBe('Geral');
    });

    it('generates rich accessible label for screen readers', () => {
      expect(getItemAccessibilityLabel(pin, false)).toBe(
        'Ponto no mapa: Ponto Pindobal. Categoria: Hospedagem'
      );
      expect(getItemAccessibilityLabel(pin, true)).toBe(
        'Ponto no mapa: Ponto Pindobal. Categoria: Hospedagem, selecionado'
      );
    });

    it('formats coordinates and generates accessible selection pin label (ECO-2311)', () => {
      const coord = { latitude: -2.4431, longitude: -54.7083 };
      expect(formatCoordinateDisplay(coord)).toBe('-2.4431, -54.7083');
      expect(getSelectionPinAccessibilityLabel(coord)).toBe(
        'Ponto de partida selecionado no mapa: -2.4431, -54.7083. Arraste para reposicionar.'
      );
      expect(getSelectionPinAccessibilityLabel(coord, 'Meu Ponto')).toBe(
        'Meu Ponto: -2.4431, -54.7083. Arraste para reposicionar.'
      );
      expect(getSelectionPinAccessibilityLabel(null)).toBe(
        'Ponto de partida selecionado no mapa'
      );
    });
  });

  describe('filterPinsByModeAndCategory (ECO-2307)', () => {
    const pinsSample: MapPin[] = [
      {
        id: 'pin-corridor-1',
        actor_id: 'actor-1',
        name: 'Pousada Corredor',
        category_slug: 'hospedagem',
        category_label: 'Hospedagem',
        color: '#2563EB',
        icon: 'bed',
        latitude: -2.63,
        longitude: -54.94,
        layer: 'route_corridor',
      },
      {
        id: 'pin-city-1',
        actor_id: 'actor-2',
        name: 'Restaurante Cidade',
        category_slug: 'gastronomia',
        category_label: 'Gastronomia',
        color: '#D97706',
        icon: 'restaurant',
        latitude: -2.44,
        longitude: -54.72,
        layer: 'citywide_essential',
      },
      {
        id: 'pin-both-1',
        actor_id: 'actor-3',
        name: 'Guia Local Ambos',
        category_slug: 'experiencias',
        category_label: 'Experiências',
        color: '#059669',
        icon: 'compass',
        latitude: -2.55,
        longitude: -54.85,
        layer: 'both',
      },
      {
        id: 'pin-no-layer',
        actor_id: 'actor-4',
        name: 'Ponto Sem Camada Definida',
        category_slug: 'hospedagem',
        category_label: 'Hospedagem',
        color: '#2563EB',
        icon: 'bed',
        latitude: -2.60,
        longitude: -54.90,
        layer: 'route_corridor',
      },
    ];

    it('in route mode, only corridor, both, or default pins are included', () => {
      const result = filterPinsByModeAndCategory(pinsSample, 'route', '', null);
      expect(result.map((p) => p.id)).toEqual(['pin-corridor-1', 'pin-both-1', 'pin-no-layer']);
    });

    it('in route mode, preserves selection state without leaking a city pin into route layer', () => {
      const result = filterPinsByModeAndCategory(pinsSample, 'route', '', 'actor-2');
      expect(result.map((p) => p.id)).toEqual([
        'pin-corridor-1',
        'pin-both-1',
        'pin-no-layer',
      ]);
    });

    it('in city mode, all pins are included when no category filter is active', () => {
      const result = filterPinsByModeAndCategory(pinsSample, 'city', '', null);
      expect(result.map((p) => p.id)).toEqual([
        'pin-corridor-1',
        'pin-city-1',
        'pin-both-1',
        'pin-no-layer',
      ]);
    });

    it('in city mode with category filter, filters by category unless selectedActorId', () => {
      const result = filterPinsByModeAndCategory(pinsSample, 'city', 'hospedagem', null);
      expect(result.map((p) => p.id)).toEqual(['pin-corridor-1', 'pin-no-layer']);

      // When actor-2 (gastronomia) is selected, it must still be returned
      const resultWithSelected = filterPinsByModeAndCategory(
        pinsSample,
        'city',
        'hospedagem',
        'actor-2'
      );
      expect(resultWithSelected.map((p) => p.id)).toEqual([
        'pin-corridor-1',
        'pin-city-1',
        'pin-no-layer',
      ]);
    });

    it('supports city_bounds seamlessly in bounds coordinate helper', () => {
      const cityBounds = { min_lat: -2.8, max_lat: -2.4, min_lng: -55.2, max_lng: -54.5 };
      expect(getBoundsCoordinates(cityBounds)).toEqual([
        { latitude: -2.8, longitude: -55.2 },
        { latitude: -2.4, longitude: -54.5 },
      ]);
    });
  });

  describe('clusterPins and applyCoincidentOffsets (ECO-2307/ECO-2315)', () => {
    const densePins: MapPin[] = Array.from({ length: 30 }, (_, i) => ({
      id: `dense-pin-${i}`,
      actor_id: `actor-${i}`,
      name: `Ponto ${i}`,
      category_slug: i % 2 === 0 ? 'alimentacao' : 'hospedagem',
      category_label: i % 2 === 0 ? 'Alimentação' : 'Hospedagem',
      color: i % 2 === 0 ? '#D97706' : '#2563EB',
      icon: i % 2 === 0 ? 'utensils' : 'bed',
      latitude: -2.63 + (i % 3) * 0.0005,
      longitude: -54.94 + (i % 3) * 0.0005,
      layer: 'route_corridor',
    }));

    it('clusters dense pins at low zoom level and produces accessible labels', () => {
      const renderables = clusterPins(densePins, 12);
      expect(renderables.length).toBeLessThan(densePins.length);
      const clusters = renderables.filter(isClusterItem);
      expect(clusters.length).toBeGreaterThan(0);

      const firstCluster = clusters[0];
      expect(firstCluster.count).toBeGreaterThanOrEqual(2);
      expect(firstCluster.bounds.min_lat).toBeLessThanOrEqual(firstCluster.latitude);
      expect(firstCluster.bounds.max_lat).toBeGreaterThanOrEqual(firstCluster.latitude);

      const a11yLabel = getClusterAccessibilityLabel(firstCluster);
      expect(a11yLabel).toContain('Grupo com');
      expect(a11yLabel).toContain('Toque para aproximar');
    });

    it('preserves the selected actor as an individual pin even when surrounding pins cluster', () => {
      const selectedId = 'actor-5';
      const renderables = clusterPins(densePins, 12, selectedId);

      const selectedRenderable = renderables.find(
        (r) => !isClusterItem(r) && ('actor_id' in r ? r.actor_id === selectedId : r.id === selectedId)
      );
      expect(selectedRenderable).toBeDefined();
    });

    it('applies coincident offsets at high zoom instead of clustering', () => {
      const coincidentPins: MapPin[] = [
        {
          id: 'p1',
          actor_id: 'act-1',
          name: 'Barraca 1',
          category_slug: 'alimentacao',
          category_label: 'Alimentação',
          color: '#D97706',
          icon: 'utensils',
          latitude: -2.63000,
          longitude: -54.94000,
          layer: 'route_corridor',
        },
        {
          id: 'p2',
          actor_id: 'act-2',
          name: 'Barraca 2',
          category_slug: 'alimentacao',
          category_label: 'Alimentação',
          color: '#D97706',
          icon: 'utensils',
          latitude: -2.63000,
          longitude: -54.94000,
          layer: 'route_corridor',
        },
      ];

      const renderables = clusterPins(coincidentPins, 16);
      expect(renderables.length).toBe(2);
      expect(renderables.every((r) => !isClusterItem(r))).toBe(true);

      const [p1, p2] = renderables as (MapPin & { offsetCoordinate?: { latitude: number; longitude: number } })[];
      expect(p1.offsetCoordinate).toBeDefined();
      expect(p2.offsetCoordinate).toBeDefined();
      expect(p1.offsetCoordinate!.latitude).not.toEqual(p2.offsetCoordinate!.latitude);
    });

    it('handles empty items array gracefully', () => {
      expect(clusterPins([], 12)).toEqual([]);
      expect(applyCoincidentOffsets([])).toEqual([]);
    });
  });
});
