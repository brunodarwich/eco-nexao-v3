import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View, Alert, ActivityIndicator, AccessibilityInfo } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQueryClient } from '@tanstack/react-query';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { LocalCatalogPreview } from '../../../src/components/routes/LocalCatalogPreview';
import { OriginSelector } from '../../../src/components/routes/OriginSelector';
import { RouteMapPreview } from '../../../src/components/routes/RouteMapPreview';
import { useRouteAlertsQuery, useRouteDetailQuery } from '../../../src/hooks/queries';
import { theme, useAppTheme } from '../../../src/theme/theme';

import { makeAccessibleButton } from '../../../src/utils/accessibility';
import { apiClient, ApiClientError } from '../../../src/api/client';
import { queryKeys } from '../../../src/api/queryKeys';
import { AuthContext } from '../../../src/auth/AuthProvider';

const routePath = (
  routeId: string,
  destination: 'map' | 'catalog',
  originId?: string,
  actorId?: string,
  category?: string
) => {
  const query = new URLSearchParams();
  if (originId) query.set('originId', originId);
  if (actorId) query.set('actorId', actorId);
  if (category) query.set('category', category);
  const suffix = query.toString();
  return `/route/${encodeURIComponent(routeId)}/${destination}${suffix ? `?${suffix}` : ''}`;
};

export default function RouteDetailScreen() {
  const router = useRouter();
  const theme = useAppTheme();
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
  const requestedOriginExists = detail.data?.origins.some((origin) => origin.id === originId);
  const effectiveOrigin = requestedOriginExists ? originId : detail.data?.origins[0]?.id;

  useEffect(() => {
    setOriginId(initialOriginId);
  }, [initialOriginId, routeId]);

  const alerts = useRouteAlertsQuery(routeId);

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

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title={route.title} />

      <ScrollView contentContainerStyle={styles.content}>
        {/* Header Hero Section */}
        <View style={styles.heroSection}>
          <Text style={styles.title}>{route.title}</Text>
          <Text style={styles.subtitle}>
            {route.city}, {route.state_code}
            {route.is_verified && ' • Rota Verificada'}
          </Text>
          <Text style={styles.description}>{route.description ?? route.summary}</Text>
        </View>

        {/* Origin Selector */}
        {route.origins && route.origins.length > 0 && (
          <OriginSelector
            origins={route.origins}
            selectedOriginId={effectiveOrigin}
            onSelectOrigin={(id) => setOriginId(id)}
          />
        )}

        <RouteMapPreview
          routeId={routeId}
          originId={effectiveOrigin}
          onExpand={(selectedActorId) =>
            router.push(routePath(routeId, 'map', effectiveOrigin, selectedActorId ?? actorId))
          }
        />

        <LocalCatalogPreview
          routeId={routeId}
          originId={effectiveOrigin}
          onOpenActor={(selectedActorId) =>
            router.push(`/actor/${encodeURIComponent(selectedActorId)}`)
          }
          onOpenCatalog={(category) =>
            router.push(routePath(routeId, 'catalog', effectiveOrigin, actorId, category))
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
