import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import MapView, { Marker, Polyline, type LatLng, type Region } from 'react-native-maps';

import { theme } from '../../theme/theme';
import { MapControls } from './MapControls';
import {
  SELECTION_PIN_COLOR,
  clusterPins,
  getClusterAccessibilityLabel,
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
  isClusterItem,
} from './MapAdapter.helpers';
import type { MapAdapterProps, MapClusterItem } from './MapAdapter.types';
import { getCategoryIonicons } from '../catalog/CategoryFilters';

const MIN_ZOOM = 3;
const MAX_ZOOM = 20;
const EDGE_PADDING = { top: 52, right: 52, bottom: 52, left: 52 };

const regionToZoom = (region: Region): number =>
  Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.log2(360 / region.longitudeDelta)));

export const MapAdapter: React.FC<MapAdapterProps> = ({
  actors,
  pins,
  geometry,
  bounds,
  selectedActorId,
  onSelectActor,
  onSelectCluster,
  height = 360,
  showControls = true,
  selectionMode = false,
  selectedCoordinate,
  onSelectCoordinate,
  selectionPinLabel,
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

  // Deterministic clustering and coincident offsets based on current zoomLevel
  const renderableItems = useMemo(
    () => clusterPins(items, zoomLevel, selectedActorId),
    [items, zoomLevel, selectedActorId]
  );

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

  const handleClusterPress = useCallback(
    (cluster: MapClusterItem) => {
      onSelectCluster?.(cluster);
      const coords: LatLng[] = [
        { latitude: cluster.bounds.min_lat, longitude: cluster.bounds.min_lng },
        { latitude: cluster.bounds.max_lat, longitude: cluster.bounds.max_lng },
      ];
      mapRef.current?.fitToCoordinates(coords, {
        edgePadding: EDGE_PADDING,
        animated: true,
      });
    },
    [onSelectCluster]
  );

  const selectionPinA11y = useMemo(
    () => getSelectionPinAccessibilityLabel(selectedCoordinate, selectionPinLabel),
    [selectedCoordinate, selectionPinLabel]
  );

  return (
    <View style={[styles.container, { height }]}>
      <MapView
        ref={mapRef}
        style={StyleSheet.absoluteFill}
        initialRegion={initialRegion}
        onMapReady={recenter}
        onRegionChangeComplete={(region) => setZoomLevel(regionToZoom(region))}
        onPress={(e) => {
          if (selectionMode && onSelectCoordinate) {
            onSelectCoordinate(e.nativeEvent.coordinate);
          }
        }}
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

        {renderableItems.map((item) => {
          if (isClusterItem(item)) {
            const a11yLabel = getClusterAccessibilityLabel(item);
            return (
              <Marker
                key={item.id}
                coordinate={{ latitude: item.latitude, longitude: item.longitude }}
                title={`Grupo (${item.count} locais)`}
                description={a11yLabel}
                zIndex={500}
                onPress={() => handleClusterPress(item)}
                accessibilityRole="button"
                accessibilityLabel={a11yLabel}
                accessibilityHint="Toque para aproximar e visualizar cada ponto."
              >
                <View
                  style={[
                    styles.clusterPin,
                    { backgroundColor: item.primaryColor || theme.colors.brandForest },
                  ]}
                >
                  <Text style={styles.clusterCountText}>{item.count}</Text>
                </View>
              </Marker>
            );
          }

          const coordinate =
            ('offsetCoordinate' in item && item.offsetCoordinate)
              ? item.offsetCoordinate
              : getItemCoordinate(item);
          if (!coordinate) return null;
          const itemId = getItemId(item);
          const selected = itemId === selectedActorId;
          const categoryLabel = getItemCategoryLabel(item);
          const color = getItemPinColor(item);
          const icon = getCategoryIonicons(getItemPinIcon(item));
          const a11yLabel = getItemAccessibilityLabel(item, selected);
          if (!color || !icon) return null;

          return (
            <Marker
              key={itemId}
              coordinate={coordinate}
              title={item.name}
              description={`Categoria: ${categoryLabel}`}
              zIndex={selected ? 1000 : 1}
              onPress={() => onSelectActor(itemId)}
              accessibilityRole="button"
              accessibilityLabel={a11yLabel}
              accessibilityHint={`Categoria: ${categoryLabel}. Toque para selecionar.`}
              accessibilityState={{ selected }}
            >
              <View
                style={[
                  styles.contractPin,
                  { backgroundColor: color },
                  selected && styles.contractPinSelected,
                ]}
              >
                <Ionicons name={icon} size={selected ? 22 : 19} color="#FFFFFF" />
              </View>
            </Marker>
          );
        })}

        {selectedCoordinate && (
          <Marker
            coordinate={selectedCoordinate}
            title={selectionPinLabel || 'Ponto de Partida Escolhido'}
            description={selectionPinA11y}
            pinColor={SELECTION_PIN_COLOR}
            draggable
            zIndex={2000}
            onDragEnd={(e) => {
              if (onSelectCoordinate) {
                onSelectCoordinate(e.nativeEvent.coordinate);
              }
            }}
            accessibilityRole="button"
            accessibilityLabel={selectionPinA11y}
            accessibilityHint="Ponto de partida selecionado no mapa. Arraste para reposicionar."
          />
        )}
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
  contractPin: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  contractPinSelected: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 4,
    borderColor: '#111827',
  },
  clusterPin: {
    minWidth: 46,
    height: 46,
    paddingHorizontal: 8,
    borderRadius: 23,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: '#FFFFFF',
    ...theme.shadows.card,
  },
  clusterCountText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  container: {
    width: '100%',
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: theme.colors.surfaceContainerLow,
  },
});
