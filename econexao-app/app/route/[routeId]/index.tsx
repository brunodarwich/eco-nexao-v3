import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View, Alert, ActivityIndicator, AccessibilityInfo, Image } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQueryClient } from '@tanstack/react-query';
import { LinearGradient } from 'expo-linear-gradient';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { LocalCatalogPreview } from '../../../src/components/routes/LocalCatalogPreview';
import { OriginSelector, MY_LOCATION_ORIGIN_ID, CHOOSE_ON_MAP_ORIGIN_ID } from '../../../src/components/routes/OriginSelector';
import { RouteMapPreview } from '../../../src/components/routes/RouteMapPreview';
import { getPindobalCoverImage } from '../../../src/components/routes/routeCoverImage';
import { useRouteAlertsQuery, useRouteDetailQuery } from '../../../src/hooks/queries';
import { theme, useAppTheme } from '../../../src/theme/theme';

import { makeAccessibleButton } from '../../../src/utils/accessibility';
import { apiClient, ApiClientError } from '../../../src/api/client';
import { queryKeys } from '../../../src/api/queryKeys';
import { AuthContext } from '../../../src/auth/AuthProvider';
import { useAppContext } from '../../../src/state/useAppContext';
import type { RoutePreviewData, RouteGeometry, MapBounds } from '../../../src/api/types';
import type { MapCoordinate } from '../../../src/components/map/MapAdapter.types';
import type { LocationCoordinates } from '../../../src/hooks/useCurrentLocation';

const routePath = (
  routeId: string,
  destination: 'map' | 'catalog',
  originId?: string,
  actorId?: string,
  category?: string,
  mode?: string
) => {
  const query = new URLSearchParams();
  if (originId && originId !== MY_LOCATION_ORIGIN_ID && originId !== CHOOSE_ON_MAP_ORIGIN_ID) {
    query.set('originId', originId);
  }
  if (actorId) query.set('actorId', actorId);
  if (category) query.set('category', category);
  if (mode) query.set('mode', mode);
  const suffix = query.toString();
  return `/route/${encodeURIComponent(routeId)}/${destination}${suffix ? `?${suffix}` : ''}`;
};

