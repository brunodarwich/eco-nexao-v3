import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';
import { apiClient } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import type { ActorListEnvelope, ActorSummary } from '../api/types';
import { useAuth } from './useAuth';

interface FavoriteActorVariables {
  actor: ActorSummary;
  isFavorite: boolean;
}

export function useOptimisticFavoriteActor() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const favoritesKey = queryKeys.favoriteActors(user?.id);

  const mutation = useMutation({
    mutationFn: async ({ actor, isFavorite }: FavoriteActorVariables) => {
      if (isFavorite) {
        return apiClient.addFavoriteActor(actor.id);
      } else {
        return apiClient.removeFavoriteActor(actor.id);
      }
    },
    onMutate: async ({ actor, isFavorite }) => {
      await queryClient.cancelQueries({ queryKey: favoritesKey });
      const previousFavorites = queryClient.getQueryData<ActorListEnvelope>(favoritesKey);

      queryClient.setQueryData<ActorListEnvelope>(favoritesKey, (old) => {
        const current = old ?? { data: [], meta: { total: 0, limit: 20 } };
        const wasFavorite = current.data.some((favorite) => favorite.id === actor.id);
        const withoutActor = current.data.filter((favorite) => favorite.id !== actor.id);
        const totalDelta = isFavorite && !wasFavorite ? 1 : !isFavorite && wasFavorite ? -1 : 0;
        return {
          ...current,
          data: isFavorite ? [actor, ...withoutActor] : withoutActor,
          meta: {
            ...current.meta,
            total: Math.max(0, current.meta.total + totalDelta),
          },
        };
      });

      return { previousFavorites };
    },
    onSuccess: (_data, { isFavorite }) => {
      AccessibilityInfo.announceForAccessibility(
        isFavorite ? 'Ator salvo nos favoritos com sucesso.' : 'Ator removido dos favoritos.'
      );
    },
    onError: (_err, _variables, context) => {
      if (context?.previousFavorites) {
        queryClient.setQueryData(favoritesKey, context.previousFavorites);
      } else {
        queryClient.removeQueries({ queryKey: favoritesKey, exact: true });
      }
      AccessibilityInfo.announceForAccessibility(
        'Falha ao atualizar favorito do ator. Alteração desfeita.'
      );
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: favoritesKey });
    },
  });

  const toggleFavorite = (actor: ActorSummary, currentIsFavorite: boolean) => {
    if (mutation.isPending) return;
    mutation.mutate({ actor, isFavorite: !currentIsFavorite });
  };

  return {
    toggleFavorite,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
    mutate: mutation.mutate,
  };
}
