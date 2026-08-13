import React from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppHeader } from '../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../src/components/common/UIStateViews';
import { RouteCard } from '../../src/components/routes/RouteCard';
import { useMyFavoriteRoutesQuery } from '../../src/hooks/queries';
import { useAuth } from '../../src/hooks/useAuth';
import { theme } from '../../src/theme/theme';

export default function FavoriteRoutesScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const favRoutes = useMyFavoriteRoutesQuery(user?.id);

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title="Rotas Salvas" />

      <ScrollView contentContainerStyle={styles.content}>
        {favRoutes.isPending ? (
          <LoadingView message="Carregando rotas salvas..." />
        ) : favRoutes.isError ? (
          <ErrorStateView
            title="Erro ao carregar favoritos"
            message="Não foi possível obter suas rotas salvas no momento."
            onRetry={() => void favRoutes.refetch()}
          />
        ) : favRoutes.data?.length ? (
          favRoutes.data.map((route) => (
            <RouteCard
              key={route.id}
              route={route}
              onPress={() => router.push(`/route/${route.id}`)}
              isFavorite={true}
            />
          ))
        ) : (
          <EmptyStateView
            title="Nenhuma rota salva"
            message="Você ainda não salvou nenhuma rota nos seus favoritos."
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
