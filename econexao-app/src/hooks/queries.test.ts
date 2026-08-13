import { apiClient } from '../api/client';
import { territorialQueries } from './queries';

describe('territorial query options', () => {
  afterEach(() => jest.restoreAllMocks());

  it('encaminha região e filtros ao client e desempacota o envelope', async () => {
    const envelope = { data: [], meta: { total: 0, limit: 20 } };
    const call = jest.spyOn(apiClient, 'getRoutes').mockResolvedValue(envelope);
    const options = territorialQueries.routes(
      'region-id',
      { q: ' praia ', saved: true },
      'user-id'
    );
    const result = await options.queryFn!({} as never);
    expect(call).toHaveBeenCalledWith({
      region_id: 'region-id',
      q: 'praia',
      saved: true,
    });
    expect(result).toEqual(envelope);
    expect(options.meta).toEqual({ authenticated: true });
  });

  it('desabilita consultas sem identificadores obrigatórios', () => {
    expect(territorialQueries.routeDetail('').enabled).toBe(false);
    expect(territorialQueries.routeGeometry('route', '').enabled).toBe(false);
    expect(territorialQueries.routes(undefined).enabled).toBe(false);
    expect(territorialQueries.routes('region', { saved: true }).enabled).toBe(false);
  });
});
