import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, Image, Modal, Platform, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQueryClient } from '@tanstack/react-query';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { Badge } from '../../../src/components/common/Badge';
import { CategoryFilters } from '../../../src/components/catalog/CategoryFilters';
import { MapAdapter } from '../../../src/components/map/MapAdapter';
import { AccessibleModal } from '../../../src/components/common/AccessibleModal';
import { GooglePlacePhoto } from '../../../src/components/common/GooglePlacePhoto';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { useRouteActorsQuery, useRouteMapQuery } from '../../../src/hooks/queries';
import { theme } from '../../../src/theme/theme';
import { makeAccessibleButton, setAccessibilityFocusSafely } from '../../../src/utils/accessibility';
import { filterPinsByModeAndCategory, formatCoordinateDisplay, getBoundsCoordinates, isContractPinColor, isContractPinIcon } from '../../../src/components/map/MapAdapter.helpers';
import { apiClient } from '../../../src/api/client';
import { queryKeys } from '../../../src/api/queryKeys';
import { CHOOSE_ON_MAP_ORIGIN_ID } from '../../../src/components/routes/OriginSelector';
import { DynamicLocationConsentModal } from '../../../src/components/routes/DynamicLocationConsentModal';
import { GoogleRoutesMapNotice } from '../../../src/components/routes/GoogleRoutesMapNotice';
import { hasValidLocationConsent } from '../../../src/auth/locationConsent';
import { useAppContext } from '../../../src/state/useAppContext';
import type { MapPin, MapLegendItem } from '../../../src/api/types';
import type { MapCoordinate, MapViewMode } from '../../../src/components/map/MapAdapter.types';

const AccessibleMapControl = ({
  children,
  style,
  onPress,
  label,
  hint,
  selected,
  disabled = false,
}: {
  children: React.ReactNode;
  style: unknown;
  onPress: () => void;
  label: string;
  hint?: string;
  selected?: boolean;
  disabled?: boolean;
}) => {
  if (Platform.OS === 'web') {
    return React.createElement(
      'button',
      {
        type: 'button',
        style: StyleSheet.flatten(style as never),
        onClick: disabled ? undefined : onPress,
        disabled,
        'aria-label': label,
        'aria-pressed': selected,
        title: hint,
      },
      children
    );
  }

  return (
    <TouchableOpacity
      style={style as never}
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={hint}
      accessibilityState={{ selected, disabled }}
    >
      {children}
    </TouchableOpacity>
  );
};

