import type { MapBounds, RouteGeometry } from '../../api/types';
import type { FlexiblePinItem, MapClusterItem, MapCoordinate, MapRenderableItem } from './MapAdapter.types';

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

export const isClusterItem = (item: MapRenderableItem): item is MapClusterItem => {
  return 'isCluster' in item && item.isCluster === true;
};

export const getClusterAccessibilityLabel = (cluster: MapClusterItem): string => {
  const count = cluster.count;
  const category = cluster.primaryCategoryLabel || 'pontos turísticos';
  return `Grupo com ${count} locais de ${category}. Toque para aproximar e visualizar cada ponto no mapa.`;
};

/**
 * Calculates a gentle circular offset for pins sharing identical or near-identical coordinates
 * so that all points remain visually distinct, clickable, and accessible at high zoom.
 */
export const applyCoincidentOffsets = <T extends FlexiblePinItem>(
  items: T[],
  selectedActorId?: string | null
): (T & { offsetCoordinate?: MapCoordinate })[] => {
  if (items.length <= 1) return items;

  const groups = new Map<string, T[]>();
  for (const item of items) {
    const coord = getItemCoordinate(item);
    if (!coord) continue;
    const key = `${coord.latitude.toFixed(5)},${coord.longitude.toFixed(5)}`;
    const group = groups.get(key) || [];
    group.push(item);
    groups.set(key, group);
  }

  const result: (T & { offsetCoordinate?: MapCoordinate })[] = [];

  for (const item of items) {
    const coord = getItemCoordinate(item);
    if (!coord) {
      result.push(item);
      continue;
    }
    const key = `${coord.latitude.toFixed(5)},${coord.longitude.toFixed(5)}`;
    const group = groups.get(key) || [];

    if (group.length <= 1) {
      result.push(item);
      continue;
    }

    const indexInGroup = group.indexOf(item);
    const isSelected = Boolean(
      selectedActorId &&
        (getItemId(item) === selectedActorId ||
          ('actor_id' in item && item.actor_id === selectedActorId))
    );

    if (isSelected) {
      result.push({
        ...item,
        offsetCoordinate: coord,
      });
      continue;
    }

    const angle = (2 * Math.PI * indexInGroup) / group.length;
    const radius = 0.00018;
    const offsetCoordinate: MapCoordinate = {
      latitude: coord.latitude + radius * Math.cos(angle),
      longitude: coord.longitude + radius * Math.sin(angle),
    };

    result.push({
      ...item,
      offsetCoordinate,
    });
  }

  return result;
};

/**
 * Deterministic clustering algorithm for map pins.
 * Groups nearby pins at low zoom levels into clusters with bounding boxes and counts.
 * Preserves the selectedActorId as an individual highlighted pin always.
 */
