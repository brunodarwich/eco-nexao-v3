import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Alert, AccessibilityInfo } from 'react-native';
import * as Linking from 'expo-linking';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { makeAccessibleButton, setAccessibilityFocusSafely } from '../../utils/accessibility';
import { AccessibleModal } from '../common/AccessibleModal';
import type { RouteOrigin } from '../../api/types';
import { useCurrentLocation, LocationCoordinates } from '../../hooks/useCurrentLocation';
import { useAppContext } from '../../state/useAppContext';

export const MY_LOCATION_ORIGIN_ID = 'current-location-preview';
export const CHOOSE_ON_MAP_ORIGIN_ID = 'map-selection-preview';

export type SelectorOrigin =
  | RouteOrigin
  | {
      id: string;
      name: string;
      code?: string;
      location_name?: string;
      locationName?: string;
      description?: string;
      actor_count?: number;
      actorCount?: number;
      distance_m?: number;
      duration_s?: number;
    };

interface OriginSelectorProps {
  origins: SelectorOrigin[];
  selectedOriginId?: string;
  onSelectOrigin: (id: string) => void;
  onSelectCurrentLocation?: (coords: LocationCoordinates) => void;
  onStartSelectOnMap?: () => void;
  isLoadingLocation?: boolean;
  enableDynamicRouting?: boolean;
}

