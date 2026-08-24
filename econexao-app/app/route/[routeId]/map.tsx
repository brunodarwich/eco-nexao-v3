import React, { useEffect, useRef, useState } from 'react';
import { Modal, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { CategoryFilters } from '../../../src/components/catalog/CategoryFilters';
import { MapAdapter } from '../../../src/components/map/MapAdapter';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { useActorCategoriesQuery, useRouteActorsQuery, useRouteMapQuery } from '../../../src/hooks/queries';
import { theme } from '../../../src/theme/theme';
import { makeAccessibleButton, setAccessibilityFocusSafely } from '../../../src/utils/accessibility';
import type { MapPin } from '../../../src/api/types';

export default function MapScreen() {
  const router = useRouter();
  const { routeId = '', originId, actorId: initialActorId } = useLocalSearchParams<{
    routeId: string;
    originId?: string;
    actorId?: string;
  }>();

  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedActorId, setSelectedActorId] = useState<string | undefined>(initialActorId);
  const mapRegionRef = useRef<React.ElementRef<typeof View>>(null);
  const closeSheetButtonRef = useRef<React.ElementRef<typeof TouchableOpacity>>(null);
  const actorSheetWasOpenRef = useRef(false);

  const moveAccessibilityFocus = (target: any) => {
    setAccessibilityFocusSafely(target);
  };

  const closeActorSheet = () => {
    setSelectedActorId(undefined);
  };

  const mapQuery = useRouteMapQuery(routeId, originId);
  const categoriesQuery = useActorCategoriesQuery();
  const actorsQuery = useRouteActorsQuery(routeId, {
    origin_id: originId,
    category: selectedCategory || undefined,
  });

  // Sync initial actorId if passed via route params
  useEffect(() => {
    if (initialActorId) {
      setSelectedActorId(initialActorId);
    }
  }, [initialActorId]);

  useEffect(() => {
    if (selectedActorId) {
      actorSheetWasOpenRef.current = true;
      return;
    }

    if (actorSheetWasOpenRef.current) {
      actorSheetWasOpenRef.current = false;
      moveAccessibilityFocus(mapRegionRef);
    }
  }, [selectedActorId]);

  if (mapQuery.isPending) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Mapa da Rota" />
        <LoadingView message="Carregando mapa da rota..." />
      </View>
    );
  }

  if (mapQuery.isError) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Mapa da Rota" />
        <ErrorStateView
          title="Erro ao carregar mapa"
          message="Não foi possível carregar os dados geoespaciais do mapa."
          onRetry={() => void mapQuery.refetch()}
        />
      </View>
    );
  }

  if (!mapQuery.data) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Mapa da Rota" />
        <EmptyStateView
          title="Mapa não disponível"
          message="Não há dados de mapa disponíveis para esta origem."
          onReset={() => router.back()}
          resetLabel="Voltar"
        />
      </View>
    );
  }

  const mapPayload = mapQuery.data;
  const allPins = mapPayload.pins || [];

  // Filter pins according to selectedCategory, keeping the selectedActorId pin visible
  const filteredPins = allPins.filter((pin) => {
    if (!selectedCategory) return true;
    if (pin.actor_id === selectedActorId || pin.id === selectedActorId) return true;
    return pin.category_slug === selectedCategory;
  });

  // Find details of selected pin or actor
  const selectedPin: MapPin | undefined = allPins.find(
    (p) => p.actor_id === selectedActorId || p.id === selectedActorId
  );
  const selectedActorSummary = actorsQuery.data?.data.find(
    (a) => a.id === selectedActorId
  );

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title="Mapa da Rota" />

      {/* Category Filter Chips Bar */}
      <View style={styles.filterBar}>
        <CategoryFilters
          categories={categoriesQuery.data ?? []}
          selectedCategory={selectedCategory}
          onSelectCategory={(catSlug) => {
            setSelectedCategory(catSlug);
          }}
        />
      </View>

      {/* Interactive Map Area */}
      <View
        ref={mapRegionRef}
        style={styles.mapWrapper}
        accessible
        accessibilityRole="summary"
        accessibilityLabel="Mapa interativo da rota"
      >
        <MapAdapter
          pins={filteredPins}
          geometry={mapPayload.geometry}
          bounds={mapPayload.bounds}
          selectedActorId={selectedActorId}
          onSelectActor={(id) => setSelectedActorId(id)}
          height="100%"
        />
      </View>

      {/* Accessible actor preview sheet. The backdrop is a sibling so its press
          cannot propagate through the sheet to map controls or pins. */}
      <Modal
        visible={Boolean(selectedActorId) && Boolean(selectedPin || selectedActorSummary)}
        transparent
        animationType="slide"
        onRequestClose={closeActorSheet}
        onShow={() => moveAccessibilityFocus(closeSheetButtonRef)}
        accessibilityViewIsModal
        aria-modal
      >
        <View style={styles.sheetModalRoot}>
          <TouchableOpacity
            style={styles.sheetBackdrop}
            activeOpacity={1}
            onPress={closeActorSheet}
            {...makeAccessibleButton('Fechar preview do ator pelo fundo')}
          />

          <View style={styles.bottomSheetCard} accessibilityRole="summary">
            <View style={styles.sheetHandle} />
            <View style={styles.sheetHeader}>
              <View style={styles.sheetTagWrapper}>
                <Text style={styles.sheetCategoryTag}>
                  {(selectedPin?.category_slug || selectedActorSummary?.category_label || 'Ponto da Rota').toUpperCase()}
                </Text>
              </View>
              <TouchableOpacity
                ref={closeSheetButtonRef}
                style={styles.closeButton}
                onPress={closeActorSheet}
                {...makeAccessibleButton(
                  'Fechar preview do ator',
                  'Fecha o preview e retorna o foco ao mapa'
                )}
              >
                <Ionicons name="close" size={20} color={theme.colors.onSurfaceVariant} />
              </TouchableOpacity>
            </View>

            <Text style={styles.sheetTitle} accessibilityRole="header">
              {selectedPin?.name || selectedActorSummary?.name}
            </Text>

            {Boolean(selectedActorSummary?.address) && (
              <Text style={styles.sheetSub} numberOfLines={1}>
                <Ionicons name="location-outline" size={13} color={theme.colors.brandForest} /> {selectedActorSummary?.address}
              </Text>
            )}

            {typeof selectedPin?.distance_from_origin_m === 'number' && (
              <Text style={styles.sheetDistance}>
                Distância da origem: {(selectedPin.distance_from_origin_m / 1000).toFixed(1)} km
              </Text>
            )}

            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => {
                const targetActorId = selectedPin?.actor_id || selectedPin?.id || selectedActorSummary?.id;
                if (targetActorId) {
                  router.push(
                    `/route/${encodeURIComponent(routeId)}/catalog?originId=${encodeURIComponent(originId ?? '')}&actorId=${encodeURIComponent(targetActorId)}`
                  );
                }
              }}
              {...makeAccessibleButton(
                `Ver ${selectedPin?.name || selectedActorSummary?.name} no catálogo`,
                'Abre o catálogo mantendo a origem e o ator selecionados'
              )}
            >
              <Text style={styles.actionButtonText}>Ver no catálogo</Text>
              <Ionicons name="chevron-forward" size={16} color={theme.colors.onPrimary} />
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.surfaceBackground,
  },
  filterBar: {
    backgroundColor: theme.colors.surfaceWhite,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(117, 155, 113, 0.15)',
    zIndex: 10,
  },
  mapWrapper: {
    flex: 1,
    position: 'relative',
  },
  sheetModalRoot: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  sheetBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
  },
  bottomSheetCard: {
    backgroundColor: theme.colors.surfaceWhite,
    borderTopLeftRadius: theme.radii.xl,
    borderTopRightRadius: theme.radii.xl,
    padding: 16,
    paddingBottom: 24,
    gap: 8,
    ...theme.shadows.card,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
  },
  sheetHandle: {
    width: 40,
    height: 4,
    borderRadius: theme.radii.full,
    backgroundColor: theme.colors.surfaceContainer,
    alignSelf: 'center',
    marginBottom: 4,
  },
  sheetHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sheetTagWrapper: {
    backgroundColor: theme.colors.surfaceContainerLow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: theme.radii.sm,
  },
  sheetCategoryTag: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontSize: 10,
    fontWeight: '700',
  },
  closeButton: {
    padding: 4,
  },
  sheetTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    fontSize: 16,
  },
  sheetSub: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 12,
  },
  sheetDistance: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontSize: 11,
    fontWeight: '600',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.brandForest,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: theme.radii.full,
    gap: 6,
    marginTop: 4,
  },
  actionButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
});
