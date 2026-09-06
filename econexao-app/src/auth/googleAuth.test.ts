import type { Session, SupabaseClient } from '@supabase/supabase-js';

import { AuthSessionManager, GUEST_SNAPSHOT_STORAGE_KEY } from './sessionManager';
import { authStorage } from './storage';
import { parseOAuthUrl, getOAuthRedirectUri } from './oauthHelper';

function mockSession(userId: string, isAnonymous: boolean = false): Session {
  return {
    access_token: `token-${userId}`,
    refresh_token: `refresh-${userId}`,
    expires_in: 3600,
    token_type: 'bearer',
    user: { id: userId, is_anonymous: isAnonymous, email: `${userId}@exemplo.com` } as Session['user'],
  };
}

function mockClient(overrides: Record<string, jest.Mock> = {}) {
  const auth = {
    getSession: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
    signInAnonymously: jest.fn().mockResolvedValue({ data: { session: mockSession('guest-1', true) }, error: null }),
    signInWithOAuth: jest.fn().mockResolvedValue({ data: { provider: 'google', url: 'https://accounts.google.com/o/oauth2/v2/auth?...' }, error: null }),
    linkIdentity: jest.fn().mockResolvedValue({ data: { provider: 'google', url: 'https://accounts.google.com/o/oauth2/v2/auth?...' }, error: null }),
    exchangeCodeForSession: jest.fn().mockResolvedValue({ data: { session: mockSession('google-user-1', false) }, error: null }),
    setSession: jest.fn().mockResolvedValue({ data: { session: mockSession('google-user-1', false) }, error: null }),
    refreshSession: jest.fn().mockResolvedValue({ data: { session: mockSession('fresh-user', false) }, error: null }),
    updateUser: jest.fn().mockResolvedValue({ data: {}, error: null }),
    signOut: jest.fn().mockResolvedValue({ error: null }),
    ...overrides,
  };
  return { auth, client: { auth } as unknown as SupabaseClient };
}

import { Platform } from 'react-native';

