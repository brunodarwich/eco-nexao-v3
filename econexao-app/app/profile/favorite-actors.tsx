import React from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';

import { ActorCard } from '../../src/components/catalog/ActorCard';
import { AppHeader } from '../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../src/components/common/UIStateViews';
import { useMyFavoriteActorsQuery } from '../../src/hooks/queries';
import { useOptimisticFavoriteActor } from '../../src/hooks/useOptimisticFavoriteActor';
import { useAuth } from '../../src/hooks/useAuth';
import { theme } from '../../src/theme/theme';
import type { ActorSummary } from '../../src/api/types';
import type { Actor, CategorySegment } from '../../src/types';

export default function FavoriteActorsScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const favActors = useMyFavoriteActorsQuery(user?.id);
  const { toggleFavorite } = useOptimisticFavoriteActor();

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title="Atores Favoritos" />

      <ScrollView contentContainerStyle={styles.content}>
        {favActors.isPending ? (
          <LoadingView message="Carregando atores favoritos..." />
        ) : favActors.isError ? (
          <ErrorStateView
            title="Erro ao carregar atores"
            message="Não foi possível obter seus atores favoritos no momento."
            onRetry={() => void favActors.refetch()}
          />
        ) : favActors.data?.length ? (
          favActors.data.map((actorSummary: ActorSummary) => {
            const actorObj: Actor = {
              id: actorSummary.id,
              name: actorSummary.name,
              segment: (actorSummary.category_slug as CategorySegment) || 'hospedagem',
              subCategory: actorSummary.category_label || 'Atração',
              group: 'Inventário SEMTUR',
              address: actorSummary.address ?? 'Endereço local',
              city: 'Belterra',
              state: 'PA',
              phone: '',
              rating: actorSummary.google_rating ?? 4.5,
              reviewCount: 10,
              greenBadge: actorSummary.green_badge_status === 'verified',
              accessibilityFeatures: [],
              imageUrl: require('../../assets/images/pousada_canto_floresta.jpg'),
              coordinate: { xPercentage: 50, yPercentage: 50 },
              description: `Categoria: ${actorSummary.category_label}`,
            };

            return (
              <ActorCard
                key={actorSummary.id}
                actor={actorObj}
                isFavorite={true}
                onToggleFavorite={() => toggleFavorite(actorSummary.id, true)}
                onPress={() => router.push(`/actor/${actorSummary.id}`)}
              />
            );
          })
        ) : (
          <EmptyStateView
            title="Nenhum ator favorito"
            message="Você ainda não salvou nenhum estabelecimento nos seus favoritos."
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
    gap: 12,
  },
});
