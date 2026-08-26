import type { MapPin, RouteGeometry } from '../../api/types';
import {
  SELECTION_PIN_COLOR,
  filterPinsByModeAndCategory,
  formatCoordinateDisplay,
  getBoundsCoordinates,
  getFitCoordinates,
  getGeometryCoordinates,
  getInitialRegion,
  getItemAccessibilityLabel,
  getItemCategoryLabel,
  getItemCoordinate,
  getItemPinColor,
  getItemPinIcon,
  getSelectionPinAccessibilityLabel,
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
});
