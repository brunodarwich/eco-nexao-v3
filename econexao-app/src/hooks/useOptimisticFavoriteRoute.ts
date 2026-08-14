import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';
import { apiClient } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import type { RouteListEnvelope, RouteDetailEnvelope, RouteSummary } from '../api/types';

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
      await queryClient.cancelQueries({ queryKey: queryKeys.myFavoriteRoutes() });

      const previousRoutesQueries = queryClient.getQueriesData({ queryKey: queryKeys.routes.all() });
      const previousFavoriteQueries = queryClient.getQueriesData({ queryKey: queryKeys.myFavoriteRoutes() });

      // Atualiza otimista todas as listagens de rotas no cache (simples ou infinitas)
      queryClient.setQueriesData<any>(
        { queryKey: queryKeys.routes.all() },
        (old: any) => {
          if (!old) return old;
          if (Array.isArray(old.pages)) {
            return {
              ...old,
              pages: old.pages.map((page: RouteListEnvelope) => ({
                ...page,
                data: (page.data || []).map((route: RouteSummary) =>
                  route.id === routeId ? { ...route, is_favorite: isFavorite } : route
                ),
              })),
            };
          }
          if (Array.isArray(old.data)) {
            return {
              ...old,
              data: old.data.map((route: RouteSummary) =>
                route.id === routeId ? { ...route, is_favorite: isFavorite } : route
              ),
            };
          }
          return old;
        }
      );

      // Atualiza detalhe da rota se estiver em cache
      queryClient.setQueriesData<RouteDetailEnvelope>(
        { queryKey: queryKeys.routes.detail(routeId) },
        (old) => {
          if (!old?.data) return old;
          return {
            ...old,
            data: { ...old.data, is_favorite: isFavorite },
          };
        }
      );

      return { previousRoutesQueries, previousFavoriteQueries };
    },
    onSuccess: (_data, { isFavorite }) => {
      AccessibilityInfo.announceForAccessibility(
        isFavorite ? 'Rota salva nos favoritos com sucesso.' : 'Rota removida dos favoritos.'
      );
    },
    onError: (_err, _variables, context) => {
      if (context?.previousRoutesQueries) {
        context.previousRoutesQueries.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      if (context?.previousFavoriteQueries) {
        context.previousFavoriteQueries.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      AccessibilityInfo.announceForAccessibility(
        'Falha ao atualizar favorito da rota. Alteração desfeita.'
      );
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.routes.all() });
      void queryClient.invalidateQueries({ queryKey: queryKeys.myFavoriteRoutes() });
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

