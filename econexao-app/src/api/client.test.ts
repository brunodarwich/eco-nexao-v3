import { ApiClient, ApiClientError } from './client';
import { onlineManager } from '@tanstack/react-query';
import { Platform } from 'react-native';

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

  it('envia avatar como multipart sem fixar Content-Type ou expor segredo', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            media_asset_id: 'asset-id',
            url: 'https://cdn/avatar.webp',
            derivatives: {},
            alt_text: 'Avatar',
          },
        }),
        { status: 200 }
      )
    );
    const client = new ApiClient('https://api.example/api/v1');
    await client.uploadAvatar({
      uri: 'file:///avatar.png',
      name: 'avatar.png',
      type: 'image/png',
      file: new Blob(['image-bytes'], { type: 'image/png' }),
    });

    const [url, options] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toBe('https://api.example/api/v1/me/avatar');
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.headers['Content-Type']).toBeUndefined();
    expect(options.headers.Authorization).toBeUndefined();
  });

  it('materializa um Blob no Web quando o picker não fornece File', async () => {
    const platform = jest.replaceProperty(Platform, 'OS', 'web');
    const fetchMock = jest
      .fn()
      .mockResolvedValueOnce(
        new Response(new Blob(['image-bytes'], { type: 'image/png' }), { status: 200 })
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: {
              media_asset_id: 'asset-id',
              url: 'https://cdn/avatar.webp',
              derivatives: {},
              alt_text: 'Avatar',
            },
          }),
          { status: 200 }
        )
      );
    global.fetch = fetchMock;

    try {
      const client = new ApiClient('https://api.example/api/v1');
      await client.uploadAvatar({
        uri: 'blob:https://app.example/avatar',
        name: 'avatar.png',
        type: 'image/png',
      });

      expect(fetchMock).toHaveBeenNthCalledWith(1, 'blob:https://app.example/avatar');
      expect(fetchMock).toHaveBeenNthCalledWith(
        2,
        'https://api.example/api/v1/me/avatar',
        expect.objectContaining({ body: expect.any(FormData) })
      );
    } finally {
      platform.restore();
    }
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

  it('serializa origem, camada e categoria do payload de mapa', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      new Response(JSON.stringify({ data: { pins: [], legend: [] } }), { status: 200 })
    );
    const client = new ApiClient('https://api.example/api/v1');
    await client.getRouteMapPayload('route-id', {
      origin_id: 'origin-id',
      layer: 'citywide_essential',
      category: 'saude',
    });
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example/api/v1/routes/route-id/map?origin_id=origin-id&layer=citywide_essential&category=saude',
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });

  it('classifica mapa offline sem chamar a rede', async () => {
    global.fetch = jest.fn();
    onlineManager.setOnline(false);
    const client = new ApiClient('https://api.example/api/v1');
    await expect(client.getRouteMapPayload('route-id')).rejects.toMatchObject({
      status: 0,
      code: 'OFFLINE',
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('aborta e classifica timeout do mapa', async () => {
    global.fetch = jest.fn((_url, options) => new Promise((_resolve, reject) => {
      if (options?.signal?.aborted) {
        reject(Object.assign(new Error('aborted'), { name: 'AbortError' }));
        return;
      }
      options?.signal?.addEventListener('abort', () =>
        reject(Object.assign(new Error('aborted'), { name: 'AbortError' }))
      );
    })) as jest.Mock;
    const client = new ApiClient('https://api.example/api/v1');
    await expect(
      client.getRouteMapPayload('route-id', {}, { timeoutMs: 1 })
    ).rejects.toMatchObject({ status: 0, code: 'TIMEOUT' });
  });

  it('suporta resposta imediata sem abortar', async () => {
    const payload = { data: { pins: [], legend: [] } };
    global.fetch = jest.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), { status: 200 })
    );
    const client = new ApiClient('https://api.example/api/v1');
    const result = await client.getRouteMapPayload('route-id');
    expect(result).toEqual(payload);
  });

  it('suporta cold start simulado quando o servidor responde antes do timeout', async () => {
    const payload = { data: { pins: [], legend: [] } };
    global.fetch = jest.fn((_url, _options) => new Promise((resolve) => {
      setTimeout(() => {
        resolve(new Response(JSON.stringify(payload), { status: 200 }));
      }, 50);
    })) as jest.Mock;
    const client = new ApiClient('https://api.example/api/v1');
    const result = await client.getRouteMapPayload('route-id', {}, { timeoutMs: 500 });
    expect(result).toEqual(payload);
  });

  it('cancela a requisição de mapa quando o caller aborta o signal', async () => {
    const controller = new AbortController();
    global.fetch = jest.fn((_url, options) => new Promise((_resolve, reject) => {
      if (options?.signal?.aborted) {
        reject(Object.assign(new Error('user cancelled'), { name: 'AbortError' }));
        return;
      }
      options?.signal?.addEventListener('abort', () =>
        reject(Object.assign(new Error('user cancelled'), { name: 'AbortError' }))
      );
    })) as jest.Mock;
    const client = new ApiClient('https://api.example/api/v1');
    const promise = client.getRouteMapPayload('route-id', {}, { signal: controller.signal });
    controller.abort();
    await expect(promise).rejects.toMatchObject({ status: 0, code: 'NETWORK_ERROR' });
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
