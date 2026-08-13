import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';
import { apiClient } from '../api/client';
import { queryKeys } from '../api/queryKeys';

interface FavoriteRouteVariables {
  routeId: string;
  isFavorite: boolean;
}

export function useOptimisticFavoriteRoute() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async ({ routeId, isFavorite }: FavoriteRouteVariables) => {
      if (isFavorite) {
        return apiClient.addFavoriteRoute(routeId);
      } else {
        return apiClient.removeFavoriteRoute(routeId);
      }
    },
    onMutate: async ({ routeId, isFavorite }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.routes.all() });

      const previousQueries = queryClient.getQueriesData({ queryKey: queryKeys.routes.all() });

      AccessibilityInfo.announceForAccessibility(
        isFavorite ? 'Rota salva nos favoritos.' : 'Rota removida dos favoritos.'
      );

      return { previousQueries };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousQueries) {
        context.previousQueries.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      AccessibilityInfo.announceForAccessibility(
        'Erro ao atualizar favorito. Alteração desfeita.'
      );
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.routes.all() });
    },
  });

  const toggleFavorite = (routeId: string, currentIsFavorite: boolean) => {
    if (mutation.isPending) return;
    mutation.mutate({ routeId, isFavorite: !currentIsFavorite });
  };

  return {
    toggleFavorite,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
    mutate: mutation.mutate,
  };
}
