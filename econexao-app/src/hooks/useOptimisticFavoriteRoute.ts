import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';
import { apiClient } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import type { RouteListEnvelope, RouteDetailEnvelope, RouteSummary } from '../api/types';
import { useAuth } from './useAuth';

interface FavoriteRouteVariables {
  route?: RouteSummary | string;
  routeId?: string;
  isFavorite: boolean;
}

export function useOptimisticFavoriteRoute() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const favoritesKey = queryKeys.myFavoriteRoutes(user?.id);

  const mutation = useMutation({
    mutationFn: async ({ route, routeId: legacyRouteId, isFavorite }: FavoriteRouteVariables) => {
      const routeId = legacyRouteId ?? (typeof route === 'string' ? route : route?.id);
      if (!routeId) throw new Error('Rota inválida para favorito.');
      if (isFavorite) {
        return apiClient.addFavoriteRoute(routeId);
      } else {
        return apiClient.removeFavoriteRoute(routeId);
      }
    },
    onMutate: async ({ route, routeId: legacyRouteId, isFavorite }) => {
      const routeId = legacyRouteId ?? (typeof route === 'string' ? route : route?.id);
      if (!routeId) return {};
      await queryClient.cancelQueries({ queryKey: queryKeys.routes.all() });
      await queryClient.cancelQueries({ queryKey: favoritesKey });

      const previousRoutesQueries = queryClient.getQueriesData({ queryKey: queryKeys.routes.all() });
      const previousFavoriteQueries = queryClient.getQueriesData({ queryKey: favoritesKey });

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

      queryClient.setQueryData<RouteListEnvelope>(favoritesKey, (old) => {
        const current = old ?? { data: [], meta: { total: 0, limit: 20 } };
        const existed = current.data.some((item) => item.id === routeId);
        const remaining = current.data.filter((item) => item.id !== routeId);
        const delta = isFavorite && !existed ? 1 : !isFavorite && existed ? -1 : 0;
        return {
          ...current,
          data: isFavorite && route && typeof route !== 'string' ? [{ ...route, is_favorite: true } as RouteSummary, ...remaining] : remaining,
          meta: { ...current.meta, total: Math.max(0, current.meta.total + delta) },
        };
      });

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
      void queryClient.invalidateQueries({ queryKey: favoritesKey });
    },
  });

  const toggleFavorite = (route: RouteSummary | string, currentIsFavorite: boolean) => {
    if (mutation.isPending) return;
    mutation.mutate({ route, isFavorite: !currentIsFavorite });
  };

  return {
    toggleFavorite,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
    mutate: mutation.mutate,
  };
}
