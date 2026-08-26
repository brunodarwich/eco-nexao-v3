import type { MapBounds, RouteGeometry } from '../../api/types';
import type { FlexiblePinItem, MapCoordinate } from './MapAdapter.types';

const isFiniteCoordinate = (latitude: unknown, longitude: unknown): boolean =>
  typeof latitude === 'number' &&
  Number.isFinite(latitude) &&
  latitude >= -90 &&
  latitude <= 90 &&
  typeof longitude === 'number' &&
  Number.isFinite(longitude) &&
  longitude >= -180 &&
  longitude <= 180;

export const getItemId = (item: FlexiblePinItem): string =>
  ('actor_id' in item && item.actor_id ? item.actor_id : item.id) || '';

export const filterPinsByModeAndCategory = <T extends FlexiblePinItem>(
  pins: T[],
  mode: 'route' | 'city' = 'route',
  selectedCategory?: string | null,
  selectedActorId?: string | null
): T[] => {
  return pins.filter((pin) => {
    const pinId = getItemId(pin);
    const isSelected = Boolean(selectedActorId && (pinId === selectedActorId || ('actor_id' in pin && pin.actor_id === selectedActorId)));

    // Layer check
    const layer = 'layer' in pin ? pin.layer : undefined;
    if (mode === 'route') {
      const isInRouteLayer = !layer || layer === 'route_corridor' || layer === 'both';
      if (!isInRouteLayer) {
        return false;
      }
    }

    // Selection survives category changes within the active spatial layer, but
    // never leaks a citywide pin into the route camera.
    if (isSelected) {
      return true;
    }

    // Category filter check
    if (selectedCategory && selectedCategory.trim().length > 0) {
      const categorySlug = 'category_slug' in pin ? pin.category_slug : undefined;
      const segment = 'segment' in pin ? pin.segment : undefined;
      if (categorySlug !== selectedCategory && segment !== selectedCategory) {
        return false;
      }
    }

    return true;
  });
};

export const SELECTION_PIN_COLOR = '#EA580C';

export const CONTRACT_PIN_ICONS = [
  'utensils', 'compass', 'bed', 'palette', 'bus', 'heart-pulse', 'cross', 'shield', 'help-circle',
] as const;

export const isContractPinColor = (value: unknown): value is string =>
  typeof value === 'string' && /^#[0-9A-Fa-f]{6}$/.test(value);

export const isContractPinIcon = (value: unknown): value is string =>
  typeof value === 'string' && (CONTRACT_PIN_ICONS as readonly string[]).includes(value);

export const formatCoordinateDisplay = (coord: MapCoordinate): string =>
  `${coord.latitude.toFixed(4)}, ${coord.longitude.toFixed(4)}`;

export const getSelectionPinAccessibilityLabel = (
  coord?: MapCoordinate | null,
  customLabel?: string
): string => {
  const base = customLabel || 'Ponto de partida selecionado no mapa';
  if (!coord) return base;
  return `${base}: ${formatCoordinateDisplay(coord)}. Arraste para reposicionar.`;
};

export const getItemPinColor = (item: FlexiblePinItem): string | null =>
  'color' in item && isContractPinColor(item.color) ? item.color : null;

export const getItemPinIcon = (item: FlexiblePinItem): string | null =>
  'icon' in item && isContractPinIcon(item.icon) ? item.icon : null;

export const getItemCategoryLabel = (item: FlexiblePinItem): string => {
  if (
    'category_label' in item &&
    typeof item.category_label === 'string' &&
    item.category_label.trim().length > 0
  ) {
    return item.category_label;
  }
  if ('category_slug' in item && item.category_slug) {
    return item.category_slug;
  }
  if ('segment' in item && item.segment) {
    return item.segment;
  }
  return 'Geral';
};

export const getItemAccessibilityLabel = (
  item: FlexiblePinItem,
  isSelected: boolean = false
): string => {
  const name = item.name || 'Ponto';
  const category = getItemCategoryLabel(item);
  const selectionStatus = isSelected ? ', selecionado' : '';
  return `Ponto no mapa: ${name}. Categoria: ${category}${selectionStatus}`;
};

export const getItemCategory = (item: FlexiblePinItem): string =>
  ('category_slug' in item && item.category_slug
    ? item.category_slug
    : 'segment' in item && item.segment
    ? item.segment
    : 'todos');

export const getItemCoordinate = (item: FlexiblePinItem): MapCoordinate | null => {
  if (
    'latitude' in item &&
    typeof item.latitude === 'number' &&
    typeof item.longitude === 'number' &&
    isFiniteCoordinate(item.latitude, item.longitude)
  ) {
    return { latitude: item.latitude, longitude: item.longitude };
  }

  if (
    'coordinate' in item &&
    item.coordinate &&
    typeof item.coordinate.latitude === 'number' &&
    typeof item.coordinate.longitude === 'number' &&
    isFiniteCoordinate(item.coordinate.latitude, item.coordinate.longitude)
  ) {
    return {
      latitude: item.coordinate.latitude,
      longitude: item.coordinate.longitude,
    };
  }

  return null;
};

export const getGeometryCoordinates = (
  geometry?: RouteGeometry | null
): MapCoordinate[] => {
  const coordinates = (geometry?.geojson as { coordinates?: [number, number][] } | null | undefined)?.coordinates;
  if (!Array.isArray(coordinates)) return [];

  return coordinates.flatMap(([longitude, latitude]) =>
    isFiniteCoordinate(latitude, longitude) ? [{ latitude, longitude }] : []
  );
};

export const getBoundsCoordinates = (bounds?: MapBounds | null): MapCoordinate[] => {
  if (
    !bounds ||
    !isFiniteCoordinate(bounds.min_lat, bounds.min_lng) ||
    !isFiniteCoordinate(bounds.max_lat, bounds.max_lng) ||
    bounds.min_lat > bounds.max_lat ||
    bounds.min_lng > bounds.max_lng
  ) {
    return [];
  }

  return [
    { latitude: bounds.min_lat, longitude: bounds.min_lng },
    { latitude: bounds.max_lat, longitude: bounds.max_lng },
  ];
};

export const getFitCoordinates = (
  bounds: MapBounds | null | undefined,
  geometry: RouteGeometry | null | undefined,
  items: FlexiblePinItem[]
): MapCoordinate[] => {
  const boundsCoordinates = getBoundsCoordinates(bounds);
  return boundsCoordinates;
};

export const getInitialRegion = (
  coordinates: MapCoordinate[]
): {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
} => {
  if (!coordinates.length) {
    return {
      latitude: -2.636,
      longitude: -54.936,
      latitudeDelta: 0.45,
      longitudeDelta: 0.45,
    };
  }

  const latitudes = coordinates.map(({ latitude }) => latitude);
  const longitudes = coordinates.map(({ longitude }) => longitude);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);

  return {
    latitude: (minLatitude + maxLatitude) / 2,
    longitude: (minLongitude + maxLongitude) / 2,
    latitudeDelta: Math.max((maxLatitude - minLatitude) * 1.25, 0.01),
    longitudeDelta: Math.max((maxLongitude - minLongitude) * 1.25, 0.01),
  };
};