export const clusterPins = (
  items: FlexiblePinItem[],
  zoomLevel: number,
  selectedActorId?: string | null
): MapRenderableItem[] => {
  if (items.length === 0) return [];

  if (zoomLevel >= 16) {
    return applyCoincidentOffsets(items, selectedActorId);
  }

  // Calculate degree radius corresponding to 40 screen pixels at given zoomLevel
  const pixelRadius = 40;
  const radiusDeg = (pixelRadius * 360) / (256 * Math.pow(2, Math.min(zoomLevel, 16)));

  const validItems: { item: FlexiblePinItem; coord: MapCoordinate }[] = [];
  let selectedEntry: { item: FlexiblePinItem; coord: MapCoordinate } | null = null;

  for (const item of items) {
    const coord = getItemCoordinate(item);
    if (!coord) continue;

    const isSelected = Boolean(
      selectedActorId &&
        (getItemId(item) === selectedActorId ||
          ('actor_id' in item && item.actor_id === selectedActorId))
    );

    if (isSelected) {
      selectedEntry = { item, coord };
    } else {
      validItems.push({ item, coord });
    }
  }

  const assigned = new Set<number>();
  const clusters: { items: FlexiblePinItem[]; centroid: MapCoordinate }[] = [];

  for (let i = 0; i < validItems.length; i++) {
    if (assigned.has(i)) continue;

    assigned.add(i);
    const clusterItems: FlexiblePinItem[] = [validItems[i].item];
    let sumLat = validItems[i].coord.latitude;
    let sumLng = validItems[i].coord.longitude;

    for (let j = i + 1; j < validItems.length; j++) {
      if (assigned.has(j)) continue;

      const dLat = validItems[j].coord.latitude - validItems[i].coord.latitude;
      const dLng = validItems[j].coord.longitude - validItems[i].coord.longitude;
      const dist = Math.sqrt(dLat * dLat + dLng * dLng);

      if (dist <= radiusDeg) {
        assigned.add(j);
        clusterItems.push(validItems[j].item);
        sumLat += validItems[j].coord.latitude;
        sumLng += validItems[j].coord.longitude;
      }
    }

    clusters.push({
      items: clusterItems,
      centroid: {
        latitude: sumLat / clusterItems.length,
        longitude: sumLng / clusterItems.length,
      },
    });
  }

  // Merge clusters whose centroids are within collision distance (1.2 * radiusDeg)
  let merged = true;
  while (merged) {
    merged = false;
    for (let i = 0; i < clusters.length; i++) {
      for (let j = i + 1; j < clusters.length; j++) {
        const dLat = clusters[i].centroid.latitude - clusters[j].centroid.latitude;
        const dLng = clusters[i].centroid.longitude - clusters[j].centroid.longitude;
        const dist = Math.sqrt(dLat * dLat + dLng * dLng);
        if (dist < radiusDeg * 1.2) {
          clusters[i].items.push(...clusters[j].items);
          const total = clusters[i].items.length;
          const sumLat = clusters[i].items.reduce((s, it) => s + getItemCoordinate(it)!.latitude, 0);
          const sumLng = clusters[i].items.reduce((s, it) => s + getItemCoordinate(it)!.longitude, 0);
          clusters[i].centroid = {
            latitude: sumLat / total,
            longitude: sumLng / total,
          };
          clusters.splice(j, 1);
          merged = true;
          break;
        }
      }
      if (merged) break;
    }
  }

  const renderable: MapRenderableItem[] = [];
  const singlePins: FlexiblePinItem[] = [];

  for (let idx = 0; idx < clusters.length; idx++) {
    const { items: clusterItems, centroid } = clusters[idx];

    if (clusterItems.length === 1 && zoomLevel >= 14) {
      singlePins.push(clusterItems[0]);
      continue;
    }

    const lats = clusterItems.map((i) => getItemCoordinate(i)!.latitude);
    const lngs = clusterItems.map((i) => getItemCoordinate(i)!.longitude);

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    const categoryCounts: Record<string, { count: number; color: string; label: string }> = {};
    for (const item of clusterItems) {
      const slug = getItemCategory(item);
      const color = getItemPinColor(item) || '#1B4D3E';
      const label = getItemCategoryLabel(item);
      if (!categoryCounts[slug]) {
        categoryCounts[slug] = { count: 0, color, label };
      }
      categoryCounts[slug].count += 1;
    }

    let maxCatSlug = 'outros';
    let maxCatCount = -1;
    let maxCatColor = '#1B4D3E';
    let maxCatLabel = 'Pontos de Interesse';

    for (const [slug, data] of Object.entries(categoryCounts)) {
      if (data.count > maxCatCount) {
        maxCatCount = data.count;
        maxCatSlug = slug;
        maxCatColor = data.color;
        maxCatLabel = data.label;
      }
    }

    const latPadding = Math.max((maxLat - minLat) * 0.2, 0.005);
    const lngPadding = Math.max((maxLng - minLng) * 0.2, 0.005);

    const clusterItem: MapClusterItem = {
      isCluster: true,
      id: `cluster-${idx}-${clusterItems.length}`,
      count: clusterItems.length,
      latitude: centroid.latitude,
      longitude: centroid.longitude,
      bounds: {
        min_lat: minLat - latPadding,
        max_lat: maxLat + latPadding,
        min_lng: minLng - lngPadding,
        max_lng: maxLng + lngPadding,
      },
      primaryCategorySlug: maxCatSlug,
      primaryCategoryLabel: maxCatLabel,
      primaryColor: maxCatColor,
      items: clusterItems,
    };

    renderable.push(clusterItem);
  }

  if (singlePins.length > 0) {
    const offsetSinglePins = applyCoincidentOffsets(singlePins, selectedActorId);
    renderable.push(...offsetSinglePins);
  }

  if (selectedEntry) {
    renderable.push(selectedEntry.item);
  }

  return renderable;
};
