import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';

import { apiClient } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import { useOptimisticFavoriteRoute } from './useOptimisticFavoriteRoute';
import { useRoutesQuery } from './queries';

jest.mock('./useAuth', () => ({
  useAuth: () => ({ user: { id: 'qa-user-1' }, status: 'authenticated' }),
}));

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('ECO-1901 — favorito otimista e cancelamento de busca obsoleta', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: Infinity },
        mutations: { retry: false, gcTime: Infinity },
      },
    });
  });

  afterEach(() => {
    queryClient.clear();
    jest.restoreAllMocks();
  });

  it('altera o cache imediatamente e restaura o snapshot com anúncio acessível na falha', async () => {
    const request = deferred<{ success: boolean }>();
    jest.spyOn(apiClient, 'addFavoriteRoute').mockReturnValue(request.promise);
    const announce = jest
      .spyOn(AccessibilityInfo, 'announceForAccessibility')
      .mockImplementation(() => undefined);

    const listKey = queryKeys.routes.list('region-1');
    queryClient.setQueryData(listKey, {
      data: [{ id: 'route-1', title: 'Rota real', is_favorite: false }],
      meta: { total: 1, limit: 20, next_cursor: null },
    });

    let favorite: ReturnType<typeof useOptimisticFavoriteRoute> | undefined;
    function Harness() {
      favorite = useOptimisticFavoriteRoute();
      return null;
    }

    await act(async () => {
      renderer.create(
        <QueryClientProvider client={queryClient}>
          <Harness />
        </QueryClientProvider>
      );
    });

    await act(async () => {
      favorite!.toggleFavorite('route-1', false);
      await flush();
    });

    expect(
      queryClient.getQueryData<any>(listKey).data[0].is_favorite
    ).toBe(true);
    expect(announce).not.toHaveBeenCalled();

    await act(async () => {
      request.reject(new Error('falha controlada'));
      await flush();
    });

    expect(
      queryClient.getQueryData<any>(listKey).data[0].is_favorite
    ).toBe(false);
    expect(announce).toHaveBeenCalledWith(
      'Falha ao atualizar favorito da rota. Alteração desfeita.'
    );
  });

  it('anuncia sucesso somente depois que o backend confirma a mutation', async () => {
    const request = deferred<{ success: boolean }>();
    jest.spyOn(apiClient, 'addFavoriteRoute').mockReturnValue(request.promise);
    const announce = jest
      .spyOn(AccessibilityInfo, 'announceForAccessibility')
      .mockImplementation(() => undefined);

    let favorite: ReturnType<typeof useOptimisticFavoriteRoute> | undefined;
    function Harness() {
      favorite = useOptimisticFavoriteRoute();
      return null;
    }
    await act(async () => {
      renderer.create(
        <QueryClientProvider client={queryClient}>
          <Harness />
        </QueryClientProvider>
      );
    });

    await act(async () => {
      favorite!.toggleFavorite('route-2', false);
      await flush();
    });
    expect(announce).not.toHaveBeenCalled();

    await act(async () => {
      request.resolve({ success: true });
      await flush();
    });
    expect(announce).toHaveBeenCalledWith(
      'Rota salva nos favoritos com sucesso.'
    );
  });

  it('propaga AbortSignal e aborta a busca anterior quando o termo muda', async () => {
    const signals: AbortSignal[] = [];
    jest.spyOn(apiClient, 'getRoutes').mockImplementation((_params, options) => {
      const signal = options?.signal;
      if (!signal) throw new Error('AbortSignal ausente');
      signals.push(signal);
      return new Promise((_resolve, reject) => {
        signal.addEventListener('abort', () => reject(new Error('aborted')), { once: true });
      });
    });

    function Harness({ query }: { query: string }) {
      useRoutesQuery('region-1', { q: query });
      return null;
    }

    let tree: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <Harness query="praia" />
        </QueryClientProvider>
      );
      await flush();
    });
    expect(signals).toHaveLength(1);
    expect(signals[0].aborted).toBe(false);

    await act(async () => {
      tree!.update(
        <QueryClientProvider client={queryClient}>
          <Harness query="pindobal" />
        </QueryClientProvider>
      );
      await flush();
    });

    expect(signals).toHaveLength(2);
    expect(signals[0].aborted).toBe(true);
    expect(signals[1].aborted).toBe(false);
  });
});
