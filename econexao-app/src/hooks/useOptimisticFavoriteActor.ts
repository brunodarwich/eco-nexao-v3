import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';
import { apiClient } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import type { ActorListEnvelope, ActorDetailEnvelope, ActorSummary } from '../api/types';

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

      // Atualiza listagens de atores em rotas (simples ou infinitas)
      queryClient.setQueriesData<any>(
        { queryKey: ['routes', 'actors'] },
        (old: any) => {
          if (!old) return old;
          if (Array.isArray(old.pages)) {
            return {
              ...old,
              pages: old.pages.map((page: ActorListEnvelope) => ({
                ...page,
                data: (page.data || []).map((actor: ActorSummary) =>
                  actor.id === actorId ? { ...actor, is_favorite: isFavorite } : actor
                ),
              })),
            };
          }
          if (Array.isArray(old.data)) {
            return {
              ...old,
              data: old.data.map((actor: ActorSummary) =>
                actor.id === actorId ? { ...actor, is_favorite: isFavorite } : actor
              ),
            };
          }
          return old;
        }
      );

      // Atualiza detalhe do ator se estiver em cache
      queryClient.setQueriesData<ActorDetailEnvelope>(
        { queryKey: queryKeys.actorDetail(actorId) },
        (old) => {
          if (!old?.data) return old;
          return {
            ...old,
            data: { ...old.data, is_favorite: isFavorite },
          };
        }
      );

      return { previousRouteQueries, previousFavoriteQueries };
    },
    onSuccess: (_data, { isFavorite }) => {
      AccessibilityInfo.announceForAccessibility(
        isFavorite ? 'Ator salvo nos favoritos com sucesso.' : 'Ator removido dos favoritos.'
      );
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
        'Falha ao atualizar favorito do ator. Alteração desfeita.'
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

