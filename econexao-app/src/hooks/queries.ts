import { infiniteQueryOptions, queryOptions, useInfiniteQuery, useQuery } from '@tanstack/react-query';

import { apiClient } from '../api/client';
import { normalizeQueryValue, queryKeys } from '../api/queryKeys';
import type { GetRouteActorsQuery, GetRouteMapQuery, ListRoutesQuery } from '../api/types';

export const adminQueries = {
  context: (isAuthenticated = true) =>
    queryOptions({
      queryKey: ['admin', 'context'],
      queryFn: ({ signal }) => apiClient.getAdminContext({ signal }),
      select: (envelope) => envelope.data,
      enabled: Boolean(isAuthenticated),
      retry: false,
      meta: { authenticated: true },
    }),
};

export const territorialQueries = {
  bootstrap: (userId: string) =>
    queryOptions({
      queryKey: queryKeys.bootstrap(userId),
      queryFn: () => apiClient.getBootstrap(),
      select: (envelope) => envelope.data,
      enabled: Boolean(userId),
      meta: { authenticated: true },
    }),
  regions: () =>
    queryOptions({
      queryKey: queryKeys.regions(),
      queryFn: () => apiClient.getRegions(),
      select: (envelope) => envelope.data,
      staleTime: 1000 * 60 * 10, // 10 minutes
      gcTime: process.env.NODE_ENV === 'test' ? Infinity : 1000 * 60 * 60, // 1 hour
    }),
  routes: (regionId: string | undefined, params: ListRoutesQuery = {}, userId?: string) => {
    const request = {
      ...params,
      region_id: normalizeQueryValue(regionId),
      q: normalizeQueryValue(params.q),
      cursor: normalizeQueryValue(params.cursor),
    };
    return queryOptions({
      queryKey: queryKeys.routes.list(regionId, request, userId),
      queryFn: ({ signal }) => (signal ? apiClient.getRoutes(request, { signal }) : apiClient.getRoutes(request)),
      enabled: Boolean(regionId) && (!params.saved || Boolean(userId)),
      meta: { authenticated: params.saved === true },
      staleTime: 1000 * 60 * 2, // 2 minutes
    });
  },
  routeDetail: (routeId: string) =>
    queryOptions({
      queryKey: queryKeys.routes.detail(routeId),
      queryFn: () => apiClient.getRouteDetail(routeId),
      select: (e) => e.data,
      enabled: Boolean(routeId),
      staleTime: 1000 * 60 * 5, // 5 minutes
    }),
  routeOrigins: (routeId: string) =>
    queryOptions({ queryKey: queryKeys.routes.origins(routeId), queryFn: () => apiClient.getRouteOrigins(routeId), select: (e) => e.data, enabled: Boolean(routeId) }),
  routeGeometry: (routeId: string, originId: string) =>
    queryOptions({ queryKey: queryKeys.routes.geometry(routeId, originId), queryFn: () => apiClient.getRouteGeometry(routeId, originId), select: (e) => e.data, enabled: Boolean(routeId && originId) }),
  routeAlerts: (routeId: string) =>
    queryOptions({ queryKey: queryKeys.routes.alerts(routeId), queryFn: () => apiClient.getRouteAlerts(routeId), select: (e) => e.data, enabled: Boolean(routeId) }),
  routeActors: (routeId: string, params: GetRouteActorsQuery = {}) => {
    const request = {
      ...params,
      q: normalizeQueryValue(params.q),
      category: normalizeQueryValue(params.category),
      origin_id: normalizeQueryValue(params.origin_id),
      cursor: normalizeQueryValue(params.cursor),
    };
    return queryOptions({
      queryKey: queryKeys.routes.actors(routeId, request),
      queryFn: ({ signal }) => (signal ? apiClient.getRouteActors(routeId, request, { signal }) : apiClient.getRouteActors(routeId, request)),
      enabled: Boolean(routeId),
      staleTime: 1000 * 60 * 3,
    });
  },
  routeMap: (routeId: string, params: GetRouteMapQuery = {}) => {
    const request: GetRouteMapQuery = {
      origin_id: normalizeQueryValue(params.origin_id),
      layer: params.layer ?? undefined,
      category: normalizeQueryValue(params.category),
    };
    return queryOptions({
      queryKey: queryKeys.routes.map(routeId, request),
      queryFn: ({ signal }) => apiClient.getRouteMapPayload(routeId, request, { signal }),
      select: (e) => e.data,
      enabled: Boolean(routeId),
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount, error) => {
        if (error && typeof error === 'object' && 'code' in error && error.code === 'OFFLINE') {
          return false;
        }
        return failureCount < 1;
      },
    });
  },
  actorCategories: () =>
    queryOptions({
      queryKey: queryKeys.actorCategories(),
      queryFn: () => apiClient.getActorCategories(),
      select: (e) => e.data,
      staleTime: 1000 * 60 * 15, // 15 minutes
      gcTime: process.env.NODE_ENV === 'test' ? Infinity : 1000 * 60 * 60, // 1 hour
    }),
  actorDetail: (actorId: string) =>
    queryOptions({ queryKey: queryKeys.actorDetail(actorId), queryFn: () => apiClient.getActorDetail(actorId), select: (e) => e.data, enabled: Boolean(actorId) }),
};

