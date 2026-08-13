import type { MapPin, RouteGeometry } from '../../api/types';
import {
  getBoundsCoordinates,
  getFitCoordinates,
  getGeometryCoordinates,
  getInitialRegion,
  getItemCoordinate,
} from './MapAdapter.helpers';

const pin: MapPin = {
  id: '11111111-1111-4111-8111-111111111111',
  actor_id: '22222222-2222-4222-8222-222222222222',
  name: 'Ponto Pindobal',
  category_slug: 'hospedagem',
  latitude: -2.63,
  longitude: -54.94,
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

  it('falls back from bounds to geometry and then pins', () => {
    expect(getFitCoordinates(null, geometry, [pin])).toEqual(getGeometryCoordinates(geometry));
    expect(getFitCoordinates(null, null, [pin])).toEqual([
      { latitude: -2.63, longitude: -54.94 },
    ]);
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
});
