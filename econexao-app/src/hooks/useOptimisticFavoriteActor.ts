import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';
import { apiClient } from '../api/client';
import { queryKeys } from '../api/queryKeys';

interface FavoriteActorVariables {
  actorId: string;
  isFavorite: boolean;
}

export function useOptimisticFavoriteActor() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async ({ actorId, isFavorite }: FavoriteActorVariables) => {
      if (isFavorite) {
        return apiClient.addFavoriteActor(actorId);
      } else {
        return apiClient.removeFavoriteActor(actorId);
      }
    },
    onMutate: async ({ actorId, isFavorite }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.routes.all() });
      await queryClient.cancelQueries({ queryKey: queryKeys.favoriteActors() });

      const previousRouteQueries = queryClient.getQueriesData({ queryKey: queryKeys.routes.all() });
      const previousFavoriteQueries = queryClient.getQueriesData({ queryKey: queryKeys.favoriteActors() });

      AccessibilityInfo.announceForAccessibility(
        isFavorite ? 'Ator salvo nos favoritos.' : 'Ator removido dos favoritos.'
      );

      return { previousRouteQueries, previousFavoriteQueries };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousRouteQueries) {
        context.previousRouteQueries.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      if (context?.previousFavoriteQueries) {
        context.previousFavoriteQueries.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      AccessibilityInfo.announceForAccessibility(
        'Erro ao atualizar favorito do ator. Alteração desfeita.'
      );
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.routes.all() });
      void queryClient.invalidateQueries({ queryKey: queryKeys.favoriteActors() });
    },
  });

  const toggleFavorite = (actorId: string, currentIsFavorite: boolean) => {
    if (mutation.isPending) return;
    mutation.mutate({ actorId, isFavorite: !currentIsFavorite });
  };

  return {
    toggleFavorite,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
    mutate: mutation.mutate,
  };
}