export default function RouteDetailScreen() {
  const router = useRouter();
  const theme = useAppTheme();
  const { state: appState } = useAppContext();
  const isDynamicRoutingEnabled = Boolean(appState?.featureFlags?.dynamicRouting);
  let queryClient: ReturnType<typeof useQueryClient> | undefined;
  try {
    queryClient = useQueryClient();
  } catch {
    queryClient = undefined;
  }
  const auth = React.useContext(AuthContext);
  const user = auth?.user;
  const { routeId = '', originId: initialOriginId, actorId } = useLocalSearchParams<{
    routeId: string;
    originId?: string;
    actorId?: string;
  }>();

  const [isStartingTrip, setIsStartingTrip] = useState(false);
  const detail = useRouteDetailQuery(routeId);

  const [originId, setOriginId] = useState<string | undefined>(initialOriginId);
  const [previewData, setPreviewData] = useState<RoutePreviewData | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const lastValidOriginIdRef = React.useRef<string | undefined>(initialOriginId);

  const isCustomLocation = isDynamicRoutingEnabled && (originId === MY_LOCATION_ORIGIN_ID || originId === CHOOSE_ON_MAP_ORIGIN_ID || Boolean(previewData));
  const requestedOriginExists = detail.data?.origins.some((origin) => origin.id === originId);
  const effectiveOrigin = isCustomLocation ? originId : (requestedOriginExists ? originId : detail.data?.origins[0]?.id);

  useEffect(() => {
    setOriginId(initialOriginId);
    setPreviewData(null);
    if (initialOriginId && initialOriginId !== MY_LOCATION_ORIGIN_ID && initialOriginId !== CHOOSE_ON_MAP_ORIGIN_ID) {
      lastValidOriginIdRef.current = initialOriginId;
    }
  }, [initialOriginId, routeId]);

  // Read ephemeral preview transferred from map screen via memory cache
  useEffect(() => {
    if (!isDynamicRoutingEnabled || !queryClient || !routeId) return;
    const ephemeralKey = queryKeys.routes.ephemeralPreview(routeId);
    const cachedData = queryClient.getQueryData<{
      previewData: RoutePreviewData;
      originType: string;
    }>(ephemeralKey);

    if (cachedData?.previewData) {
      setPreviewData(cachedData.previewData);
      setOriginId(cachedData.originType || CHOOSE_ON_MAP_ORIGIN_ID);
      AccessibilityInfo.announceForAccessibility('Trajeto sugerido a partir do ponto escolhido no mapa carregado.');
      // Consume/clear ephemeral preview so subsequent back/focus operations don't re-trigger
      queryClient.removeQueries({ queryKey: ephemeralKey });
    }
  }, [queryClient, routeId, isDynamicRoutingEnabled]);

  const alerts = useRouteAlertsQuery(routeId);

  const handleSelectOrigin = (newOriginId: string) => {
    setOriginId(newOriginId);
    if (newOriginId !== MY_LOCATION_ORIGIN_ID && newOriginId !== CHOOSE_ON_MAP_ORIGIN_ID) {
      lastValidOriginIdRef.current = newOriginId;
      setPreviewData(null);
      if (queryClient) {
        queryClient.removeQueries({ queryKey: queryKeys.routes.ephemeralPreview(routeId) });
      }
    }
  };

  const handleSelectCoordinate = async (coords: MapCoordinate, originType: string = CHOOSE_ON_MAP_ORIGIN_ID) => {
    if (isPreviewLoading || !isDynamicRoutingEnabled) return;
    setIsPreviewLoading(true);
    try {
      const response = await apiClient.previewRoute(routeId, {
        latitude: coords.latitude,
        longitude: coords.longitude,
        travel_mode: 'DRIVE',
      });
      setPreviewData(response.data);
      setOriginId(originType);
      AccessibilityInfo.announceForAccessibility('Trajeto sugerido a partir do ponto escolhido carregado com sucesso.');
    } catch {
      // Fallback to previous valid origin or first origin
      const fallbackOrigin = lastValidOriginIdRef.current || detail.data?.origins[0]?.id;
      setOriginId(fallbackOrigin);
      setPreviewData(null);
      AccessibilityInfo.announceForAccessibility('Não foi possível calcular o trajeto sugerido.');
      Alert.alert(
        'Trajeto Sugerido Indisponível',
        'Não conseguimos calcular o trajeto sugerido a partir deste ponto. Exibindo rota pela origem padrão.'
      );
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleSelectCurrentLocation = async (coords: LocationCoordinates) => {
    if (!isDynamicRoutingEnabled) return;
    await handleSelectCoordinate(coords, MY_LOCATION_ORIGIN_ID);
  };

  const handleStartSelectOnMap = () => {
    if (!isDynamicRoutingEnabled) return;
    router.push(routePath(routeId, 'map', isCustomLocation ? undefined : effectiveOrigin, actorId, undefined, 'select-origin'));
  };

  const handleStartTrip = async () => {
    try {
      setIsStartingTrip(true);
      await apiClient.createTrip(routeId);
      if (queryClient && user?.id) {
        void queryClient.invalidateQueries({ queryKey: queryKeys.myTrips(user.id) });
      }

      AccessibilityInfo.announceForAccessibility('Viagem iniciada com sucesso. Bom passeio sustentável!');
      Alert.alert('Viagem Iniciada', 'Sua viagem foi registrada no histórico do seu perfil.');
    } catch {
      AccessibilityInfo.announceForAccessibility('Erro ao iniciar viagem.');
      Alert.alert('Erro', 'Não foi possível registrar o início da viagem no momento.');
    } finally {
      setIsStartingTrip(false);
    }
  };

  if (detail.isPending) {
    return <LoadingView message="Carregando detalhes da rota..." />;
  }

  const isNotFound = detail.error instanceof ApiClientError && detail.error.status === 404;

  if (isNotFound || (!detail.isPending && !detail.isError && !detail.data)) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Detalhes da Rota" />
        <EmptyStateView
          title="Rota não encontrada"
          message="A rota solicitada não existe ou pode estar temporariamente indisponível."
          onReset={() => void detail.refetch()}
          resetLabel="Tentar novamente"
        />
        <TouchableOpacity
          style={styles.notFoundBackButton}
          onPress={() => router.back()}
          {...makeAccessibleButton('Voltar para a lista')}
        >
          <Text style={styles.notFoundBackText}>Voltar para a lista</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (detail.isError) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Detalhes da Rota" />
        <ErrorStateView
          title="Erro ao carregar rota"
          message="Não foi possível carregar as informações desta rota."
          onRetry={() => void detail.refetch()}
        />
      </View>
    );
  }

  const route = detail.data;
  const pindobalHeroImage = getPindobalCoverImage(route);

  const customGeometry: RouteGeometry | null = previewData
    ? {
        id: originId || MY_LOCATION_ORIGIN_ID,
        route_origin_id: originId || MY_LOCATION_ORIGIN_ID,
        provider: previewData.provider || 'dynamic_preview',
        geojson: previewData.geojson,
        encoded_polyline: previewData.encoded_polyline ?? null,
        distance_m: previewData.distance_m,
        duration_s: previewData.duration_s,
      }
    : null;

  const customBounds: MapBounds | null = previewData?.bounds ?? null;
  const originSelector = route.origins && route.origins.length > 0 ? (
    <OriginSelector
      origins={route.origins}
      selectedOriginId={effectiveOrigin}
      onSelectOrigin={handleSelectOrigin}
      onSelectCurrentLocation={handleSelectCurrentLocation}
      onStartSelectOnMap={handleStartSelectOnMap}
      isLoadingLocation={isPreviewLoading}
      enableDynamicRouting={isDynamicRoutingEnabled}
    />
  ) : null;

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title={route.title} />

      <ScrollView contentContainerStyle={styles.content}>
        {/* Header Hero Section */}
        {pindobalHeroImage ? (
          <View style={styles.pindobalHeroStack}>
            <View style={[styles.heroSection, styles.heroSectionWithImage]}>
              <Image
                source={pindobalHeroImage}
                style={styles.heroImage}
                resizeMode="cover"
                accessible={false}
              />
              <View style={styles.heroOverlay}>
                <Text style={[styles.title, styles.titleOnImage]}>{route.title}</Text>
                <Text style={[styles.subtitle, styles.subtitleOnImage]}>
                  {route.city}, {route.state_code}
                  {route.is_verified && ' • Rota Verificada'}
                </Text>
                <Text style={[styles.description, styles.descriptionOnImage]}>{route.description ?? route.summary}</Text>
              </View>
              <LinearGradient
                pointerEvents="none"
                colors={[
                  'rgba(249, 250, 247, 0)',
                  'rgba(249, 250, 247, 0.12)',
                  'rgba(249, 250, 247, 0.42)',
                  'rgba(249, 250, 247, 0.76)',
                  theme.colors.surfaceBackground,
                ]}
                locations={[0, 0.28, 0.56, 0.8, 1]}
                style={styles.heroBottomGradient}
              />
            </View>
            {originSelector ? <View style={styles.originSelectorOverlay}>{originSelector}</View> : null}
          </View>
        ) : (
          <>
            <View style={styles.heroSection}>
              <Text style={styles.title}>{route.title}</Text>
              <Text style={styles.subtitle}>
                {route.city}, {route.state_code}
                {route.is_verified && ' • Rota Verificada'}
              </Text>
              <Text style={styles.description}>{route.description ?? route.summary}</Text>
            </View>
            {originSelector}
          </>
        )}

        {/* Dynamic preview notice banner */}
        {isCustomLocation && (
          <View style={styles.previewNoticeBanner} accessibilityRole="alert" accessibilityLiveRegion="polite">
            <Ionicons name="sparkles-outline" size={16} color={theme.colors.brandForest} />
            <View style={styles.previewNoticeContent}>
              <Text style={styles.previewNoticeText}>
                Trajeto sugerido a partir do seu ponto de partida
              </Text>
              {previewData && (
                <Text style={styles.previewNoticeSubtext}>
                  Distância estimada: {(previewData.distance_m / 1000).toFixed(1)} km • Tempo: ~{Math.round(previewData.duration_s / 60)} min
                </Text>
              )}
            </View>
          </View>
        )}

        <RouteMapPreview
          routeId={routeId}
          originId={isCustomLocation ? undefined : effectiveOrigin}
          customGeometry={customGeometry}
          customBounds={customBounds}
          customPins={isCustomLocation ? previewData?.pins : undefined}
          customLegend={isCustomLocation ? previewData?.legend : undefined}
          customCityBounds={isCustomLocation ? previewData?.city_bounds : undefined}
          isCustomLocation={isCustomLocation}
          onExpand={(selectedActorId) => {
            if (isCustomLocation && previewData && queryClient) {
              queryClient.setQueryData(queryKeys.routes.ephemeralPreview(routeId), {
                previewData,
                originType: originId || MY_LOCATION_ORIGIN_ID,
              });
            }
            router.push(routePath(routeId, 'map', isCustomLocation ? undefined : effectiveOrigin, selectedActorId ?? actorId));
          }}
        />

        <LocalCatalogPreview
          routeId={routeId}
          originId={isCustomLocation ? undefined : effectiveOrigin}
          onOpenActor={(selectedActorId) =>
            router.push(`/actor/${encodeURIComponent(selectedActorId)}`)
          }
          onOpenCatalog={(category) =>
            router.push(routePath(routeId, 'catalog', isCustomLocation ? undefined : effectiveOrigin, actorId, category))
          }
        />

        {/* Start Trip CTA */}
        <TouchableOpacity
          style={[
            styles.startTripButton,
            {
              backgroundColor: theme.colors.brandForest,
              borderColor: theme.isHighContrast ? theme.colors.brandDeep : 'transparent',
              borderWidth: theme.isHighContrast ? 2 : 0,
            },
          ]}
          onPress={handleStartTrip}
          disabled={isStartingTrip}
          {...makeAccessibleButton(
            'Registrar início de viagem nesta rota',
            'Inicia a viagem e registra o passeio no histórico do seu perfil'
          )}
        >
          {isStartingTrip ? (
            <ActivityIndicator size="small" color={theme.colors.surfaceWhite} />
          ) : (
            <>
              <Ionicons name="play-circle-outline" size={20} color={theme.colors.surfaceWhite} />
              <Text style={[styles.startTripText, { color: theme.colors.surfaceWhite }]}>
                Registrar Início de Viagem
              </Text>
            </>
          )}
        </TouchableOpacity>

        {/* Route Alerts Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Alertas da Rota</Text>
          {alerts.isPending ? (
            <LoadingView message="Carregando alertas..." />
          ) : alerts.isError ? (
            <ErrorStateView
              message="Erro ao carregar alertas."
              onRetry={() => void alerts.refetch()}
            />
          ) : alerts.data && alerts.data.length > 0 ? (
            <View style={styles.alertsContainer}>
              {alerts.data.map((alert) => {
                let alertColor: string = theme.colors.brandForest;
                let alertBg: string = 'rgba(51, 96, 30, 0.08)';
                let alertIcon: keyof typeof Ionicons.glyphMap = 'information-circle-outline';

                if (alert.severity === 'warning') {
                  alertColor = theme.colors.brandSun;
                  alertBg = 'rgba(217, 119, 6, 0.1)';
                  alertIcon = 'warning-outline';
                } else if (alert.severity === 'critical') {
                  alertColor = theme.colors.error;
                  alertBg = 'rgba(220, 38, 38, 0.1)';
                  alertIcon = 'alert-circle-outline';
                }

                return (
                  <View key={alert.id} style={[styles.alertCard, { backgroundColor: alertBg }]}>
                    <Ionicons name={alertIcon} size={20} color={alertColor} />
                    <View style={styles.alertTextWrapper}>
                      <Text style={[styles.alertTitle, { color: alertColor }]}>
                        {alert.title}
                      </Text>
                      <Text style={styles.alertMessage}>{alert.message}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          ) : (
            <View style={styles.emptyAlertsCard}>
              <Ionicons name="checkmark-circle-outline" size={18} color={theme.colors.brandForest} />
              <Text style={styles.emptyAlertsText}>Nenhum alerta ativo no momento.</Text>
            </View>
          )}
        </View>

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.surfaceBackground,
  },
  content: {
    width: '100%',
    maxWidth: '100%',
    overflow: 'hidden',
    padding: theme.spacing.marginMobile,
    paddingBottom: 32,
    gap: 16,
  },
  heroSection: {
    gap: 4,
  },
  heroSectionWithImage: {
    height: 300,
    backgroundColor: theme.colors.surfaceBackground,
    overflow: 'hidden',
  },
  heroImage: {
    borderRadius: theme.radii.xl,
    ...StyleSheet.absoluteFillObject,
    width: '100%',
    height: '100%',
  },
  heroOverlay: {
    gap: 4,
    backgroundColor: 'rgba(8, 18, 5, 0.36)',
    padding: theme.spacing.marginMobile,
    minHeight: 150,
  },
  pindobalHeroStack: {
    position: 'relative',
  },
  originSelectorOverlay: {
    marginTop: -105,
    paddingHorizontal: 28,
    zIndex: 1,
  },
  heroBottomGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 118,
  },
  titleOnImage: {
    color: theme.colors.surfaceWhite,
    textShadowColor: 'rgba(0, 0, 0, 0.60)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  subtitleOnImage: {
    color: 'rgba(255, 255, 255, 0.92)',
    textShadowColor: 'rgba(0, 0, 0, 0.55)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  descriptionOnImage: {
    color: 'rgba(255, 255, 255, 0.94)',
    textShadowColor: 'rgba(0, 0, 0, 0.55)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  title: {
    ...theme.typography.headlineLg,
    color: theme.colors.brandDeep,
  },
  subtitle: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '700',
  },
  description: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurfaceVariant,
    marginTop: 4,
    lineHeight: 22,
  },
  previewNoticeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(51, 96, 30, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.brandForest,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: theme.radii.md,
  },
  previewNoticeContent: {
    flex: 1,
  },
  previewNoticeText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '700',
    fontSize: 12,
  },
  previewNoticeSubtext: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 11,
    marginTop: 2,
  },
  section: {
    gap: 8,
  },
  sectionTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandForest,
  },
  startTripButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: theme.radii.full,
    gap: 8,
    marginVertical: 4,
    ...theme.shadows.card,
  },
  startTripText: {
    ...theme.typography.labelMd,
    fontWeight: '700',
  },
  alertsContainer: {
    gap: 8,
  },
  alertCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
    borderRadius: theme.radii.md,
    gap: 10,
  },
  alertTextWrapper: {
    flex: 1,
  },
  alertTitle: {
    ...theme.typography.labelMd,
    fontWeight: '700',
    marginBottom: 2,
  },
  alertMessage: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 12,
    lineHeight: 16,
  },
  emptyAlertsCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: theme.colors.surfaceContainerLow,
    padding: 12,
    borderRadius: theme.radii.md,
  },
  emptyAlertsText: {
    ...theme.typography.bodySm,
    color: theme.colors.brandForest,
  },
  notFoundBackButton: {
    alignSelf: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  notFoundBackText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandForest,
    fontWeight: '700',
  },
});
