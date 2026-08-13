import { ApiClientError } from './client';
import { createQueryClient, removeAuthenticatedQueries, shouldRetry } from './queryClient';
import { queryKeys } from './queryKeys';

describe('server cache', () => {
  it('isola listas por região e filtros', () => {
    const client = createQueryClient();
    const regionA = queryKeys.routes.list('region-a', { q: ' praia ', verified: true });
    const regionB = queryKeys.routes.list('region-b', { q: 'praia', verified: true });
    const saved = queryKeys.routes.list('region-a', { q: 'praia', saved: true }, 'user-a');
    const savedB = queryKeys.routes.list('region-a', { q: 'praia', saved: true }, 'user-b');
    client.setQueryData(regionA, ['A']);
    client.setQueryData(regionB, ['B']);
    client.setQueryData(saved, ['saved-A']);
    client.setQueryData(savedB, ['saved-B']);
    expect(client.getQueryData(regionA)).toEqual(['A']);
    expect(client.getQueryData(regionB)).toEqual(['B']);
    expect(client.getQueryData(saved)).toEqual(['saved-A']);
    expect(client.getQueryData(savedB)).toEqual(['saved-B']);
    client.clear();
  });

  it('isola geometria e mapa por origem', () => {
    expect(queryKeys.routes.geometry('route', 'port')).not.toEqual(
      queryKeys.routes.geometry('route', 'airport')
    );
    expect(queryKeys.routes.map('route', 'port')).not.toEqual(
      queryKeys.routes.map('route', 'airport')
    );
  });

  it('normaliza strings equivalentes nas chaves', () => {
    expect(queryKeys.routes.list('region', { q: ' praia ' })).toEqual(
      queryKeys.routes.list('region', { q: 'praia' })
    );
  });

  it('não repete 4xx e limita tentativas transitórias', () => {
    expect(shouldRetry(0, new ApiClientError('unauthorized', 401))).toBe(false);
    expect(shouldRetry(0, new ApiClientError('server', 503))).toBe(true);
    expect(shouldRetry(2, new ApiClientError('server', 503))).toBe(false);
    expect(shouldRetry(0, new ApiClientError('network', 0))).toBe(true);
  });

  it('remove dados autenticados sem apagar conteúdo público', () => {
    const client = createQueryClient();
    client.getQueryCache().build(client, {
      queryKey: queryKeys.bootstrap('user-a'),
      queryFn: async () => 'private',
      meta: { authenticated: true },
    }).setData('private');
    client.setQueryData(queryKeys.regions(), ['public']);
    removeAuthenticatedQueries(client);
    expect(client.getQueryData(queryKeys.bootstrap('user-a'))).toBeUndefined();
    expect(client.getQueryData(queryKeys.regions())).toEqual(['public']);
    client.clear();
  });
});
