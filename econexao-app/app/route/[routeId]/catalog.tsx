import React, { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { ActorCard } from '../../../src/components/catalog/ActorCard';
import { CategoryFilters } from '../../../src/components/catalog/CategoryFilters';
import { AppHeader } from '../../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { SearchInput } from '../../../src/components/common/SearchInput';
import { useActorCategoriesQuery, useInfiniteRouteActorsQuery } from '../../../src/hooks/queries';
import { useOptimisticFavoriteActor } from '../../../src/hooks/useOptimisticFavoriteActor';
import { theme } from '../../../src/theme/theme';
import type { ActorSummary } from '../../../src/api/types';

export default function CatalogScreen() {
  const router = useRouter();
  const { routeId = '', originId, actorId } = useLocalSearchParams<{
    routeId: string;
    originId?: string;
    actorId?: string;
  }>();

  const [q, setQ] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [category, setCategory] = useState('');
  const [favoriteMap, setFavoriteMap] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQ(q);
    }, 350);
    return () => clearTimeout(timer);
  }, [q]);

  const { toggleFavorite } = useOptimisticFavoriteActor();

  const handleToggleFav = (id: string, currentStatus?: boolean) => {
    const current = currentStatus !== undefined ? currentStatus : Boolean(favoriteMap[id]);
    setFavoriteMap((prev) => ({ ...prev, [id]: !current }));
    toggleFavorite(id, current);
  };

  const categories = useActorCategoriesQuery();
  const actorsQuery = useInfiniteRouteActorsQuery(routeId, {
    q: debouncedQ || undefined,
    category: category || undefined,
    origin_id: originId,
  });

  const allActors: ActorSummary[] = actorsQuery.data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title="Catálogo de Atores" />

      <View style={styles.headerControls}>
        <SearchInput
          value={q}
          onChangeText={setQ}
          onClear={() => setQ('')}
          placeholder="Buscar empreendimentos na rota..."
        />
        <CategoryFilters
          categories={categories.data ?? []}
          selectedCategory={category}
          onSelectCategory={setCategory}
        />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {actorsQuery.isPending ? (
          <LoadingView message="Carregando catálogo..." />
        ) : actorsQuery.isError ? (
          <ErrorStateView
            title="Erro ao carregar catálogo"
            message="Não foi possível obter a lista de atores para esta rota."
            onRetry={() => void actorsQuery.refetch()}
          />
        ) : allActors.length > 0 ? (
          <>
            {allActors.map((summary) => {
              const isFav = favoriteMap[summary.id] !== undefined
                ? favoriteMap[summary.id]
                : (summary as any).is_favorite ?? false;

              return (
                <ActorCard
                  key={summary.id}
                  actor={summary}
                  focusOnMount={summary.id === actorId}
                  isFavorite={isFav}
                  onToggleFavorite={() => handleToggleFav(summary.id, isFav)}
                  onPress={() => {
                    const query = new URLSearchParams();
                    if (originId) query.set('originId', originId);
                    const suffix = query.toString();
                    router.push(`/actor/${encodeURIComponent(summary.id)}${suffix ? `?${suffix}` : ''}`);
                  }}
                />
              );
            })}

            {actorsQuery.hasNextPage && (
              <TouchableOpacity
                style={styles.loadMoreButton}
                onPress={() => void actorsQuery.fetchNextPage()}
                disabled={actorsQuery.isFetchingNextPage}
                accessibilityRole="button"
                accessibilityLabel="Carregar mais atores da rota"
              >
                {actorsQuery.isFetchingNextPage ? (
                  <ActivityIndicator size="small" color="#059669" />
                ) : (
                  <Text style={styles.loadMoreText}>Carregar Mais Estabelecimentos</Text>
                )}
              </TouchableOpacity>
            )}
          </>
        ) : (
          <EmptyStateView
            title="Nenhum ator encontrado"
            message="Tente ajustar os filtros ou a busca para visualizar outros resultados."
            onReset={() => {
              setQ('');
              setCategory('');
            }}
            resetLabel="Limpar filtros"
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
  headerControls: {
    backgroundColor: theme.colors.surfaceWhite,
    paddingHorizontal: theme.spacing.marginMobile,
    paddingTop: 8,
    paddingBottom: 8,
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(117, 155, 113, 0.15)',
  },
  content: {
    padding: theme.spacing.marginMobile,
    paddingBottom: 32,
    gap: 12,
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

