import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import L, { type LatLngBoundsExpression, type Map as LeafletMap } from 'leaflet';
import { MapContainer, Marker, Polyline, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

import { theme } from '../../theme/theme';
import { MapControls } from './MapControls';
import {
  SELECTION_PIN_COLOR,
  formatCoordinateDisplay,
  getFitCoordinates,
  getGeometryCoordinates,
  getInitialRegion,
  getItemAccessibilityLabel,
  getItemCategoryLabel,
  getItemCoordinate,
  getItemId,
  getItemPinColor,
  getItemPinIcon,
  getSelectionPinAccessibilityLabel,
} from './MapAdapter.helpers';
import type { FlexiblePinItem, MapAdapterProps, MapCoordinate } from './MapAdapter.types';

const MIN_ZOOM = 3;
const MAX_ZOOM = 19;

const toLeafletBounds = (coordinates: MapCoordinate[]): LatLngBoundsExpression | null =>
  coordinates.length
    ? coordinates.map(({ latitude, longitude }) => [latitude, longitude] as [number, number])
    : null;

const getPinIconSvg = (iconName: string): string | null => {
  switch (iconName) {
    case 'flag':
      return '<path d="M5 22V4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M5 4h11l-2 4 2 4H5" stroke="currentColor" stroke-width="2" stroke-linejoin="round" fill="none"/>';
    case 'flag':
    case 'pin':
    case 'selection-pin':
      // Flag / Pin marker icon
      return '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/><line x1="4" y1="22" x2="4" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>';
    case 'utensils':
    case 'restaurant':
      // Cutlery / knife & fork
      return '<path d="M18 2v6a3 3 0 0 1-3 3 3 3 0 0 1-3-3V2M15 2v20M5 2v7a3 3 0 0 0 3 3v10M8 2v4M2 2v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>';
    case 'compass':
      // Compass
      return '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor"/>';
    case 'bed':
      // Bed
      return '<path d="M2 4v16M2 8h18a2 2 0 0 1 2 2v10M2 17h20M6 8v9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>';
    case 'palette':
      // Palette
      return '<circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.563-2.512 5.563-5.563C22 6.5 17.5 2 12 2z" stroke="currentColor" stroke-width="2" fill="none"/>';
    case 'bus':
      // Bus
      return '<rect x="3" y="3" width="18" height="15" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><path d="M3 9h18M3 14h18M6 18v2M18 18v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>';
    case 'heart-pulse':
    case 'cross':
    case 'medkit':
      // Heart with pulse / health
      return '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M3.22 12H9.5l1.5-3 2 6 1.5-3h4.28" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
    case 'shield':
      // Shield
      return '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>';
    case 'help-circle':
      // Help circle / question
      return '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>';
    default:
      return null;
  }
};

const createPinIcon = (item: FlexiblePinItem, selected: boolean) => {
  const color = getItemPinColor(item);
  const icon = getItemPinIcon(item);
  if (!color || !icon) return null;
  const size = selected ? 50 : 44;
  const iconSize = selected ? 22 : 18;
  const svgContent = getPinIconSvg(icon);
  if (!svgContent) return null;
  const ringStyle = selected
    ? 'box-shadow:0 0 0 3px #FFFFFF, 0 0 0 6px rgba(17,24,39,0.85), 0 4px 12px rgba(0,0,0,0.5); transform:scale(1.15);'
    : 'box-shadow:0 2px 6px rgba(0,0,0,0.35);';

  const html = `
    <div style="display:flex;align-items:center;justify-content:center;width:${size}px;height:${size}px;border-radius:50%;background:${color};border:2.5px solid #FFFFFF;color:#FFFFFF;transition:transform 0.15s ease,box-shadow 0.15s ease;${ringStyle}" aria-hidden="true">
      <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" fill="none" style="display:block;">
        ${svgContent}
      </svg>
    </div>
  `;

  return L.divIcon({
    className: 'econexao-map-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

const createSelectionPinIcon = () => {
  const size = 42;
  const iconSize = 20;
  const color = SELECTION_PIN_COLOR;
  const svgContent = getPinIconSvg('flag');
  const ringStyle =
    'box-shadow:0 0 0 3px #FFFFFF, 0 0 0 6px rgba(234,88,12,0.8), 0 6px 16px rgba(0,0,0,0.45); transform:scale(1.1); animation:pulse 2s infinite;';

  const html = `
    <div style="display:flex;align-items:center;justify-content:center;width:${size}px;height:${size}px;border-radius:50%;background:${color};border:3px solid #FFFFFF;color:#FFFFFF;transition:transform 0.15s ease,box-shadow 0.15s ease;cursor:grab;${ringStyle}" aria-label="Marcador de seleção">
      <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" fill="none" style="display:block;">
        ${svgContent}
      </svg>
    </div>
  `;

  return L.divIcon({
    className: 'econexao-selection-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

const MapEventsHandler: React.FC<{
  selectionMode?: boolean;
  onSelectCoordinate?: (coord: MapCoordinate) => void;
  onZoomChange: (zoom: number) => void;
}> = ({ selectionMode, onSelectCoordinate, onZoomChange }) => {
  const map = useMap();

  useMapEvents({
    click: (e) => {
      if (selectionMode && onSelectCoordinate) {
        onSelectCoordinate({ latitude: e.latlng.lat, longitude: e.latlng.lng });
      }
    },
    zoomend: () => onZoomChange(map.getZoom()),
  });

  return null;
};

const CameraSync: React.FC<{
  bounds: LatLngBoundsExpression | null;
}> = ({ bounds }) => {
  const map = useMap();

  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [52, 52], animate: true });
  }, [bounds, map]);

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
  showControls = true,
  selectionMode = false,
  selectedCoordinate,
  onSelectCoordinate,
  selectionPinLabel,
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

  const selectionPinA11y = useMemo(
    () => getSelectionPinAccessibilityLabel(selectedCoordinate, selectionPinLabel),
    [selectedCoordinate, selectionPinLabel]
  );

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
        <CameraSync bounds={leafletBounds} />
        <MapEventsHandler
          selectionMode={selectionMode}
          onSelectCoordinate={onSelectCoordinate}
          onZoomChange={setZoomLevel}
        />

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
          const isSelected = itemId === selectedActorId;
          const a11yLabel = getItemAccessibilityLabel(item, isSelected);
          const pinIcon = createPinIcon(item, isSelected);
          if (!pinIcon) return null;

          return (
            <Marker
              key={itemId}
              position={[coordinate.latitude, coordinate.longitude]}
              icon={pinIcon}
              title={a11yLabel}
              alt={a11yLabel}
              eventHandlers={{
                click: (e) => {
                  L.DomEvent.stopPropagation(e as any);
                  onSelectActor(itemId);
                },
              }}
              zIndexOffset={isSelected ? 1000 : 0}
            />
          );
        })}

        {selectedCoordinate && (
          <Marker
            position={[selectedCoordinate.latitude, selectedCoordinate.longitude]}
            icon={createSelectionPinIcon()}
            title={selectionPinA11y}
            alt={selectionPinA11y}
            draggable={true}
            zIndexOffset={2000}
            eventHandlers={{
              click: (e) => {
                L.DomEvent.stopPropagation(e as any);
              },
              dragend: (e) => {
                const marker = e.target;
                const latlng = marker.getLatLng();
                if (onSelectCoordinate) {
                  onSelectCoordinate({ latitude: latlng.lat, longitude: latlng.lng });
                }
              },
            }}
          />
        )}
      </MapContainer>

      {showControls && (
        <MapControls
          onZoomIn={() => changeZoom(1)}
          onZoomOut={() => changeZoom(-1)}
          onRecenter={recenter}
          canZoomIn={zoomLevel < MAX_ZOOM}
          canZoomOut={zoomLevel > MIN_ZOOM}
        />
      )}
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
