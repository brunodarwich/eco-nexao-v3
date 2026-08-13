import type { MapBounds, RouteGeometry } from '../../api/types';
import type { FlexiblePinItem } from './MapPin';
import type { MapCoordinate } from './MapAdapter.types';

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
  'actor_id' in item ? item.actor_id : item.id;

export const getItemCategory = (item: FlexiblePinItem): string =>
  'category_slug' in item ? item.category_slug : item.segment;

export const getItemCoordinate = (item: FlexiblePinItem): MapCoordinate | null => {
  if (
    'latitude' in item &&
    isFiniteCoordinate(item.latitude, item.longitude)
  ) {
    return { latitude: item.latitude, longitude: item.longitude };
  }

  if (
    'coordinate' in item &&
    item.coordinate &&
    isFiniteCoordinate(item.coordinate.latitude, item.coordinate.longitude)
  ) {
    return {
      latitude: item.coordinate.latitude as number,
      longitude: item.coordinate.longitude as number,
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
  if (boundsCoordinates.length) return boundsCoordinates;

  const geometryCoordinates = getGeometryCoordinates(geometry);
  if (geometryCoordinates.length) return geometryCoordinates;

  return items.flatMap((item) => {
    const coordinate = getItemCoordinate(item);
    return coordinate ? [coordinate] : [];
  });
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
