import type { GetRouteActorsQuery, ListRoutesQuery } from './types';

export const normalizeQueryValue = (value?: string | null) => value?.trim() || undefined;

export const queryKeys = {
  bootstrap: (userId: string) => ['bootstrap', userId] as const,
  regions: () => ['regions'] as const,
  routes: {
    all: () => ['routes'] as const,
    list: (regionId: string | undefined, params: ListRoutesQuery = {}, userId?: string) =>
      [
        'routes',
        'list',
        {
          regionId: normalizeQueryValue(regionId),
          q: normalizeQueryValue(params.q),
          saved: params.saved,
          verified: params.verified,
          cursor: normalizeQueryValue(params.cursor),
          limit: params.limit,
          userId: params.saved ? normalizeQueryValue(userId) : undefined,
        },
      ] as const,
    detail: (routeId: string) => ['routes', 'detail', routeId] as const,
    origins: (routeId: string) => ['routes', 'origins', routeId] as const,
    geometry: (routeId: string, originId: string) =>
      ['routes', 'geometry', routeId, originId] as const,
    alerts: (routeId: string) => ['routes', 'alerts', routeId] as const,
    actors: (routeId: string, params: GetRouteActorsQuery = {}) =>
      [
        'routes',
        'actors',
        routeId,
        {
          q: normalizeQueryValue(params.q),
          category: normalizeQueryValue(params.category),
          originId: normalizeQueryValue(params.origin_id),
          cursor: normalizeQueryValue(params.cursor),
          limit: params.limit,
        },
      ] as const,
    map: (routeId: string, originId?: string) =>
      ['routes', 'map', routeId, normalizeQueryValue(originId)] as const,
  },
  actorCategories: () => ['actor-categories'] as const,
  actorDetail: (actorId: string) => ['actors', 'detail', actorId] as const,
  favoriteActors: (userId?: string) => ['favorite-actors', normalizeQueryValue(userId)] as const,
  myProfile: (userId?: string) => ['me', 'profile', normalizeQueryValue(userId)] as const,
  myTrips: (userId?: string) => ['me', 'trips', normalizeQueryValue(userId)] as const,
  myFavoriteRoutes: (userId?: string) => ['me', 'favorite-routes', normalizeQueryValue(userId)] as const,
  myPreferences: (userId?: string) => ['me', 'preferences', normalizeQueryValue(userId)] as const,
  supportContent: () => ['content', 'support'] as const,
};

