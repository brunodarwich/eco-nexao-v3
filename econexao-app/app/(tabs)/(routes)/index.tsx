import React from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { RouteCard } from '../../../src/components/routes/RouteCard';
import { useApp } from '../../../src/hooks/useApp';
import { useAuth } from '../../../src/hooks/useAuth';
import { flattenUniquePages, useInfiniteRoutesQuery, useRegionsQuery, useRoutesQuery } from '../../../src/hooks/queries';
import { useOptimisticFavoriteRoute } from '../../../src/hooks/useOptimisticFavoriteRoute';
import { theme } from '../../../src/theme/theme';
import type { RouteSummary } from '../../../src/api/types';

export default function RoutesScreen() {
  const router = useRouter();
  const { state } = useApp();
  const { user } = useAuth();
  const regionsQuery = useRegionsQuery();

  const activeRegionId = state.activeRegionId ?? regionsQuery.data?.[0]?.id;
  const hasNoRegions = regionsQuery.isSuccess && !activeRegionId;

  const routesQuery = useInfiniteRoutesQuery(
    activeRegionId,
    {},
    user?.id
  );

  const savedRoutesQuery = useRoutesQuery(activeRegionId, { saved: true }, user?.id);
  const { toggleFavorite } = useOptimisticFavoriteRoute();

  const savedRouteIds = new Set(savedRoutesQuery.data?.data?.map((r) => r.id));
  const allRoutes: RouteSummary[] = flattenUniquePages(routesQuery.data?.pages);

  return (
    <View style={styles.container}>
      <AppHeader />
      <ScrollView contentContainerStyle={styles.content}>
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
        ) : routesQuery.isPending ? (
          <LoadingView message="Carregando rotas..." />
        ) : routesQuery.isError && allRoutes.length === 0 ? (
          <ErrorStateView
            message="Não foi possível carregar a lista de rotas."
            onRetry={() => void routesQuery.refetch()}
          />
        ) : allRoutes.length > 0 ? (
          <>
            {allRoutes.map((route) => {
              const isFav =
                (route as RouteSummary & { is_favorite?: boolean }).is_favorite ??
                savedRouteIds.has(route.id);
              return (
                <RouteCard
                  key={route.id}
                  route={route}
                  isFavorite={isFav}
                  onPress={() => router.push(`/route/${route.id}`)}
                  onToggleFavorite={() => toggleFavorite(route, isFav)}
                />
              );
            })}

            {routesQuery.hasNextPage && (
              <TouchableOpacity
                style={styles.loadMoreButton}
                onPress={() => void routesQuery.fetchNextPage()}
                disabled={routesQuery.isFetchingNextPage}
                accessibilityRole="button"
                accessibilityLabel="Carregar mais rotas"
                accessibilityState={{ disabled: routesQuery.isFetchingNextPage, busy: routesQuery.isFetchingNextPage }}
              >
                {routesQuery.isFetchingNextPage ? (
                  <ActivityIndicator size="small" color="#059669" />
                ) : (
                  <Text style={styles.loadMoreText}>Carregar Mais Rotas</Text>
                )}
              </TouchableOpacity>
            )}
            {routesQuery.isError && (
              <ErrorStateView message="Não foi possível carregar mais rotas." onRetry={() => void routesQuery.fetchNextPage()} />
            )}
          </>
        ) : (
          <EmptyStateView
            title="Nenhuma rota encontrada"
            message="Não há rotas cadastradas para a região selecionada."
          />
        )}
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
    gap: 16,
    paddingBottom: 40,
  },
  loadMoreButton: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#059669',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  loadMoreText: {
    color: '#059669',
    fontSize: 14,
    fontWeight: '600',
  },
});