describe('ECO-2606 — Login Google com Favoritos Preservados e Isolamento A/B', () => {
  const originalPlatform = Platform.OS;

  beforeEach(async () => {
    Platform.OS = 'web';
    jest.clearAllMocks();
    await authStorage.removeItem(GUEST_SNAPSHOT_STORAGE_KEY);
  });

  afterAll(() => {
    Platform.OS = originalPlatform;
  });

  describe('1. Fluxos de Autenticacao Google (signInWithOAuth vs linkIdentity)', () => {
    it('inicia login normal com Google via signInWithOAuth no modo entrar', async () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      const result = await manager.signInWithGoogle('https://app.econexao.com.br/');
      expect(fake.auth.signInWithOAuth).toHaveBeenCalledWith({
        provider: 'google',
        options: {
          redirectTo: 'https://app.econexao.com.br/',
          skipBrowserRedirect: false,
        },
      });
      expect(result.url).toContain('https://accounts.google.com');
    });

    it('inicia vinculacao guest com Google via linkIdentity preservando a conta', async () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      const result = await manager.linkGoogleAccount('https://app.econexao.com.br/');
      expect(fake.auth.linkIdentity).toHaveBeenCalledWith({
        provider: 'google',
        options: {
          redirectTo: 'https://app.econexao.com.br/',
        },
      });
      expect(result.url).toContain('https://accounts.google.com');
    });
  });

  describe('2. Preservacao de Snapshot de Favoritos Guest', () => {
    it('armazena e recupera o snapshot de favoritos do guest com integridade', async () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      const snapshot = {
        guestUserId: 'guest-123',
        favoriteRouteIds: ['route-pindobal', 'route-alter-do-chao'],
        favoriteActorIds: ['actor-artesanato-1', 'actor-bar-praia-2'],
        createdAt: Date.now(),
      };

      await manager.saveGuestFavoritesSnapshot(snapshot);
      const retrieved = await manager.getGuestFavoritesSnapshot();

      expect(retrieved).toEqual(snapshot);
    });

    it('reconcilia os favoritos guest na nova conta de forma idempotente e limpa o snapshot', async () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      await manager.saveGuestFavoritesSnapshot({
        guestUserId: 'guest-123',
        favoriteRouteIds: ['route-pindobal'],
        favoriteActorIds: ['actor-artesanato-1', 'actor-artesanato-2'],
        createdAt: Date.now(),
      });

      const mockApiClient = {
        addFavoriteRoute: jest.fn().mockResolvedValue({ success: true }),
        addFavoriteActor: jest.fn().mockResolvedValue({ success: true }),
      };

      const result = await manager.reconcileGuestFavorites(mockApiClient);

      expect(result.routesPreserved).toBe(1);
      expect(result.actorsPreserved).toBe(2);
      expect(mockApiClient.addFavoriteRoute).toHaveBeenCalledWith('route-pindobal');
      expect(mockApiClient.addFavoriteActor).toHaveBeenCalledWith('actor-artesanato-1');
      expect(mockApiClient.addFavoriteActor).toHaveBeenCalledWith('actor-artesanato-2');

      const remaining = await manager.getGuestFavoritesSnapshot();
      expect(remaining).toBeNull();
    });
  });

  describe('3. Resolucao de Conflito segundo ADR 0007 (Opcao 1 - Rejeicao com Alternativa de Login)', () => {
    it('detecta erros reais de identidade ja existente no Supabase', () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      expect(manager.isIdentityConflictError(new Error('identity_already_exists'))).toBe(true);
      expect(manager.isIdentityConflictError(new Error('A user with this provider already exists'))).toBe(true);
      expect(manager.isIdentityConflictError(new Error('User already registered'))).toBe(true);
      expect(manager.isIdentityConflictError(new Error('manual_linking_disabled'))).toBe(true);
      expect(manager.isIdentityConflictError(new Error('Network request failed'))).toBe(false);
    });

    it('descarta o snapshot guest ao optar por entrar na conta existente (zero contaminacao A/B)', async () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      await manager.saveGuestFavoritesSnapshot({
        guestUserId: 'guest-123',
        favoriteRouteIds: ['route-temp'],
        favoriteActorIds: ['actor-temp'],
        createdAt: Date.now(),
      });

      // Usuario confirma login na conta antiga: snapshot descartado
      await manager.clearGuestFavoritesSnapshot();
      const snapshotAfterDiscard = await manager.getGuestFavoritesSnapshot();
      expect(snapshotAfterDiscard).toBeNull();
    });
  });

  describe('4. Isolamento A/B e Ciclo de Logout', () => {
    it('limpa sessao, tokens e snapshot pendente no signOut garantindo que Usuario A nao vaze para B', async () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      await manager.saveGuestFavoritesSnapshot({
        guestUserId: 'user-a',
        favoriteRouteIds: ['route-a'],
        favoriteActorIds: ['actor-a'],
        createdAt: Date.now(),
      });

      // Sessao ativa do usuario A
      manager.handleAuthEvent('SIGNED_IN', mockSession('user-a', false));
      expect(manager.getAccessToken()).toBe('token-user-a');

      // Logout do usuario A
      await manager.signOut();

      expect(manager.getAccessToken()).toBeNull();
      expect(manager.getRefreshToken()).toBeNull();
      expect(manager.getSession()).toBeNull();
      expect(await manager.getGuestFavoritesSnapshot()).toBeNull();

      // Sessao subsequente do usuario B via login Google (OAuth callback)
      fake.auth.exchangeCodeForSession.mockResolvedValueOnce({
        data: { session: mockSession('user-b', false) },
        error: null,
      });
      await manager.handleOAuthCallback({ type: 'success', code: 'code-user-b' });
      expect(manager.getAccessToken()).toBe('token-user-b');
      expect(manager.getSession()?.user?.id).toBe('user-b');
    });
  });

  describe('5. Callback OAuth e Parsing de Parametros', () => {
    it('faz parsing correto de PKCE code em URLs de callback', () => {
      const parsed = parseOAuthUrl('https://app.econexao.com.br/?code=pkce-auth-code-1234');
      expect(parsed.type).toBe('success');
      expect(parsed.code).toBe('pkce-auth-code-1234');
    });

    it('faz parsing de access_token em fragmento hash (#)', () => {
      const parsed = parseOAuthUrl('https://app.econexao.com.br/#access_token=jwt-token-xyz&refresh_token=refresh-xyz');
      expect(parsed.type).toBe('success');
      expect(parsed.accessToken).toBe('jwt-token-xyz');
      expect(parsed.refreshToken).toBe('refresh-xyz');
    });

    it('identifica cancelamento gracioso pelo usuario (access_denied)', () => {
      const parsed = parseOAuthUrl('https://app.econexao.com.br/?error=access_denied&error_description=User+denied');
      expect(parsed.type).toBe('cancel');
      expect(parsed.errorDescription).toContain('User');
    });

    it('processa callback PKCE no handleOAuthCallback com sucesso', async () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      const session = await manager.handleOAuthCallback({
        type: 'success',
        code: 'auth-code-test',
      });

      expect(fake.auth.exchangeCodeForSession).toHaveBeenCalledWith('auth-code-test');
      expect(session?.user.id).toBe('google-user-1');
      expect(manager.getAccessToken()).toBe('token-google-user-1');
    });

    it('lanca erro descritivo quando o callback indica cancelamento do usuario', async () => {
      const fake = mockClient();
      const manager = new AuthSessionManager(fake.client);

      await expect(
        manager.handleOAuthCallback({
          type: 'cancel',
          errorDescription: 'Cancelado pelo usuario',
        })
      ).rejects.toThrow('Cancelado pelo usuario');
    });
  });
});
