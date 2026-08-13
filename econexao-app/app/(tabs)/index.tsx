import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppHeader } from '../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../src/components/common/UIStateViews';
import { RouteCard } from '../../src/components/routes/RouteCard';
import { useApp } from '../../src/hooks/useApp';
import { useAuth } from '../../src/hooks/useAuth';
import { useRegionsQuery, useRoutesQuery } from '../../src/hooks/queries';
import { useOptimisticFavoriteRoute } from '../../src/hooks/useOptimisticFavoriteRoute';
import { theme } from '../../src/theme/theme';
import { makeAccessibleButton } from '../../src/utils/accessibility';

export default function HomeScreen() {
  const router = useRouter();
  const { state } = useApp();
  const { user } = useAuth();
  const regionsQuery = useRegionsQuery();

  const activeRegionId = state.activeRegionId ?? regionsQuery.data?.[0]?.id;
  const hasNoRegions = regionsQuery.isSuccess && !activeRegionId;

  const featuredQuery = useRoutesQuery(activeRegionId, { limit: 5 });
  const savedQuery = useRoutesQuery(activeRegionId, { saved: true }, user?.id);

  const { toggleFavorite } = useOptimisticFavoriteRoute();

  const savedRouteIds = new Set(savedQuery.data?.data.map((r) => r.id));

  return (
    <View style={styles.container}>
      <AppHeader />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.heroSection}>
          <Text style={styles.heroTitle}>Conecte-se à oferta real da Amazônia.</Text>
          <Text style={styles.heroSubtitle}>
            Descubra rotas comunitárias, iniciativas sustentáveis e atores locais com dados verificados.
          </Text>
          <TouchableOpacity
            style={styles.ctaButton}
            onPress={() => router.push('/(tabs)/routes')}
            {...makeAccessibleButton('Descobrir rotas', 'Navega para a lista completa de rotas')}
          >
            <Text style={styles.ctaButtonText}>Descobrir Rotas</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Rotas em Destaque</Text>
          </View>
          {regionsQuery.isPending ? (
            <LoadingView message="Carregando regiões..." />
          ) : regionsQuery.isError ? (
            <ErrorStateView
              message="Não foi possível carregar as regiões disponíveis."
              onRetry={() => void regionsQuery.refetch()}
            />
          ) : hasNoRegions ? (
            <EmptyStateView
              title="Nenhuma região disponível"
              message="O ambiente ainda não possui regiões cadastradas."
            />
          ) : featuredQuery.isPending ? (
            <LoadingView message="Carregando rotas em destaque..." />
          ) : featuredQuery.isError ? (
            <ErrorStateView
              message="Não foi possível carregar as rotas em destaque."
              onRetry={() => void featuredQuery.refetch()}
            />
          ) : featuredQuery.data?.data.length ? (
            featuredQuery.data.data.map((route) => {
              const isFav = savedRouteIds.has(route.id);
              return (
                <RouteCard
                  key={route.id}
                  route={route}
                  isFavorite={isFav}
                  onPress={() => router.push(`/route/${route.id}`)}
                  onToggleFavorite={() => toggleFavorite(route.id, isFav)}
                />
              );
            })
          ) : (
            <EmptyStateView
              title="Nenhuma rota em destaque"
              message="Não há rotas cadastradas para a região selecionada."
            />
          )}
        </View>

        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Rotas Salvas</Text>
          </View>
          {regionsQuery.isPending ? (
            <LoadingView message="Carregando regiões..." />
          ) : regionsQuery.isError ? (
            <ErrorStateView
              message="Não foi possível carregar as regiões disponíveis."
              onRetry={() => void regionsQuery.refetch()}
            />
          ) : hasNoRegions ? (
            <EmptyStateView
              title="Nenhuma região disponível"
              message="Cadastre uma região para explorar e salvar rotas."
            />
          ) : savedQuery.isPending ? (
            <LoadingView message="Carregando rotas salvas..." />
          ) : savedQuery.isError ? (
            <ErrorStateView
              message="Não foi possível carregar suas rotas salvas."
              onRetry={() => void savedQuery.refetch()}
            />
          ) : savedQuery.data?.data.length ? (
            savedQuery.data.data.map((route) => (
              <RouteCard
                key={route.id}
                route={route}
                isFavorite={true}
                onPress={() => router.push(`/route/${route.id}`)}
                onToggleFavorite={() => toggleFavorite(route.id, true)}
              />
            ))
          ) : (
            <EmptyStateView
              title="Nenhuma rota salva"
              message="Explore as rotas e toque no coração para salvar seus destinos preferidos."
            />
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
    padding: theme.spacing.marginMobile,
    gap: 24,
    paddingBottom: 40,
  },
  heroSection: {
    gap: 12,
    paddingVertical: 12,
  },
  heroTitle: {
    ...theme.typography.displayLg,
    color: theme.colors.brandDeep,
  },
  heroSubtitle: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurfaceVariant,
  },
  ctaButton: {
    backgroundColor: theme.colors.brandForest,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: theme.radii.full,
    alignItems: 'center',
    marginTop: 8,
  },
  ctaButtonText: {
    ...theme.typography.titleMd,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
  section: {
    gap: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    ...theme.typography.headlineMd,
    color: theme.colors.brandDeep,
  },
});
