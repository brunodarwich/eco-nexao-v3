import type { Session, SupabaseClient } from '@supabase/supabase-js';

import { AuthSessionManager } from './sessionManager';

function session(token: string): Session {
  return {
    access_token: token,
    refresh_token: `refresh-${token}`,
    expires_in: 3600,
    token_type: 'bearer',
    user: { id: 'user-1', is_anonymous: true } as Session['user'],
  };
}

function client(overrides: Record<string, jest.Mock> = {}) {
  const auth = {
    getSession: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
    signInAnonymously: jest.fn().mockResolvedValue({ data: { session: session('guest') }, error: null }),
    refreshSession: jest.fn().mockResolvedValue({ data: { session: session('fresh') }, error: null }),
    updateUser: jest.fn().mockResolvedValue({ data: {}, error: null }),
    signOut: jest.fn().mockResolvedValue({ error: null }),
    ...overrides,
  };
  return { auth, client: { auth } as unknown as SupabaseClient };
}

describe('AuthSessionManager', () => {
  it('restaura uma sessão existente sem criar outro guest', async () => {
    const existing = session('existing');
    const fake = client({
      getSession: jest.fn().mockResolvedValue({ data: { session: existing }, error: null }),
    });
    const manager = new AuthSessionManager(fake.client);
    await expect(manager.initialize()).resolves.toBe(existing);
    expect(fake.auth.signInAnonymously).not.toHaveBeenCalled();
    expect(manager.getAccessToken()).toBe('existing');
    expect(manager.getRefreshToken()).toBe('refresh-existing');
  });

  it('faz criação anônima single-flight', async () => {
    const fake = client();
    const manager = new AuthSessionManager(fake.client);
    const [first, second] = await Promise.all([manager.initialize(), manager.initialize()]);
    expect(first).toBe(second);
    expect(fake.auth.getSession).toHaveBeenCalledTimes(1);
    expect(fake.auth.signInAnonymously).toHaveBeenCalledTimes(1);
    expect(manager.getAccessToken()).toBe('guest');
    expect(manager.getRefreshToken()).toBe('refresh-guest');
  });

  it('faz refresh single-flight', async () => {
    const fake = client();
    const manager = new AuthSessionManager(fake.client);
    await manager.initialize();
    const [first, second] = await Promise.all([manager.refresh(), manager.refresh()]);
    expect(first).toBe(second);
    expect(fake.auth.refreshSession).toHaveBeenCalledTimes(1);
    expect(manager.getAccessToken()).toBe('fresh');
    expect(manager.getRefreshToken()).toBe('refresh-fresh');
  });

  it('limpa a sessão no logout local', async () => {
    const fake = client();
    const manager = new AuthSessionManager(fake.client);
    await manager.initialize();
    await manager.signOut();
    expect(fake.auth.signOut).toHaveBeenCalledWith({ scope: 'local' });
    expect(manager.getAccessToken()).toBeNull();
    expect(manager.getRefreshToken()).toBeNull();
  });

  it('ignora evento tardio que tentaria restaurar sessão após logout', async () => {
    const fake = client();
    const manager = new AuthSessionManager(fake.client);
    await manager.initialize();
    await manager.signOut();
    manager.handleAuthEvent('SIGNED_IN', session('stale'));
    expect(manager.getAccessToken()).toBeNull();
  });

  it('invalida a sessão quando o FastAPI rejeita refresh', async () => {
    const fake = client();
    const manager = new AuthSessionManager(fake.client);
    await manager.initialize();
    manager.invalidateSession();
    expect(manager.getAccessToken()).toBeNull();
    manager.handleAuthEvent('TOKEN_REFRESHED', session('stale'));
    expect(manager.getAccessToken()).toBeNull();
  });

  it('fica fail-closed mesmo quando o logout remoto falha', async () => {
    const fake = client({
      signOut: jest.fn().mockResolvedValue({ error: new Error('offline') }),
    });
    const manager = new AuthSessionManager(fake.client);
    await manager.initialize();
    await expect(manager.signOut()).rejects.toThrow('offline');
    expect(manager.getAccessToken()).toBeNull();
  });

  it('rejeita refresh com erro sem disparar signInAnonymously', async () => {
    const fake = client({
      refreshSession: jest.fn().mockResolvedValue({
        data: { session: null },
        error: new Error('invalid_grant'),
      }),
    });
    const manager = new AuthSessionManager(fake.client);
    await manager.initialize();
    fake.auth.signInAnonymously.mockClear();

    await expect(manager.refresh()).rejects.toThrow('invalid_grant');
    expect(fake.auth.signInAnonymously).not.toHaveBeenCalled();
  });
});
