import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';
import type { RouteOrigin } from '../../api/types';

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
    };

interface OriginSelectorProps {
  origins: SelectorOrigin[];
  selectedOriginId?: string;
  onSelectOrigin: (id: string) => void;
}

export const OriginSelector: React.FC<OriginSelectorProps> = ({
  origins,
  selectedOriginId,
  onSelectOrigin,
}) => {
  if (!origins || origins.length === 0) return null;

  const activeOriginId = selectedOriginId ?? origins[0].id;
  const selectedOrigin = origins.find((o) => o.id === activeOriginId) || origins[0];

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Ionicons name="navigate-outline" size={16} color={theme.colors.brandForest} />
        <Text style={styles.headerTitle}>Simulador de Origem da Rota</Text>
      </View>

      {/* Compact Segmented Pills Row */}
      <View style={styles.segmentedRow}>
        {origins.map((origin) => {
          const isSelected = origin.id === activeOriginId;
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
              ]}
              onPress={() => onSelectOrigin(origin.id)}
              {...makeAccessibleButton(`Selecionar origem ${origin.name}`)}
              accessibilityState={{ selected: isSelected }}
            >
              <Ionicons
                name={iconName}
                size={18}
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
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surfaceWhite,
    padding: 12,
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
    gap: 6,
    marginBottom: 8,
  },
  pillButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 6,
    borderRadius: theme.radii.full,
    gap: 5,
    borderWidth: 1,
  },
  pillSelected: {
    backgroundColor: theme.colors.brandForest,
    borderColor: theme.colors.brandForest,
  },
  pillUnselected: {
    backgroundColor: theme.colors.surfaceContainerLow,
    borderColor: 'transparent',
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
    paddingVertical: 8,
    paddingHorizontal: 10,
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
});
