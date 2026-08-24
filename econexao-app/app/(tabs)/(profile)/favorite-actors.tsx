import React from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';

import { ActorCard } from '../../../src/components/catalog/ActorCard';
import { AppHeader } from '../../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { useMyFavoriteActorsQuery } from '../../../src/hooks/queries';
import { useOptimisticFavoriteActor } from '../../../src/hooks/useOptimisticFavoriteActor';
import { useAuth } from '../../../src/hooks/useAuth';
import { theme } from '../../../src/theme/theme';

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
          favActors.data.map((actorSummary) => (
              <ActorCard
                key={actorSummary.id}
                actor={actorSummary}
                isFavorite={true}
                onToggleFavorite={() => toggleFavorite(actorSummary, true)}
                onPress={() => router.push(`/actor/${actorSummary.id}`)}
              />
          ))
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
