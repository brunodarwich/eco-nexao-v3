import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useRouteMapQuery } from '../../hooks/queries';
import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';
import { ErrorStateView, LoadingView } from '../common/UIStateViews';
import { MapAdapter } from '../map/MapAdapter';

interface RouteMapPreviewProps {
  routeId: string;
  originId?: string;
  onExpand: (actorId?: string) => void;
}

export const RouteMapPreview: React.FC<RouteMapPreviewProps> = ({
  routeId,
  originId,
  onExpand,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const mapQuery = useRouteMapQuery(routeId, originId);

  return (
    <View style={styles.section}>
      <View style={styles.headerRow}>
        <Text style={styles.title} accessibilityRole="header">Mapa da Rota</Text>
        <TouchableOpacity
          style={styles.visibilityButton}
          onPress={() => setIsVisible((value) => !value)}
          accessibilityRole="button"
          accessibilityState={{ expanded: isVisible }}
          accessibilityLabel={isVisible ? 'Ocultar mapa da rota' : 'Mostrar mapa da rota'}
        >
          <Ionicons
            name={isVisible ? 'chevron-up' : 'chevron-down'}
            size={16}
            color={theme.colors.brandForest}
          />
          <Text style={styles.visibilityText}>{isVisible ? 'Ocultar mapa' : 'Mostrar mapa'}</Text>
        </TouchableOpacity>
      </View>

      {isVisible && (
        <View style={styles.mapCard}>
          {mapQuery.isPending ? (
            <View style={styles.stateContainer}>
              <LoadingView message="Carregando mapa da rota..." />
            </View>
          ) : mapQuery.isError ? (
            <View style={styles.stateContainer}>
              <ErrorStateView
                message="Não foi possível carregar o mapa desta origem."
                onRetry={() => void mapQuery.refetch()}
              />
            </View>
          ) : mapQuery.data ? (
            <>
              <MapAdapter
                pins={mapQuery.data.pins}
                geometry={mapQuery.data.geometry}
                bounds={mapQuery.data.bounds}
                onSelectActor={(actorId) => onExpand(actorId)}
                height={236}
                showControls={false}
              />
              <TouchableOpacity
                style={styles.expandButton}
                onPress={() => onExpand()}
                {...makeAccessibleButton(
                  'Expandir mapa da rota',
                  'Abre o mapa em tela cheia preservando a origem selecionada.'
                )}
              >
                <Ionicons name="expand-outline" size={18} color={theme.colors.brandDeep} />
                <Text style={styles.expandText}>Expandir mapa</Text>
              </TouchableOpacity>
            </>
          ) : (
            <View style={styles.stateContainer}>
              <Text style={styles.emptyText}>Mapa indisponível para esta origem.</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  section: { gap: 10, width: '100%', maxWidth: '100%' },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  title: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
  },
  visibilityButton: {
    minHeight: 40,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingHorizontal: 8,
    flexShrink: 1,
  },
  visibilityText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '700',
  },
  mapCard: {
    width: '100%',
    maxWidth: '100%',
    minHeight: 236,
    borderRadius: theme.radii.xl,
    overflow: 'hidden',
    backgroundColor: theme.colors.surfaceContainerLow,
    position: 'relative',
    borderWidth: 1,
    borderColor: theme.colors.outlineVariant,
    ...theme.shadows.card,
  },
  stateContainer: {
    minHeight: 236,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  expandButton: {
    position: 'absolute',
    right: 12,
    bottom: 12,
    minHeight: 44,
    paddingHorizontal: 16,
    borderRadius: theme.radii.full,
    backgroundColor: 'rgba(255,255,255,0.96)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
    ...theme.shadows.card,
  },
  expandText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandDeep,
    fontWeight: '700',
  },
  emptyText: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
  },
});