export const useAdminContextQuery = (isAuthenticated = true) => useQuery(adminQueries.context(isAuthenticated));

export const useRegionsQuery = () => useQuery(territorialQueries.regions());
export const useRoutesQuery = (regionId: string | undefined, params?: ListRoutesQuery, userId?: string) => useQuery(territorialQueries.routes(regionId, params, userId));
export const useRouteDetailQuery = (routeId: string) => useQuery(territorialQueries.routeDetail(routeId));
export const useRouteOriginsQuery = (routeId: string) => useQuery(territorialQueries.routeOrigins(routeId));
export const useRouteGeometryQuery = (routeId: string, originId: string) => useQuery(territorialQueries.routeGeometry(routeId, originId));
export const useRouteAlertsQuery = (routeId: string) => useQuery(territorialQueries.routeAlerts(routeId));
export const useRouteActorsQuery = (routeId: string, params?: GetRouteActorsQuery) => useQuery(territorialQueries.routeActors(routeId, params));
export const useRouteMapQuery = (routeId: string, params?: GetRouteMapQuery) =>
  useQuery(territorialQueries.routeMap(routeId, params));
export const useActorCategoriesQuery = () => useQuery(territorialQueries.actorCategories());
export const useActorDetailQuery = (actorId: string) => useQuery(territorialQueries.actorDetail(actorId));
export const useBootstrapQuery = (userId: string) => useQuery(territorialQueries.bootstrap(userId));

export const useInfiniteRoutesQuery = (
  regionId: string | undefined,
  params: ListRoutesQuery = {},
  userId?: string
) =>
  useInfiniteQuery({
    queryKey: ['routes', 'infinite', regionId, params, userId],
    queryFn: ({ pageParam, signal }) =>
      apiClient.getRoutes(
        {
          ...params,
          region_id: normalizeQueryValue(regionId),
          cursor: pageParam ? String(pageParam) : undefined,
        },
        { signal }
      ),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.meta.next_cursor ?? undefined,
    enabled: Boolean(regionId) && (!params.saved || Boolean(userId)),
  });

export const useInfiniteRouteActorsQuery = (
  routeId: string,
  params: GetRouteActorsQuery = {}
) =>
  useInfiniteQuery({
    queryKey: ['routes', 'actors', 'infinite', routeId, params],
    queryFn: ({ pageParam, signal }) =>
      apiClient.getRouteActors(
        routeId,
        {
          ...params,
          cursor: pageParam ? String(pageParam) : undefined,
        },
        { signal }
      ),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.meta.next_cursor ?? undefined,
    enabled: Boolean(routeId),
  });

export const userQueries = {
  profile: (userId?: string) =>
    queryOptions({
      queryKey: queryKeys.myProfile(userId),
      queryFn: () => apiClient.getMyProfile(),
      select: (e) => e.data,
      meta: { authenticated: true },
    }),
  trips: (userId?: string) =>
    queryOptions({
      queryKey: queryKeys.myTrips(userId),
      queryFn: () => apiClient.getMyTrips(),
      select: (e) => e.data,
      meta: { authenticated: true },
    }),
  favoriteRoutes: (userId?: string) =>
    queryOptions({
      queryKey: queryKeys.myFavoriteRoutes(userId),
      queryFn: () => apiClient.getMyFavoriteRoutes(),
      select: (e) => e.data,
      meta: { authenticated: true },
    }),
  favoriteActors: (userId?: string) =>
    queryOptions({
      queryKey: queryKeys.favoriteActors(userId),
      queryFn: () => apiClient.getMyFavoriteActors(),
      select: (e) => e.data,
      enabled: Boolean(userId),
      meta: { authenticated: true },
    }),
  preferences: (userId?: string) =>
    queryOptions({
      queryKey: queryKeys.myPreferences(userId),
      queryFn: () => apiClient.getMyPreferences(),
      select: (e) => e.data,
      meta: { authenticated: true },
    }),
  supportContent: () =>
    queryOptions({
      queryKey: queryKeys.supportContent(),
      queryFn: () => apiClient.getSupportContent(),
      select: (e) => e.data,
    }),
};

export const useMyProfileQuery = (userId?: string) => useQuery(userQueries.profile(userId));
export const useMyTripsQuery = (userId?: string) => useQuery(userQueries.trips(userId));
export const useMyFavoriteRoutesQuery = (userId?: string) => useQuery(userQueries.favoriteRoutes(userId));
export const useMyFavoriteActorsQuery = (userId?: string) => useQuery(userQueries.favoriteActors(userId));
export const useMyPreferencesQuery = (userId?: string) => useQuery(userQueries.preferences(userId));
export const useSupportContentQuery = () => useQuery(userQueries.supportContent());
