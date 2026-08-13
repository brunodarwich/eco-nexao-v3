import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import L, { type LatLngBoundsExpression, type Map as LeafletMap } from 'leaflet';
import { MapContainer, Marker, Polyline, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

import { theme } from '../../theme/theme';
import { MapControls } from './MapControls';
import {
  getFitCoordinates,
  getGeometryCoordinates,
  getInitialRegion,
  getItemCategory,
  getItemCoordinate,
  getItemId,
} from './MapAdapter.helpers';
import type { MapAdapterProps, MapCoordinate } from './MapAdapter.types';

const MIN_ZOOM = 3;
const MAX_ZOOM = 19;

const toLeafletBounds = (coordinates: MapCoordinate[]): LatLngBoundsExpression | null =>
  coordinates.length
    ? coordinates.map(({ latitude, longitude }) => [latitude, longitude] as [number, number])
    : null;

const getPinColor = (category: string): string => {
  if (category === 'alimentacao' || category === 'gastronomia') return theme.colors.brandSun;
  if (category === 'emergencia' || category === 'saude') return theme.colors.error;
  if (category === 'artesanato' || category === 'comercio') return theme.colors.brandLeaf;
  return theme.colors.brandForest;
};

const createPinIcon = (category: string, selected: boolean) =>
  L.divIcon({
    className: 'econexao-map-marker',
    html: `<span aria-hidden="true" style="display:block;width:${selected ? 26 : 22}px;height:${selected ? 26 : 22}px;border-radius:50% 50% 50% 0;background:${getPinColor(category)};border:${selected ? 3 : 2}px solid white;box-shadow:0 2px 6px rgba(0,0,0,.35);transform:rotate(-45deg)"></span>`,
    iconSize: selected ? [30, 30] : [26, 26],
    iconAnchor: selected ? [15, 28] : [13, 24],
  });

const CameraSync: React.FC<{
  bounds: LatLngBoundsExpression | null;
  onZoomChange: (zoom: number) => void;
}> = ({ bounds, onZoomChange }) => {
  const map = useMap();

  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [52, 52], animate: false });
  }, [bounds, map]);

  useMapEvents({
    zoomend: () => onZoomChange(map.getZoom()),
  });

  return null;
};

export const MapAdapter: React.FC<MapAdapterProps> = ({
  actors,
  pins,
  geometry,
  bounds,
  selectedActorId,
  onSelectActor,
  height = 360,
}) => {
  const mapRef = useRef<LeafletMap | null>(null);
  const [zoomLevel, setZoomLevel] = useState(12);
  const items = pins ?? actors ?? [];
  const routeCoordinates = useMemo(() => getGeometryCoordinates(geometry), [geometry]);
  const fitCoordinates = useMemo(
    () => getFitCoordinates(bounds, geometry, items),
    [bounds, geometry, items]
  );
  const leafletBounds = useMemo(() => toLeafletBounds(fitCoordinates), [fitCoordinates]);
  const initialRegion = useMemo(() => getInitialRegion(fitCoordinates), [fitCoordinates]);

  const recenter = useCallback(() => {
    if (leafletBounds) {
      mapRef.current?.fitBounds(leafletBounds, { padding: [52, 52], animate: true });
    } else {
      mapRef.current?.setView([initialRegion.latitude, initialRegion.longitude], 12, {
        animate: true,
      });
    }
  }, [initialRegion, leafletBounds]);

  const changeZoom = useCallback((delta: number) => {
    const map = mapRef.current;
    if (!map) return;
    const nextZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, map.getZoom() + delta));
    map.setZoom(nextZoom, { animate: true });
    setZoomLevel(nextZoom);
  }, []);

  return (
    <View
      style={[styles.container, { height }]}
      accessibilityLabel="Mapa interativo da rota, com percurso e pontos selecionáveis"
    >
      <MapContainer
        ref={mapRef}
        center={[initialRegion.latitude, initialRegion.longitude]}
        zoom={12}
        minZoom={MIN_ZOOM}
        maxZoom={MAX_ZOOM}
        zoomControl={false}
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <CameraSync bounds={leafletBounds} onZoomChange={setZoomLevel} />

        {routeCoordinates.length >= 2 && (
          <Polyline
            positions={routeCoordinates.map(({ latitude, longitude }) => [latitude, longitude])}
            pathOptions={{ color: theme.colors.brandForest, weight: 5 }}
          />
        )}

        {items.map((item) => {
          const coordinate = getItemCoordinate(item);
          if (!coordinate) return null;
          const itemId = getItemId(item);
          const category = getItemCategory(item);

          return (
            <Marker
              key={itemId}
              position={[coordinate.latitude, coordinate.longitude]}
              icon={createPinIcon(category, itemId === selectedActorId)}
              title={`Ponto no mapa: ${item.name}`}
              alt={`Ponto no mapa: ${item.name}. Categoria: ${category}`}
              eventHandlers={{ click: () => onSelectActor(itemId) }}
              zIndexOffset={itemId === selectedActorId ? 1000 : 0}
            />
          );
        })}
      </MapContainer>

      <MapControls
        onZoomIn={() => changeZoom(1)}
        onZoomOut={() => changeZoom(-1)}
        onRecenter={recenter}
        canZoomIn={zoomLevel < MAX_ZOOM}
        canZoomOut={zoomLevel > MIN_ZOOM}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: theme.colors.surfaceContainerLow,
  },
});