export default function MapScreen() {
  const router = useRouter();
  const { state: appState } = useAppContext();
  const isDynamicRoutingEnabled = Boolean(appState?.featureFlags?.dynamicRouting);

  let queryClient: ReturnType<typeof useQueryClient> | undefined;
  try {
    queryClient = useQueryClient();
  } catch {
    queryClient = undefined;
  }

  const {
    routeId = '',
    originId,
    actorId: initialActorId,
    mode: initialMode,
    viewMode: initialViewMode,
    category: initialCategory,
    q: initialQuery,
  } = useLocalSearchParams<{
    routeId: string;
    originId?: string;
    actorId?: string;
    mode?: string;
    viewMode?: MapViewMode;
    category?: string;
    q?: string;
  }>();

  const isSelectionModeInitial = isDynamicRoutingEnabled && initialMode === 'select-origin';
  const [isSelectionMode, setIsSelectionMode] = useState<boolean>(isSelectionModeInitial);
  const [selectedCoordinate, setSelectedCoordinate] = useState<MapCoordinate | null>(null);
  const [isConfirmingSelection, setIsConfirmingSelection] = useState<boolean>(false);
  const [showConsentModal, setShowConsentModal] = useState<boolean>(false);

  const [viewMode, setViewMode] = useState<MapViewMode>(initialViewMode === 'city' ? 'city' : 'route');
  const [selectedCategory, setSelectedCategory] = useState<string>(initialCategory?.trim() || '');
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

  useEffect(() => {
    if (!isDynamicRoutingEnabled && isSelectionMode) {
      setIsSelectionMode(false);
      setSelectedCoordinate(null);
    }
  }, [isDynamicRoutingEnabled, isSelectionMode]);

  const mapQuery = useRouteMapQuery(routeId, {
    origin_id: originId,
  });
  const actorsQuery = useRouteActorsQuery(routeId, {
    origin_id: originId,
    category: selectedCategory || undefined,
  });

  // Check for ephemeral preview data passed via memory cache (when expanded from dynamic preview)
  const ephemeralData = React.useMemo(() => {
    if (!isDynamicRoutingEnabled || !queryClient || isSelectionMode) return null;
    return queryClient.getQueryData<{
      previewData: import('../../../src/api/types').RoutePreviewData;
      originType: string;
    }>(queryKeys.routes.ephemeralPreview(routeId));
  }, [isDynamicRoutingEnabled, queryClient, routeId, isSelectionMode]);

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

  const handleSelectMapCoordinate = (coord: MapCoordinate) => {
    if (!isDynamicRoutingEnabled) return;
    setSelectedCoordinate(coord);
  };

  const handleCancelSelection = () => {
    setSelectedCoordinate(null);
    setIsSelectionMode(false);
    if (isSelectionModeInitial) {
      router.back();
    }
  };

  const executeRoutePreview = async (coord: MapCoordinate) => {
    setIsConfirmingSelection(true);
    try {
      const response = await apiClient.previewRoute(routeId, {
        latitude: coord.latitude,
        longitude: coord.longitude,
        travel_mode: 'DRIVE',
      });
      // Transfer ephemeral preview data via memory cache without exposing coordinates in URL
      if (queryClient) {
        queryClient.setQueryData(queryKeys.routes.ephemeralPreview(routeId), {
          previewData: response.data,
          originType: CHOOSE_ON_MAP_ORIGIN_ID,
        });
      }
      // Navigate back to detail screen
      router.back();
    } catch {
      Alert.alert(
        'Erro ao calcular rota',
        'Não foi possível calcular o trajeto a partir destas coordenadas. Tente outro ponto no mapa.'
      );
    } finally {
      setIsConfirmingSelection(false);
    }
  };

  const handleConfirmSelection = async () => {
    if (!isDynamicRoutingEnabled || !selectedCoordinate || isConfirmingSelection) return;
    const hasConsent = await hasValidLocationConsent();
    if (!hasConsent) {
      setShowConsentModal(true);
      return;
    }
    await executeRoutePreview(selectedCoordinate);
  };

  const handleConsentSuccess = async () => {
    setShowConsentModal(false);
    if (selectedCoordinate) {
      await executeRoutePreview(selectedCoordinate);
    }
  };

  const handleConsentCancel = () => {
    setShowConsentModal(false);
    handleCancelSelection();
  };

  const [isProlongedLoading, setIsProlongedLoading] = useState<boolean>(false);

  useEffect(() => {
    if (mapQuery.isPending && !ephemeralData?.previewData) {
      const timer = setTimeout(() => {
        setIsProlongedLoading(true);
      }, 4000);
      return () => clearTimeout(timer);
    } else if (isProlongedLoading) {
      setIsProlongedLoading(false);
    }
  }, [mapQuery.isPending, ephemeralData?.previewData, isProlongedLoading]);

  if (mapQuery.isPending && !ephemeralData?.previewData) {
    const loadingMessage = isProlongedLoading
      ? 'Servidor de staging iniciando; isso pode levar alguns segundos.'
      : 'Carregando mapa da rota...';
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Mapa da Rota" />
        <LoadingView message={loadingMessage} />
      </View>
    );
  }

  if (mapQuery.isError && !ephemeralData?.previewData) {
    const errorCode = (mapQuery.error as { code?: string } | null)?.code;
    const errorCopy = errorCode === 'OFFLINE'
      ? {
          title: 'Mapa indisponível offline',
          message: 'Reconecte-se para atualizar os pontos e tente novamente.',
        }
      : errorCode === 'TIMEOUT'
      ? {
          title: 'O mapa demorou para responder',
          message: 'A conexão pode estar instável ou o servidor demorou para responder. Tente carregar novamente.',
        }
      : {
          title: 'Erro ao carregar mapa',
          message: 'Não foi possível carregar os dados geoespaciais do mapa.',
        };
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Mapa da Rota" />
        <ErrorStateView
          title={errorCopy.title}
          message={errorCopy.message}
          onRetry={() => void mapQuery.refetch()}
        />
      </View>
    );
  }

  if (!mapQuery.data && !ephemeralData?.previewData) {
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

  const isGoogleRoutesPreview = ephemeralData?.previewData.provider === 'google_routes';
  const mapPayload: import('../../../src/api/types').RouteMapPayload = ephemeralData?.previewData
    ? {
        route_id: routeId,
        selected_origin_id: undefined,
        bounds: ephemeralData.previewData.bounds,
        city_bounds: ephemeralData.previewData.city_bounds,
        pins: ephemeralData.previewData.pins ?? [],
        legend: ephemeralData.previewData.legend ?? [],
        geometry: {
          id: ephemeralData.originType || 'dynamic_preview',
          route_origin_id: ephemeralData.originType || 'dynamic_preview',
          provider: ephemeralData.previewData.provider || 'dynamic_preview',
          geojson: ephemeralData.previewData.geojson,
          encoded_polyline: ephemeralData.previewData.encoded_polyline ?? null,
          distance_m: ephemeralData.previewData.distance_m,
          duration_s: ephemeralData.previewData.duration_s,
        },
      }
    : mapQuery.data!;
  const allPins = mapPayload.pins;
  const legend = [...mapPayload.legend].sort((a, b) => a.sort_order - b.sort_order);
  const legendBySlug = new Map(legend.map((item) => [item.category_slug, item]));
  const hasInvalidMetadata =
    mapPayload.route_id !== routeId ||
    Boolean(originId && mapPayload.selected_origin_id && mapPayload.selected_origin_id !== originId) ||
    getBoundsCoordinates(mapPayload.bounds).length !== 2 ||
    allPins.length > 200 ||
    legend.some((item) =>
      !item.category_slug || !item.label || !isContractPinColor(item.color) ||
      !isContractPinIcon(item.icon) || !Number.isInteger(item.count) || item.count < 0
    ) ||
    allPins.some((pin) => {
      const item = legendBySlug.get(pin.category_slug);
      return !item || !isContractPinColor(pin.color) || !isContractPinIcon(pin.icon) ||
        pin.color !== item.color || pin.icon !== item.icon || pin.category_label !== item.label;
    }) ||
    legend.some((item) => item.count !== allPins.filter((pin) => pin.category_slug === item.category_slug).length);

  if (hasInvalidMetadata) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Mapa da Rota" />
        <ErrorStateView
          title="Mapa temporariamente indisponível"
          message="Os metadados visuais do mapa são inválidos. Tente carregar novamente."
          onRetry={() => void mapQuery.refetch()}
        />
      </View>
    );
  }

  if (!isGoogleRoutesPreview && allPins.length === 0 && legend.every((item) => item.count === 0)) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Mapa da Rota" />
        <EmptyStateView
          title="Nenhum ponto nesta rota"
          message="Não há pontos disponíveis para esta origem."
          onReset={() => void mapQuery.refetch()}
          resetLabel="Tentar novamente"
        />
      </View>
    );
  }

  const cityModeAvailable = getBoundsCoordinates(mapPayload.city_bounds).length === 2;
  const displayedViewMode: MapViewMode = viewMode === 'city' && cityModeAvailable ? 'city' : 'route';

  // Filter pins according to viewMode & selectedCategory, keeping the selectedActorId pin visible
  const filteredPins = filterPinsByModeAndCategory(
    allPins,
    displayedViewMode,
    selectedCategory,
    selectedActorId
  );

  // Active bounds based on viewMode: city_bounds with fallback to bounds for city mode, bounds for route mode
  const activeBounds =
    displayedViewMode === 'city'
      ? mapPayload.city_bounds
      : mapPayload.bounds;

  // Find details of selected pin or actor
  const selectedPin: MapPin | undefined = allPins.find(
    (p) => p.actor_id === selectedActorId || p.id === selectedActorId
  );
  const actorsList = Array.isArray(actorsQuery.data)
    ? actorsQuery.data
    : actorsQuery.data?.data || (actorsQuery.data as any)?.items;
  const selectedActorSummary = actorsList?.find(
    (a: any) => a.id === selectedActorId
  );

  return (
    <View style={styles.container}>
      <AppHeader
        showBack
        onBackPress={() => router.back()}
        title={isSelectionMode ? 'Escolher Origem no Mapa' : 'Mapa da Rota'}
      />

      {/* Selection Mode Instructions Bar */}
      {isSelectionMode ? (
        <View style={styles.selectionModeHeader} accessibilityRole="summary" accessibilityLiveRegion="polite">
          <Ionicons name="location-outline" size={18} color={theme.colors.brandDeep} />
          <Text style={styles.selectionModeHeaderText}>
            {selectedCoordinate
              ? 'Arraste o marcador laranja ou toque no mapa para ajustar.'
              : 'Toque no mapa para posicionar seu ponto de partida.'}
          </Text>
        </View>
      ) : (
        <>
          {/* View Mode Toggle Bar */}
          <View style={styles.modeToggleBar} accessibilityRole="toolbar" accessibilityLabel="Modos de visualização do mapa">
            <AccessibleMapControl
              style={[styles.modeTab, displayedViewMode === 'route' && styles.modeTabActive]}
              onPress={() => setViewMode('route')}
              label="Modo de visualização da rota"
              hint="Filtra a visualização para o corredor e pontos da rota selecionada"
              selected={displayedViewMode === 'route'}
            >
              <Ionicons
                name="trail-sign-outline"
                size={16}
                color={displayedViewMode === 'route' ? theme.colors.surfaceWhite : theme.colors.brandForest}
              />
              <Text
                style={[styles.modeTabText, displayedViewMode === 'route' && styles.modeTabTextActive]}
              >
                Ver rota
              </Text>
            </AccessibleMapControl>

            <AccessibleMapControl
              style={[styles.modeTab, displayedViewMode === 'city' && styles.modeTabActive]}
              onPress={() => cityModeAvailable && setViewMode('city')}
              disabled={!cityModeAvailable}
              label="Modo de visualização da cidade"
              hint="Expande a visualização para todos os pontos e limites da cidade"
              selected={displayedViewMode === 'city'}
            >
              <Ionicons
                name="business-outline"
                size={16}
                color={displayedViewMode === 'city' ? theme.colors.surfaceWhite : theme.colors.brandForest}
              />
              <Text
                style={[styles.modeTabText, displayedViewMode === 'city' && styles.modeTabTextActive]}
              >
                Ver cidade
              </Text>
            </AccessibleMapControl>
          </View>

          {/* Category Filter Chips Bar */}
          <View style={styles.filterBar}>
            <CategoryFilters
              categories={legend}
              selectedCategory={selectedCategory}
              onSelectCategory={(catSlug) => {
                setSelectedCategory(catSlug);
              }}
            />
          </View>
          {!cityModeAvailable && (
            <Text style={styles.modeStatus} accessibilityLiveRegion="polite">
              A visualização da cidade não está disponível para esta origem.
            </Text>
          )}
          <Text style={styles.srStatus} accessibilityLiveRegion="polite">
            {displayedViewMode === 'route' ? 'Visualização da rota' : 'Visualização da cidade'}: {filteredPins.length} pontos visíveis.
          </Text>
        </>
      )}

      {/* Interactive Map Area */}
      <View
        ref={mapRegionRef}
        style={styles.mapWrapper}
        focusable
        tabIndex={-1}
        accessible
        accessibilityRole="summary"
        accessibilityLabel={isSelectionMode ? 'Mapa interativo de seleção de origem' : 'Mapa interativo da rota'}
      >
        {isGoogleRoutesPreview && ephemeralData?.previewData ? (
          <GoogleRoutesMapNotice
            distanceMeters={ephemeralData.previewData.distance_m}
            durationSeconds={ephemeralData.previewData.duration_s}
          />
        ) : (
          <MapAdapter
            pins={filteredPins}
            geometry={mapPayload.geometry}
            bounds={activeBounds}
            selectedActorId={selectedActorId}
            onSelectActor={(id) => {
              if (!isSelectionMode) {
                setSelectedActorId(id);
              }
            }}
            selectionMode={isSelectionMode}
            selectedCoordinate={selectedCoordinate}
            onSelectCoordinate={handleSelectMapCoordinate}
            selectionPinLabel="Ponto de partida escolhido"
            height="100%"
          />
        )}

        {!isSelectionMode && filteredPins.length === 0 && (
          <View style={styles.filteredEmpty} accessibilityLiveRegion="polite">
            <Text style={styles.filteredEmptyText}>Nenhum ponto neste modo ou filtro.</Text>
            <TouchableOpacity
              style={styles.filteredEmptyButton}
              onPress={() => setSelectedCategory('')}
              {...makeAccessibleButton('Limpar filtro do mapa')}
            >
              <Text style={styles.filteredEmptyButtonText}>Limpar filtro</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Selection bottom confirm / cancel action bar */}
        {isSelectionMode && selectedCoordinate && (
          <View style={styles.selectionActionBar} accessibilityLiveRegion="polite">
            <View style={styles.selectionCoordInfo}>
              <Ionicons name="pin" size={16} color="#EA580C" />
              <Text style={styles.selectionCoordText}>
                Coordenadas: {formatCoordinateDisplay(selectedCoordinate)}
              </Text>
            </View>
            <View style={styles.selectionActionButtons}>
              <TouchableOpacity
                style={[styles.selectionBtn, styles.selectionCancelBtn]}
                onPress={handleCancelSelection}
                disabled={isConfirmingSelection}
                {...makeAccessibleButton('Cancelar seleção de ponto de partida')}
              >
                <Text style={styles.selectionCancelText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.selectionBtn, styles.selectionConfirmBtn]}
                onPress={handleConfirmSelection}
                disabled={isConfirmingSelection}
                {...makeAccessibleButton('Confirmar ponto de partida escolhido')}
              >
                {isConfirmingSelection ? (
                  <ActivityIndicator size="small" color={theme.colors.surfaceWhite} />
                ) : (
                  <Text style={styles.selectionConfirmText}>Confirmar Ponto de Partida</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Contextual button to return to route mode when in city view */}
        {!isSelectionMode && displayedViewMode === 'city' && (
          <AccessibleMapControl
            style={styles.returnToRouteButton}
            onPress={() => setViewMode('route')}
            label="Voltar para a rota"
            hint="Retorna a visualização para o corredor e enquadramento da rota"
          >
            <Ionicons name="arrow-back" size={14} color={theme.colors.brandForest} />
            <Text style={styles.returnToRouteText}>Voltar para a rota</Text>
          </AccessibleMapControl>
        )}
      </View>

      {/* Accessible actor preview sheet. The backdrop is a sibling so its press
          cannot propagate through the sheet to map controls or pins. */}
      <AccessibleModal
        visible={!isSelectionMode && Boolean(selectedActorId) && Boolean(selectedPin || selectedActorSummary)}
        transparent
        animationType="slide"
        onClose={closeActorSheet}
        initialFocusRef={closeSheetButtonRef}
        returnFocusRef={mapRegionRef}
        accessibilityLabel="Painel de detalhes do ator selecionado"
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
                  {(selectedPin?.category_label || selectedActorSummary?.category_label || selectedPin?.category_slug || 'Ponto da Rota').toUpperCase()}
                </Text>
                {selectedActorSummary?.verification_status === 'verified' && (
                  <Badge type="semturInventory" label="Inventário SEMTUR" />
                )}
                {selectedActorSummary?.green_badge_status === 'verified' && (
                  <Badge type="greenSeal" label="Selo Verde" />
                )}
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

            {typeof selectedActorSummary?.google_rating === 'number' && Number.isFinite(selectedActorSummary.google_rating) && (
              <View
                style={styles.sheetRatingRow}
                accessibilityRole="text"
                accessibilityLabel={`Avaliação Google: ${selectedActorSummary.google_rating.toFixed(1)} estrelas`}
              >
                <Ionicons name="star" size={14} color={theme.colors.brandSun} />
                <Text style={styles.sheetRatingText}>{`${selectedActorSummary.google_rating.toFixed(1)} Google`}</Text>
              </View>
            )}

            {typeof selectedPin?.distance_from_origin_m === 'number' && (
              <Text style={styles.sheetDistance}>
                Distância da origem: {(selectedPin.distance_from_origin_m / 1000).toFixed(1)} km
              </Text>
            )}

            <View style={styles.sheetPhotoContainer}>
              {selectedActorSummary?.cover_media?.derivatives?.card || selectedActorSummary?.cover_media?.url || selectedActorSummary?.cover_image_url ? (
                <Image
                  source={{
                    uri:
                      selectedActorSummary?.cover_media?.derivatives?.card ??
                      selectedActorSummary?.cover_media?.url ??
                      selectedActorSummary?.cover_image_url,
                  }}
                  style={styles.sheetCoverImage}
                  resizeMode="cover"
                  accessible
                  accessibilityLabel={
                    selectedActorSummary?.cover_media?.alt_text ||
                    `Foto de ${selectedPin?.name || selectedActorSummary?.name}`
                  }
                />
              ) : (selectedPin?.actor_id || selectedPin?.id || selectedActorSummary?.id || selectedActorId) ? (
                <GooglePlacePhoto
                  actorId={
                    (selectedPin?.actor_id ||
                      selectedPin?.id ||
                      selectedActorSummary?.id ||
                      selectedActorId)!
                  }
                  alt={`Foto de ${selectedPin?.name || selectedActorSummary?.name || 'estabelecimento'}`}
                  compact
                />
              ) : null}
            </View>

            {actorsQuery.isFetching && !selectedActorSummary && (
              <ActivityIndicator accessibilityLabel="Carregando detalhes do ator" />
            )}
            {actorsQuery.isError && !selectedActorSummary && (
              <View accessibilityLiveRegion="polite" style={styles.sheetQueryError}>
                <Text style={styles.sheetQueryErrorText}>Detalhes adicionais indisponíveis.</Text>
                <TouchableOpacity
                  style={styles.sheetRetryButton}
                  onPress={() => void actorsQuery.refetch()}
                  {...makeAccessibleButton('Tentar carregar detalhes do ator novamente')}
                >
                  <Text style={styles.sheetRetryButtonText}>Tentar novamente</Text>
                </TouchableOpacity>
              </View>
            )}

            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => {
                const targetActorId =
                  selectedPin?.actor_id ||
                  selectedPin?.id ||
                  selectedActorSummary?.id ||
                  selectedActorId;
                if (targetActorId) {
                  router.push(
                    `/route/${encodeURIComponent(routeId)}/catalog?${new URLSearchParams({
                      ...(originId ? { originId } : {}),
                      actorId: targetActorId,
                      ...(selectedCategory ? { category: selectedCategory } : {}),
                      ...(initialQuery ? { q: initialQuery } : {}),
                      viewMode: displayedViewMode,
                    }).toString()}`
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
      </AccessibleModal>

      {/* LGPD Dynamic Location Consent Gate Modal */}
      {showConsentModal && (
        <DynamicLocationConsentModal
          visible
          onConsentSuccess={handleConsentSuccess}
          onCancelFixedOrigin={handleConsentCancel}
        />
      )}
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
  modeStatus: {
    ...theme.typography.labelSm,
    color: theme.colors.onSurfaceVariant,
    backgroundColor: theme.colors.surfaceWhite,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  srStatus: {
    position: 'absolute',
    width: 1,
    height: 1,
    overflow: 'hidden',
    opacity: 0,
  },
  modeToggleBar: {
    flexDirection: 'row',
    backgroundColor: theme.colors.surfaceWhite,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
    gap: 8,
    zIndex: 11,
  },
  modeTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: theme.radii.full,
    backgroundColor: theme.colors.surfaceContainerLow,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
    minHeight: 44,
  },
  modeTabActive: {
    backgroundColor: theme.colors.brandForest,
    borderColor: theme.colors.brandForest,
  },
  modeTabText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandForest,
    fontWeight: '600',
  },
  modeTabTextActive: {
    color: theme.colors.surfaceWhite,
  },
  returnToRouteButton: {
    position: 'absolute',
    bottom: 20,
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: theme.colors.surfaceWhite,
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: theme.radii.full,
    ...theme.shadows.card,
    borderWidth: 1,
    borderColor: theme.colors.brandForest,
    zIndex: 20,
    minHeight: 44,
  },
  returnToRouteText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '700',
  },
  selectionModeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingVertical: 10,
    paddingHorizontal: 16,
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#FDE68A',
    zIndex: 15,
  },
  selectionModeHeaderText: {
    ...theme.typography.labelSm,
    color: '#92400E',
    fontWeight: '600',
    flex: 1,
  },
  selectionActionBar: {
    position: 'absolute',
    bottom: 20,
    left: 16,
    right: 16,
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.xl,
    padding: 14,
    gap: 10,
    ...theme.shadows.card,
    borderWidth: 1,
    borderColor: 'rgba(234, 88, 12, 0.3)',
    zIndex: 25,
  },
  selectionCoordInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  selectionCoordText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandDeep,
    fontWeight: '600',
  },
  selectionActionButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  selectionBtn: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: theme.radii.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectionCancelBtn: {
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  selectionCancelText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandDeep,
    fontWeight: '600',
  },
  selectionConfirmBtn: {
    backgroundColor: '#EA580C',
  },
  selectionConfirmText: {
    ...theme.typography.labelMd,
    color: theme.colors.surfaceWhite,
    fontWeight: '700',
  },
  mapWrapper: {
    flex: 1,
    position: 'relative',
  },
  filteredEmpty: {
    position: 'absolute',
    top: 12,
    left: 16,
    right: 16,
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.md,
    padding: 12,
    alignItems: 'center',
    gap: 8,
    zIndex: 18,
    ...theme.shadows.card,
  },
  filteredEmptyText: {
    ...theme.typography.bodySm,
    color: theme.colors.brandDeep,
  },
  filteredEmptyButton: {
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: 16,
    borderRadius: theme.radii.full,
    borderWidth: 1,
    borderColor: theme.colors.brandForest,
  },
  filteredEmptyButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandForest,
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
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 6,
  },
  sheetCategoryTag: {
    ...theme.typography.labelSm,
    backgroundColor: theme.colors.surfaceContainerLow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: theme.radii.sm,
    color: theme.colors.brandForest,
    fontSize: 10,
    fontWeight: '700',
  },
  closeButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
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
  sheetRatingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginVertical: 2,
  },
  sheetRatingText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandDeep,
    fontWeight: '700',
    fontSize: 12,
  },
  sheetPhotoContainer: {
    width: '100%',
    marginVertical: 4,
    borderRadius: theme.radii.md,
    overflow: 'hidden',
  },
  sheetCoverImage: {
    width: '100%',
    aspectRatio: 16 / 9,
    maxHeight: 140,
    borderRadius: theme.radii.md,
  },
  sheetQueryError: {
    gap: 8,
  },
  sheetQueryErrorText: {
    ...theme.typography.bodySm,
    color: theme.colors.error,
  },
  sheetRetryButton: {
    minHeight: 44,
    alignSelf: 'flex-start',
    justifyContent: 'center',
    paddingHorizontal: 14,
    borderRadius: theme.radii.full,
    borderWidth: 1,
    borderColor: theme.colors.brandForest,
  },
  sheetRetryButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandForest,
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
    minHeight: 44,
  },
  actionButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
});