export const OriginSelector: React.FC<OriginSelectorProps> = ({
  origins,
  selectedOriginId,
  onSelectOrigin,
  onSelectCurrentLocation,
  onStartSelectOnMap,
  isLoadingLocation: externalLoading,
  enableDynamicRouting,
}) => {
  const { state } = useAppContext();
  const isDynamicRoutingEnabled = enableDynamicRouting ?? Boolean(state?.featureFlags?.dynamicRouting);
  const { status, requestLocation, resetLocation } = useCurrentLocation();
  const [pendingCoords, setPendingCoords] = useState<LocationCoordinates | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  const myLocationButtonRef = useRef<any>(null);
  const modalTitleRef = useRef<any>(null);
  const focusTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isLocating = status === 'requesting' || Boolean(externalLoading);

  const restoreFocus = () => {
    if (focusTimerRef.current) clearTimeout(focusTimerRef.current);
    focusTimerRef.current = setTimeout(() => {
      setAccessibilityFocusSafely(myLocationButtonRef);
    }, 100);
  };

  useEffect(() => {
    if (showConfirmModal) {
      const timer = setTimeout(() => {
        setAccessibilityFocusSafely(modalTitleRef);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [showConfirmModal]);

  useEffect(() => {
    return () => {
      if (focusTimerRef.current) clearTimeout(focusTimerRef.current);
      setShowConfirmModal(false);
      setPendingCoords(null);
    };
  }, []);

  if (!origins || origins.length === 0) return null;

  const isMyLocationSelected = isDynamicRoutingEnabled && selectedOriginId === MY_LOCATION_ORIGIN_ID;
  const isChooseOnMapSelected = isDynamicRoutingEnabled && selectedOriginId === CHOOSE_ON_MAP_ORIGIN_ID;
  const fallbackOrigin = origins[0];
  const activeOriginId = selectedOriginId ?? fallbackOrigin.id;
  const selectedOrigin = isMyLocationSelected
    ? {
        id: MY_LOCATION_ORIGIN_ID,
        name: 'Minha localização',
        description: 'Ponto de partida aproximado obtido via GPS (efêmero)',
      }
    : isChooseOnMapSelected
    ? {
        id: CHOOSE_ON_MAP_ORIGIN_ID,
        name: 'Ponto escolhido no mapa',
        description: 'Ponto de partida selecionado manualmente no mapa interativo',
      }
    : origins.find((o) => o.id === activeOriginId) || fallbackOrigin;

  const handlePressMyLocation = async () => {
    if (!isDynamicRoutingEnabled) return;
    try {
      AccessibilityInfo.announceForAccessibility('Obtendo sua localização atual via GPS...');
      const result = await requestLocation();
      if (result.success && result.coords) {
        setPendingCoords(result.coords);
        setShowConfirmModal(true);
        AccessibilityInfo.announceForAccessibility('Localização obtida com sucesso. Confirme o cálculo do trajeto sugerido.');
      } else {
        // Fallback to default origin only if current selection was already GPS
        if (selectedOriginId === MY_LOCATION_ORIGIN_ID) {
          onSelectOrigin(fallbackOrigin.id);
        }

        if (result.status === 'permanently_denied') {
          const msg = result.errorMessage || 'Permissão de localização bloqueada. Por favor, habilite nas configurações do aparelho.';
          AccessibilityInfo.announceForAccessibility(msg);
          Alert.alert(
            'Permissão Necessária',
            'O acesso à localização está desativado nas configurações do aplicativo. Deseja abrir as configurações?',
            [
              { text: 'Agora não', style: 'cancel' },
              { text: 'Abrir Configurações', onPress: () => void Linking.openSettings() },
            ]
          );
        } else {
          const msg = result.errorMessage || 'Não foi possível obter sua localização atual.';
          AccessibilityInfo.announceForAccessibility(msg);
          Alert.alert('Aviso de Localização', msg, [
            { text: 'OK', onPress: () => {} },
          ]);
        }
      }
    } catch {
      if (selectedOriginId === MY_LOCATION_ORIGIN_ID) {
        onSelectOrigin(fallbackOrigin.id);
      }
      AccessibilityInfo.announceForAccessibility('Ocorreu um erro ao acessar a localização.');
      Alert.alert('Erro', 'Ocorreu um erro ao acessar a localização.');
    }
  };

  const handleConfirmLocation = () => {
    setShowConfirmModal(false);
    const coordsToPass = pendingCoords;
    setPendingCoords(null);
    if (coordsToPass) {
      if (onSelectCurrentLocation) {
        onSelectCurrentLocation(coordsToPass);
      }
      onSelectOrigin(MY_LOCATION_ORIGIN_ID);
    }
    restoreFocus();
  };

  const handleCancelLocation = () => {
    setShowConfirmModal(false);
    setPendingCoords(null);
    resetLocation();
    // Keep current selected origin or fallback
    if (selectedOriginId === MY_LOCATION_ORIGIN_ID) {
      onSelectOrigin(fallbackOrigin.id);
    }
    AccessibilityInfo.announceForAccessibility('Cálculo a partir da localização cancelado.');
    restoreFocus();
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Ionicons name="navigate-outline" size={16} color={theme.colors.brandForest} />
        <Text style={styles.headerTitle}>saindo de onde?</Text>
      </View>

      {/* Compact Segmented Pills Row */}
      <View style={styles.segmentedRow}>
        {/* Minha Localização Pill */}
        {isDynamicRoutingEnabled && (
          <TouchableOpacity
            ref={myLocationButtonRef}
            key="my-location"
            style={[
              styles.pillButton,
              isMyLocationSelected ? styles.pillSelected : styles.pillUnselected,
              isLocating && styles.pillDisabled,
            ]}
            onPress={handlePressMyLocation}
            disabled={isLocating}
            {...makeAccessibleButton(
              'Usar minha localização atual como origem',
              'Obtém as coordenadas GPS do dispositivo para sugerir trajeto dinâmico',
              isLocating
            )}
            accessibilityRole="button"
            accessibilityState={{ selected: isMyLocationSelected, busy: isLocating }}
          >
            {isLocating ? (
              <ActivityIndicator
                size="small"
                color={isMyLocationSelected ? theme.colors.onPrimary : theme.colors.brandForest}
              />
            ) : (
              <Ionicons
                name="location"
                size={16}
                color={isMyLocationSelected ? theme.colors.onPrimary : theme.colors.brandForest}
              />
            )}
            <Text
              style={[
                styles.pillText,
                isMyLocationSelected ? styles.pillTextSelected : styles.pillTextUnselected,
              ]}
              numberOfLines={1}
            >
              {isLocating ? 'Obtendo GPS...' : 'Minha localização'}
            </Text>
          </TouchableOpacity>
        )}

        {/* Escolher no Mapa Pill */}
        {isDynamicRoutingEnabled && onStartSelectOnMap && (
          <TouchableOpacity
            key="choose-on-map"
            style={[
              styles.pillButton,
              isChooseOnMapSelected ? styles.pillSelected : styles.pillUnselected,
              isLocating && styles.pillDisabled,
            ]}
            onPress={() => {
              if (isDynamicRoutingEnabled && onStartSelectOnMap) {
                onStartSelectOnMap();
              }
            }}
            disabled={isLocating}
            {...makeAccessibleButton(
              'Escolher ponto de partida no mapa',
              'Abre o mapa para selecionar ou arrastar o ponto de partida do trajeto'
            )}
            accessibilityRole="button"
            accessibilityState={{ selected: isChooseOnMapSelected }}
          >
            <Ionicons
              name="map-outline"
              size={16}
              color={isChooseOnMapSelected ? theme.colors.onPrimary : theme.colors.brandForest}
            />
            <Text
              style={[
                styles.pillText,
                isChooseOnMapSelected ? styles.pillTextSelected : styles.pillTextUnselected,
              ]}
              numberOfLines={1}
            >
              Escolher no mapa
            </Text>
          </TouchableOpacity>
        )}

        {origins.map((origin) => {
          const isSelected = !isMyLocationSelected && !isChooseOnMapSelected && origin.id === activeOriginId;
          const originCode = ('code' in origin && origin.code ? origin.code : origin.id || '').toLowerCase();
          const originName = (origin.name || '').toLowerCase();

          let iconName: keyof typeof Ionicons.glyphMap = 'boat-outline';
          let shortName = origin.name || '';

          if (originCode.includes('rodoviaria') || originName.includes('rodoviária') || originName.includes('rodoviaria')) {
            iconName = 'bus-outline';
            shortName = 'Rodoviária';
          } else if (originCode.includes('aeroporto') || originName.includes('aeroporto')) {
            iconName = 'airplane-outline';
            shortName = 'Aeroporto';
          } else if (originCode.includes('porto') || originName.includes('porto')) {
            iconName = 'boat-outline';
            shortName = 'Porto';
          }

          return (
            <TouchableOpacity
              key={origin.id}
              style={[
                styles.pillButton,
                isSelected ? styles.pillSelected : styles.pillUnselected,
                isLocating && styles.pillDisabled,
              ]}
              onPress={() => onSelectOrigin(origin.id)}
              disabled={isLocating}
              {...makeAccessibleButton(`Selecionar origem ${origin.name}`)}
              accessibilityRole="button"
              accessibilityState={{ selected: isSelected }}
            >
              <Ionicons
                name={iconName}
                size={16}
                color={isSelected ? theme.colors.onPrimary : theme.colors.brandForest}
              />
              <Text
                style={[
                  styles.pillText,
                  isSelected ? styles.pillTextSelected : styles.pillTextUnselected,
                ]}
                numberOfLines={1}
              >
                {shortName}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Selected Origin Active Detail Line */}
      {selectedOrigin && (
        <View style={styles.activeDetailCard} accessibilityLiveRegion="polite">
          <Text style={styles.activeName}>{selectedOrigin.name}</Text>
          {Boolean(selectedOrigin.description) && (
            <Text style={styles.activeDesc} numberOfLines={2}>
              {selectedOrigin.description}
            </Text>
          )}
          {'distance_m' in selectedOrigin && typeof selectedOrigin.distance_m === 'number' && (
            <Text style={styles.distanceText}>
              Distância total: {(selectedOrigin.distance_m / 1000).toFixed(1)} km
              {'duration_s' in selectedOrigin && typeof selectedOrigin.duration_s === 'number'
                ? ` • Tempo estimado: ~${Math.round(selectedOrigin.duration_s / 60)} min`
                : ''}
            </Text>
          )}
        </View>
      )}

      {/* Confirmation Modal with Full Accessibility */}
      <AccessibleModal
        visible={showConfirmModal}
        transparent
        animationType="fade"
        onClose={handleCancelLocation}
        initialFocusRef={modalTitleRef}
        returnFocusRef={myLocationButtonRef}
        accessibilityLabel="Confirmar cálculo de trajeto"
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer} accessibilityRole="alert">
            <View style={styles.modalHeader}>
              <Ionicons name="location" size={24} color={theme.colors.brandForest} />
              <Text ref={modalTitleRef} style={styles.modalTitle} accessibilityRole="header">
                Confirmar Trajeto
              </Text>
            </View>
            <Text style={styles.modalMessage}>
              Localização aproximada obtida. Deseja calcular o trajeto sugerido a partir deste ponto?
            </Text>
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalCancelButton]}
                onPress={handleCancelLocation}
                {...makeAccessibleButton('Cancelar cálculo a partir da minha localização')}
              >
                <Text style={styles.modalCancelText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalConfirmButton]}
                onPress={handleConfirmLocation}
                {...makeAccessibleButton('Confirmar cálculo do trajeto sugerido')}
              >
                <Text style={styles.modalConfirmText}>Calcular</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </AccessibleModal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surfaceWhite,
    padding: 14,
    borderRadius: theme.radii.lg,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
    marginVertical: theme.spacing.stackSm,
    ...theme.shadows.sm,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 10,
  },
  headerTitle: {
    ...theme.typography.labelMd,
    color: theme.colors.brandDeep,
    fontWeight: '700',
    fontSize: 14,
  },
  segmentedRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 10,
  },
  pillButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 7,
    paddingHorizontal: 14,
    borderRadius: theme.radii.full,
    gap: 6,
    borderWidth: 1,
  },
  pillDisabled: {
    opacity: 0.7,
  },
  pillSelected: {
    backgroundColor: theme.colors.brandForest,
    borderColor: theme.colors.brandForest,
  },
  pillUnselected: {
    backgroundColor: theme.colors.surfaceContainerLow,
    borderColor: 'rgba(117, 155, 113, 0.15)',
  },
  pillText: {
    ...theme.typography.labelSm,
    fontSize: 12,
  },
  pillTextSelected: {
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
  pillTextUnselected: {
    color: theme.colors.brandDeep,
    fontWeight: '600',
  },
  activeDetailCard: {
    backgroundColor: 'rgba(51, 96, 30, 0.04)',
    paddingVertical: 9,
    paddingHorizontal: 12,
    borderRadius: theme.radii.md,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.brandForest,
    gap: 2,
  },
  activeName: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '700',
    fontSize: 12,
  },
  activeDesc: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 11,
    lineHeight: 15,
  },
  distanceText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandDeep,
    fontSize: 11,
    fontWeight: '600',
    marginTop: 2,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContainer: {
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.xl,
    padding: 20,
    width: '100%',
    maxWidth: 380,
    ...theme.shadows.card,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  modalTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    fontWeight: '700',
  },
  modalMessage: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurfaceVariant,
    lineHeight: 20,
    marginBottom: 20,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  modalButton: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: theme.radii.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalCancelButton: {
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  modalCancelText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandDeep,
    fontWeight: '600',
  },
  modalConfirmButton: {
    backgroundColor: theme.colors.brandForest,
  },
  modalConfirmText: {
    ...theme.typography.labelMd,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
});
