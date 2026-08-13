import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppHeader } from '../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../src/components/common/UIStateViews';
import { FilterChip } from '../../src/components/common/FilterChip';
import { SearchInput } from '../../src/components/common/SearchInput';
import { RouteCard } from '../../src/components/routes/RouteCard';
import { useApp } from '../../src/hooks/useApp';
import { useAuth } from '../../src/hooks/useAuth';
import { useRegionsQuery, useRoutesQuery } from '../../src/hooks/queries';
import { useOptimisticFavoriteRoute } from '../../src/hooks/useOptimisticFavoriteRoute';
import { theme } from '../../src/theme/theme';

type FilterType = 'all' | 'saved' | 'verified';

export default function RoutesScreen() {
  const router = useRouter();
  const { state } = useApp();
  const { user } = useAuth();
  const regionsQuery = useRegionsQuery();

  const [filter, setFilter] = useState<FilterType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 350);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const activeRegionId = state.activeRegionId ?? regionsQuery.data?.[0]?.id;
  const hasNoRegions = regionsQuery.isSuccess && !activeRegionId;

  const routesQuery = useRoutesQuery(
    activeRegionId,
    {
      q: debouncedSearch || undefined,
      saved: filter === 'saved' || undefined,
      verified: filter === 'verified' || undefined,
    },
    user?.id
  );

  const savedRoutesQuery = useRoutesQuery(activeRegionId, { saved: true }, user?.id);
  const { toggleFavorite } = useOptimisticFavoriteRoute();

  const savedRouteIds = new Set(savedRoutesQuery.data?.data.map((r) => r.id));

  const handleResetFilters = () => {
    setSearchQuery('');
    setDebouncedSearch('');
    setFilter('all');
  };

  return (
    <View style={styles.container}>
      <AppHeader />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Rotas da Região</Text>

        <SearchInput
          value={searchQuery}
          onChangeText={setSearchQuery}
          onClear={() => setSearchQuery('')}
          placeholder="Buscar por nome ou município..."
        />

        <View style={styles.filters}>
          <FilterChip
            label="Todas"
            isSelected={filter === 'all'}
            onPress={() => setFilter('all')}
          />
          <FilterChip
            label="Salvas"
            isSelected={filter === 'saved'}
            onPress={() => setFilter('saved')}
          />
          <FilterChip
            label="Verificadas"
            isSelected={filter === 'verified'}
            onPress={() => setFilter('verified')}
          />
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
        ) : routesQuery.isPending ? (
          <LoadingView message="Carregando rotas..." />
        ) : routesQuery.isError ? (
          <ErrorStateView
            message="Não foi possível carregar a lista de rotas."
            onRetry={() => void routesQuery.refetch()}
          />
        ) : routesQuery.data?.data.length ? (
          routesQuery.data.data.map((route) => {
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
            title="Nenhuma rota encontrada"
            message="Não encontramos rotas com os filtros selecionados."
            onReset={searchQuery || filter !== 'all' ? handleResetFilters : undefined}
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
  title: {
    ...theme.typography.headlineLg,
    color: theme.colors.brandDeep,
  },
  filters: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
  },
});
