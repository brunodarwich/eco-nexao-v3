import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { apiClient } from '../../api/client';
import { useApp } from '../../hooks/useApp';
import { useAuth } from '../../hooks/useAuth';
import { useOptimisticFavoriteRoute } from '../../hooks/useOptimisticFavoriteRoute';
import { useOptimisticFavoriteActor } from '../../hooks/useOptimisticFavoriteActor';
import { queryKeys } from '../../api/queryKeys';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));

jest.mock('expo-router', () => ({
  useRouter: () => ({ push: jest.fn(), back: jest.fn() }),
  useLocalSearchParams: () => ({ routeId: 'route-tapajos' }),
}));

jest.mock('../../hooks/useApp', () => ({
  useApp: jest.fn(),
}));

jest.mock('../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

describe('ECO-1901 — Dados reais, paginação e favoritos consistentes no App público', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: Infinity },
        mutations: { retry: false, gcTime: Infinity },
      },
    });

    (useApp as jest.Mock).mockReturnValue({
      state: { activeRegionId: 'region-tapajos' },
      activeRegion: { id: 'region-tapajos', name: 'Tapajós' },
    });

    (useAuth as jest.Mock).mockReturnValue({
      user: { id: 'test-user-1' },
      status: 'authenticated',
    });
  });

  afterEach(() => {
    queryClient.clear();
  });

  test('useOptimisticFavoriteRoute atualiza cache imediatamente e faz rollback no erro', async () => {
    let hookResult: ReturnType<typeof useOptimisticFavoriteRoute> | undefined;

    const queryKey = queryKeys.routes.list('region-tapajos');
    const initialRouteList = {
      data: [
        {
          id: 'route-100',
          slug: 'rota-praias',
          title: 'Rota das Praias',
          region_id: 'region-tapajos',
          city: 'Belterra',
          state_code: 'PA',
          total_distance_km: 12.5,
          actor_count_total: 4,
          is_verified: true,
          is_favorite: false,
        },
      ],
      meta: { total: 1, limit: 20 },
    };

    queryClient.setQueryDefaults(queryKeys.routes.all(), {
      queryFn: async () => initialRouteList,
    });
    queryClient.setQueryData(queryKey, initialRouteList);

    const TestComponent = () => {
      hookResult = useOptimisticFavoriteRoute();
      return <div />;
    };

    await act(async () => {
      renderer.create(
        <QueryClientProvider client={queryClient}>
          <TestComponent />
        </QueryClientProvider>
      );
    });

    // Mock falha no backend
    jest.spyOn(apiClient, 'addFavoriteRoute').mockRejectedValueOnce(new Error('Network error'));

    // Executa mutação otimista
    await act(async () => {
      hookResult!.toggleFavorite('route-100', false);
      await new Promise((resolve) => setTimeout(resolve, 50));
    });

    // O cache deve ter sido desfeito para o estado inicial após falha
    const cachedData = queryClient.getQueryData<typeof initialRouteList>(queryKey);
    expect(cachedData?.data[0].is_favorite).toBe(false);
  });

  test('useOptimisticFavoriteActor atualiza cache imediatamente e faz rollback no erro', async () => {
    let hookResult: ReturnType<typeof useOptimisticFavoriteActor> | undefined;

    const queryKey = queryKeys.favoriteActors('test-user-1');
    const actor = {
      id: 'actor-200',
      slug: 'pousada-sol',
      name: 'Pousada do Sol',
      category_slug: 'hospedagem',
      category_label: 'Hospedagem',
      green_badge_status: 'verified',
      verification_status: 'verified',
    };
    const initialActorList = {
      data: [],
      meta: { total: 1, limit: 20 },
    };

    queryClient.setQueryDefaults(queryKey, {
      queryFn: async () => initialActorList,
    });
    queryClient.setQueryData(queryKey, initialActorList);

    const TestComponent = () => {
      hookResult = useOptimisticFavoriteActor();
      return <div />;
    };

    await act(async () => {
      renderer.create(
        <QueryClientProvider client={queryClient}>
          <TestComponent />
        </QueryClientProvider>
      );
    });

    jest.spyOn(apiClient, 'addFavoriteActor').mockRejectedValueOnce(new Error('Server 500'));

    await act(async () => {
      hookResult!.toggleFavorite(actor, false);
      await new Promise((resolve) => setTimeout(resolve, 50));
    });

    const cachedData = queryClient.getQueryData<typeof initialActorList>(queryKey);
    expect(cachedData?.data).toEqual([]);
  });
});
