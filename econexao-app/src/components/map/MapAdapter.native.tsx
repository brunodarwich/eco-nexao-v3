import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import MapView, { Marker, Polyline, type LatLng, type Region } from 'react-native-maps';

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
import type { MapAdapterProps } from './MapAdapter.types';

const MIN_ZOOM = 3;
const MAX_ZOOM = 20;
const EDGE_PADDING = { top: 52, right: 52, bottom: 52, left: 52 };

const getPinColor = (category: string): string => {
  if (category === 'alimentacao' || category === 'gastronomia') return theme.colors.brandSun;
  if (category === 'emergencia' || category === 'saude') return theme.colors.error;
  if (category === 'artesanato' || category === 'comercio') return theme.colors.brandLeaf;
  return theme.colors.brandForest;
};

const regionToZoom = (region: Region): number =>
  Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.log2(360 / region.longitudeDelta)));

export const MapAdapter: React.FC<MapAdapterProps> = ({
  actors,
  pins,
  geometry,
  bounds,
  selectedActorId,
  onSelectActor,
  height = 360,
  showControls = true,
}) => {
  const mapRef = useRef<MapView>(null);
  const [zoomLevel, setZoomLevel] = useState(12);
  const items = pins ?? actors ?? [];
  const routeCoordinates = useMemo(() => getGeometryCoordinates(geometry), [geometry]);
  const fitCoordinates = useMemo(
    () => getFitCoordinates(bounds, geometry, items),
    [bounds, geometry, items]
  );
  const initialRegion = useMemo(() => getInitialRegion(fitCoordinates), [fitCoordinates]);

  const recenter = useCallback(() => {
    if (fitCoordinates.length >= 2) {
      mapRef.current?.fitToCoordinates(fitCoordinates as LatLng[], {
        edgePadding: EDGE_PADDING,
        animated: true,
      });
      return;
    }

    mapRef.current?.animateToRegion(initialRegion, 300);
  }, [fitCoordinates, initialRegion]);

  useEffect(() => {
    recenter();
  }, [recenter]);

  const changeZoom = useCallback(async (delta: number) => {
    const nextZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoomLevel + delta));
    const camera = await mapRef.current?.getCamera();
    if (!camera) return;
    mapRef.current?.animateCamera({ ...camera, zoom: nextZoom }, { duration: 250 });
    setZoomLevel(nextZoom);
  }, [zoomLevel]);

  return (
    <View style={[styles.container, { height }]}>
      <MapView
        ref={mapRef}
        style={StyleSheet.absoluteFill}
        initialRegion={initialRegion}
        onMapReady={recenter}
        onRegionChangeComplete={(region) => setZoomLevel(regionToZoom(region))}
        minZoomLevel={MIN_ZOOM}
        maxZoomLevel={MAX_ZOOM}
        accessibilityLabel="Mapa interativo da rota, com percurso e pontos selecionáveis"
        accessibilityHint="Use os controles de zoom e recentralização ou selecione um ponto da rota"
      >
        {routeCoordinates.length >= 2 && (
          <Polyline
            coordinates={routeCoordinates as LatLng[]}
            strokeColor={theme.colors.brandForest}
            strokeWidth={5}
          />
        )}

        {items.map((item) => {
          const coordinate = getItemCoordinate(item);
          if (!coordinate) return null;
          const itemId = getItemId(item);
          const category = getItemCategory(item);
          const selected = itemId === selectedActorId;

          return (
            <Marker
              key={itemId}
              coordinate={coordinate}
              title={item.name}
              description={`Categoria: ${category}`}
              pinColor={getPinColor(category)}
              opacity={selected ? 1 : 0.88}
              zIndex={selected ? 2 : 1}
              onPress={() => onSelectActor(itemId)}
              accessibilityRole="button"
              accessibilityLabel={`Ponto no mapa: ${item.name}`}
              accessibilityHint={`Categoria: ${category}. Toque para selecionar.`}
            />
          );
        })}
      </MapView>

      {showControls && (
        <MapControls
          onZoomIn={() => void changeZoom(1)}
          onZoomOut={() => void changeZoom(-1)}
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
