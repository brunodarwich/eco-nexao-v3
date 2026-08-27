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
      await queryClient.cancelQueries({ queryKey: queryKeys.routes.all() });
      await queryClient.cancelQueries({ queryKey: queryKeys.actorDetail(actor.id) });
      await queryClient.cancelQueries({ queryKey: favoritesKey });
      const previousActorQueries = queryClient.getQueriesData({ queryKey: queryKeys.routes.all() });
      const previousActorDetail = queryClient.getQueryData(queryKeys.actorDetail(actor.id));
      const previousFavorites = queryClient.getQueryData<ActorListEnvelope>(favoritesKey);

      queryClient.setQueriesData<any>({ queryKey: queryKeys.routes.all() }, (old: any) => {
        if (!old) return old;
        const update = (item: ActorSummary) => item.id === actor.id ? { ...item, is_favorite: isFavorite } : item;
        if (Array.isArray(old.pages)) return { ...old, pages: old.pages.map((page: ActorListEnvelope) => ({ ...page, data: page.data.map(update) })) };
        if (Array.isArray(old.data)) return { ...old, data: old.data.map(update) };
        return old;
      });
      queryClient.setQueryData<any>(queryKeys.actorDetail(actor.id), (old: any) =>
        old?.data ? { ...old, data: { ...old.data, is_favorite: isFavorite } } : old
      );

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

      return { previousFavorites, previousActorQueries, previousActorDetail };
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
      context?.previousActorQueries?.forEach(([queryKey, data]) => queryClient.setQueryData(queryKey, data));
      if (context?.previousActorDetail !== undefined) {
        queryClient.setQueryData(queryKeys.actorDetail(_variables.actor.id), context.previousActorDetail);
      }
      AccessibilityInfo.announceForAccessibility(
        'Falha ao atualizar favorito do ator. Alteração desfeita.'
      );
    },
    onSettled: (_data, _error, variables) => {
      void queryClient.invalidateQueries({ queryKey: favoritesKey });
      void queryClient.invalidateQueries({ queryKey: queryKeys.routes.all() });
      void queryClient.invalidateQueries({ queryKey: queryKeys.actorDetail(variables.actor.id) });
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
