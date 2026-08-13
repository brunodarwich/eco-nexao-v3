import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { ActorCard } from '../../../src/components/catalog/ActorCard';
import { CategoryFilters } from '../../../src/components/catalog/CategoryFilters';
import { AppHeader } from '../../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { SearchInput } from '../../../src/components/common/SearchInput';
import { useActorCategoriesQuery, useRouteActorsQuery } from '../../../src/hooks/queries';
import { useOptimisticFavoriteActor } from '../../../src/hooks/useOptimisticFavoriteActor';
import { theme } from '../../../src/theme/theme';
import type { ActorSummary } from '../../../src/api/types';
import type { Actor, CategorySegment } from '../../../src/types';

export default function CatalogScreen() {
  const router = useRouter();
  const { routeId = '', originId, actorId } = useLocalSearchParams<{
    routeId: string;
    originId?: string;
    actorId?: string;
  }>();

  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [favoriteMap, setFavoriteMap] = useState<Record<string, boolean>>({});

  const { toggleFavorite } = useOptimisticFavoriteActor();

  const handleToggleFav = (id: string) => {
    const current = Boolean(favoriteMap[id]);
    setFavoriteMap((prev) => ({ ...prev, [id]: !current }));
    toggleFavorite(id, current);
  };


  const categories = useActorCategoriesQuery();
  const actors = useRouteActorsQuery(routeId, {
    q: q || undefined,
    category: category || undefined,
    origin_id: originId,
  });

  const mapActorSummaryToActor = (summary: ActorSummary): Actor => {
    return {
      id: summary.id,
      name: summary.name,
      segment: (summary.category_slug as CategorySegment) || 'hospedagem',
      subCategory: summary.category_label || 'Ponto de Apoio',
      group: 'Inventário SEMTUR',
      address: summary.address ?? 'Endereço local',
      city: 'Belterra',
      state: 'PA',
      phone: '',
      rating: summary.google_rating ?? 4.5,
      reviewCount: 8,
      greenBadge: summary.green_badge_status === 'verified',
      accessibilityFeatures: [],
      imageUrl: require('../../../assets/images/pousada_canto_floresta.jpg'),
      coordinate: {
        xPercentage: 50,
        yPercentage: 50,
        latitude: summary.latitude ?? undefined,
        longitude: summary.longitude ?? undefined,
      },
      description: `Categoria: ${summary.category_label}`,
    };
  };

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
        {actors.isPending ? (
          <LoadingView message="Carregando catálogo..." />
        ) : actors.isError ? (
          <ErrorStateView
            title="Erro ao carregar catálogo"
            message="Não foi possível obter a lista de atores para esta rota."
            onRetry={() => void actors.refetch()}
          />
        ) : actors.data?.data.length ? (
          actors.data.data.map((summary) => {
            const actorObj = mapActorSummaryToActor(summary);
            return (
              <ActorCard
                key={summary.id}
                actor={actorObj}
                focusOnMount={summary.id === actorId}
                isFavorite={Boolean(favoriteMap[summary.id])}
                onToggleFavorite={() => handleToggleFav(summary.id)}
                onPress={() => {
                  const query = new URLSearchParams();
                  if (originId) query.set('originId', originId);
                  const suffix = query.toString();
                  router.push(`/actor/${encodeURIComponent(summary.id)}${suffix ? `?${suffix}` : ''}`);
                }}
              />
            );
          })
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
});
