import { ApiClient, ApiClientError } from './client';
import { onlineManager } from '@tanstack/react-query';

describe('ApiClient auth', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    onlineManager.setOnline(true);
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  it('bloqueia mutation offline sem chamar a rede', async () => {
    global.fetch = jest.fn();
    onlineManager.setOnline(false);
    const client = new ApiClient('https://api.example/api/v1');

    await expect(client.updateMyPreferences({ high_contrast: true })).rejects.toMatchObject({
      status: 0,
      code: 'OFFLINE_MUTATION_BLOCKED',
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('envia o token atual', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: [] }), { status: 200 })
    );
    const client = new ApiClient('https://api.example/api/v1');
    client.configureAuth(() => 'access-token', async () => null);
    await client.getRegions();
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example/api/v1/regions',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer access-token' }),
      })
    );
  });

  it('serializa filtros gerados de rotas e atores', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: [], meta: { total: 0, limit: 20 } }), {
        status: 200,
      })
    );
    const client = new ApiClient('https://api.example/api/v1');
    await client.getRoutes({ saved: true, verified: true });
    await client.getRouteActors('route-id', { origin_id: 'origin-id', category: 'food' });
    expect(global.fetch).toHaveBeenNthCalledWith(
      1,
      'https://api.example/api/v1/routes?saved=true&verified=true',
      expect.any(Object)
    );
    expect(global.fetch).toHaveBeenNthCalledWith(
      2,
      'https://api.example/api/v1/routes/route-id/actors?category=food&origin_id=origin-id',
      expect.any(Object)
    );
  });

  it('coordena refresh concorrente e repete cada request uma vez', async () => {
    let token = 'old';
    const fetchMock = jest
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: {} }), { status: 401 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: {} }), { status: 401 }))
      .mockResolvedValue(new Response(JSON.stringify({ data: [] }), { status: 200 }));
    global.fetch = fetchMock;
    const refresh = jest.fn(async () => {
      token = 'new';
      return token;
    });
    const client = new ApiClient('https://api.example/api/v1');
    client.configureAuth(() => token, refresh);
    await Promise.all([client.getRegions(), client.getRegions()]);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(4);
    const replayHeaders = fetchMock.mock.calls.slice(2).map((call) => call[1].headers);
    replayHeaders.forEach((headers) => expect(headers.Authorization).toBe('Bearer new'));
  });

  it('não entra em loop quando o replay continua não autorizado', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { message: 'unauthorized' } }), { status: 401 })
    );
    const client = new ApiClient('https://api.example/api/v1');
    const refresh = jest.fn().mockResolvedValue('new');
    client.configureAuth(() => 'old', refresh);
    await expect(client.getRegions()).rejects.toBeInstanceOf(ApiClientError);
    expect(global.fetch).toHaveBeenCalledTimes(2);
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it('classifica falha de refresh como erro de autenticação', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: {} }), { status: 401 })
    );
    const client = new ApiClient('https://api.example/api/v1');
    const onAuthFailure = jest.fn();
    client.configureAuth(
      () => 'old',
      async () => {
        throw new Error('refresh token rejected');
      },
      onAuthFailure
    );
    await expect(client.getRegions()).rejects.toMatchObject({
      status: 401,
      code: 'AUTH_REFRESH_FAILED',
    });
    expect(onAuthFailure).toHaveBeenCalledTimes(1);
  });

  it('preserva o request_id retornado pelo backend em erros', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: 'NOT_FOUND', message: 'Rota não encontrada.' },
          request_id: 'req-backend-123',
        }),
        { status: 404 }
      )
    );
    const client = new ApiClient('https://api.example/api/v1');
    await expect(client.getRouteDetail('missing')).rejects.toMatchObject({
      status: 404,
      code: 'NOT_FOUND',
      requestId: 'req-backend-123',
    });
  });

  it('rejeita API HTTP fora do ambiente local', () => {
    expect(() => new ApiClient('http://api.example/api/v1')).toThrow('HTTPS');
  });
});
