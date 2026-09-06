import type { AuthChangeEvent, Session, SupabaseClient } from '@supabase/supabase-js';

import { authStorage } from './storage';
import {
  cleanWebOAuthUrl,
  getOAuthRedirectUri,
  getWebLocationOAuthCallback,
  type ParsedOAuthCallback,
} from './oauthHelper';

export type SessionListener = (session: Session | null) => void;

export interface GuestFavoritesSnapshot {
  guestUserId: string;
  favoriteRouteIds: string[];
  favoriteActorIds: string[];
  createdAt: number;
}

export const GUEST_SNAPSHOT_STORAGE_KEY = 'econexao-guest-pending-favorites';

export class AuthSessionManager {
  private session: Session | null = null;
  private initializeFlight: Promise<Session> | null = null;
  private refreshFlight: Promise<Session | null> | null = null;
  private generation = 0;
  private explicitlySignedOut = false;
  private listeners = new Set<SessionListener>();

  constructor(private readonly client: SupabaseClient) {}

  getSession(): Session | null {
    return this.session;
  }

  getAccessToken(): string | null {
    return this.session?.access_token ?? null;
  }

  getRefreshToken(): string | null {
    return this.session?.refresh_token ?? null;
  }

  subscribe(listener: SessionListener): () => void {
    this.listeners.add(listener);
    listener(this.session);
    return () => this.listeners.delete(listener);
  }

  private setSession(session: Session | null): void {
    this.session = session;
    this.listeners.forEach((listener) => listener(session));
  }

  initialize(): Promise<Session> {
    if (this.session) return Promise.resolve(this.session);
    if (this.initializeFlight) return this.initializeFlight;
    const generation = this.generation;
    this.explicitlySignedOut = false;
    this.initializeFlight = this.restoreOrCreate(generation).finally(() => {
      this.initializeFlight = null;
    });
    return this.initializeFlight;
  }

  private async restoreOrCreate(generation: number): Promise<Session> {
    // 1. Processa possivel retorno OAuth pendente na URL (Web callback / PKCE)
    const webCallback = getWebLocationOAuthCallback();
    if (webCallback.type === 'success' && webCallback.code) {
      try {
        const { data, error } = await this.client.auth.exchangeCodeForSession(webCallback.code);
        if (!error && data?.session) {
          cleanWebOAuthUrl();
          if (generation !== this.generation) throw new Error('Inicializacao de sessao cancelada.');
          this.setSession(data.session);
          return data.session;
        }
      } catch {
        // Se a troca falhar, cai para o restore padrao
      }
    } else if (webCallback.type === 'cancel' || webCallback.type === 'error') {
      cleanWebOAuthUrl();
    }

    // 2. Restaura sessao existente armazenada
    const restored = await this.client.auth.getSession();
    if (restored.error) throw restored.error;
    let session = restored.data.session;

    // 3. Se nenhuma sessao ativa existir, inicializa sessao anonima guest
    if (!session) {
      const signedIn = await this.client.auth.signInAnonymously();
      if (signedIn.error) throw signedIn.error;
      session = signedIn.data.session;
    }
    if (!session) throw new Error('O Supabase nao retornou uma sessao valida.');
    if (generation !== this.generation) throw new Error('Inicializacao de sessao cancelada.');
    this.setSession(session);
    return session;
  }

  refresh(): Promise<Session | null> {
    if (this.refreshFlight) return this.refreshFlight;
    const generation = this.generation;
    this.refreshFlight = this.client.auth
      .refreshSession()
      .then(({ data, error }) => {
        if (error) throw error;
        if (generation === this.generation) this.setSession(data.session);
        return generation === this.generation ? data.session : null;
      })
      .finally(() => {
        this.refreshFlight = null;
      });
    return this.refreshFlight;
  }

  handleAuthEvent(_event: AuthChangeEvent, session: Session | null): void {
    if (this.explicitlySignedOut && session) return;
    this.setSession(session);
  }

  invalidateSession(): void {
    this.generation += 1;
    this.explicitlySignedOut = true;
    this.setSession(null);
  }

  async linkEmail(email: string): Promise<void> {
    const { error } = await this.client.auth.updateUser({ email });
    if (error) throw error;
  }

  async linkAccount(email: string, password?: string): Promise<void> {
    const payload: { email: string; password?: string } = { email };
    if (password) payload.password = password;
    const { data, error } = await this.client.auth.updateUser(payload);
    if (error) throw error;
    if (this.session && data.user) {
      this.setSession({ ...this.session, user: data.user });
    }
  }

  async signInWithPassword(email: string, password: string): Promise<Session> {
    const { data, error } = await this.client.auth.signInWithPassword({ email, password });
    if (error) throw error;
    if (!data.session) throw new Error('Nao foi possivel obter uma sessao apos o login.');
    this.explicitlySignedOut = false;
    this.setSession(data.session);
    return data.session;
  }

  async signUp(email: string, password: string): Promise<Session | null> {
    const { data, error } = await this.client.auth.signUp({ email, password });
    if (error) throw error;
    if (data.session) {
      this.explicitlySignedOut = false;
      this.setSession(data.session);
    }
    return data.session;
  }

  async resetPassword(email: string): Promise<void> {
    const { error } = await this.client.auth.resetPasswordForEmail(email);
    if (error) throw error;
  }

  // --- Google OAuth Methods (ECO-2606) ---

  /**
   * Inicia login direto com o Google via signInWithOAuth.
   */
  async signInWithGoogle(redirectTo?: string): Promise<{ url?: string }> {
    const targetRedirect = redirectTo ?? getOAuthRedirectUri();
    const { data, error } = await this.client.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: targetRedirect,
        skipBrowserRedirect: false,
      },
    });
    if (error) throw error;
    return { url: data?.url ?? undefined };
  }

  /**
   * Vincula a identidade Google a conta atual (guest) via linkIdentity.
   */
  async linkGoogleAccount(redirectTo?: string): Promise<{ url?: string }> {
    const targetRedirect = redirectTo ?? getOAuthRedirectUri();
    const { data, error } = await this.client.auth.linkIdentity({
      provider: 'google',
      options: {
        redirectTo: targetRedirect,
      },
    });
    if (error) throw error;
    return { url: data?.url ?? undefined };
  }

  /**
   * Identifica se um erro recebido corresponde a conflito de conta Google existente.
   */
  isIdentityConflictError(err: unknown): boolean {
    if (!err) return false;
    const msg = (err instanceof Error ? err.message : String(err)).toLowerCase();
    const code = typeof err === 'object' && err !== null && 'code' in err ? String((err as any).code).toLowerCase() : '';
    return (
      code.includes('already_exists') ||
      code.includes('already_registered') ||
      code.includes('identities_conflict') ||
      code.includes('manual_linking_disabled') ||
      msg.includes('already_exists') ||
      msg.includes('already exists') ||
      msg.includes('already registered') ||
      msg.includes('already_registered') ||
      msg.includes('already linked') ||
      msg.includes('already_linked') ||
      msg.includes('user already registered') ||
      msg.includes('identity already belongs') ||
      msg.includes('manual_linking_disabled')
    );
  }

  /**
   * Processa explicitamente um callback OAuth (troca de auth code PKCE ou tokens).
   */
  async handleOAuthCallback(params: ParsedOAuthCallback): Promise<Session | null> {
    if (params.type === 'cancel') {
      throw new Error(params.errorDescription || 'Autenticacao com Google cancelada pelo usuario.');
    }
    if (params.type === 'error') {
      throw new Error(params.errorDescription || params.error || 'Falha na autenticacao com Google.');
    }
    if (params.type === 'success' && params.code) {
      const { data, error } = await this.client.auth.exchangeCodeForSession(params.code);
      if (error) throw error;
      if (data?.session) {
        this.explicitlySignedOut = false;
        this.setSession(data.session);
        return data.session;
      }
    }
    if (params.type === 'success' && params.accessToken) {
      const { data, error } = await this.client.auth.setSession({
        access_token: params.accessToken,
        refresh_token: params.refreshToken || '',
      });
      if (error) throw error;
      if (data?.session) {
        this.explicitlySignedOut = false;
        this.setSession(data.session);
        return data.session;
      }
    }
    return null;
  }

  // --- Snapshot e Preservacao de Favoritos Guest (ADR 0007 / ECO-2606) ---

  async saveGuestFavoritesSnapshot(snapshot: GuestFavoritesSnapshot): Promise<void> {
    await authStorage.setItem(GUEST_SNAPSHOT_STORAGE_KEY, JSON.stringify(snapshot));
  }

  async getGuestFavoritesSnapshot(): Promise<GuestFavoritesSnapshot | null> {
    try {
      const raw = await authStorage.getItem(GUEST_SNAPSHOT_STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw) as GuestFavoritesSnapshot;
    } catch {
      return null;
    }
  }

  async clearGuestFavoritesSnapshot(): Promise<void> {
    await authStorage.removeItem(GUEST_SNAPSHOT_STORAGE_KEY);
  }

  /**
   * Reconcilia os favoritos do snapshot guest na conta identificada ativa.
   * Utiliza chamadas idempotentes para cada rota e ator favoritado.
   */
  async reconcileGuestFavorites(apiClient: {
    addFavoriteRoute: (id: string) => Promise<any>;
    addFavoriteActor: (id: string) => Promise<any>;
  }): Promise<{ routesPreserved: number; actorsPreserved: number }> {
    const snapshot = await this.getGuestFavoritesSnapshot();
    if (!snapshot) {
      return { routesPreserved: 0, actorsPreserved: 0 };
    }

    let routesPreserved = 0;
    let actorsPreserved = 0;

    for (const routeId of snapshot.favoriteRouteIds) {
      try {
        await apiClient.addFavoriteRoute(routeId);
        routesPreserved += 1;
      } catch {
        // Idempotente / continua para proximos
      }
    }

    for (const actorId of snapshot.favoriteActorIds) {
      try {
        await apiClient.addFavoriteActor(actorId);
        actorsPreserved += 1;
      } catch {
        // Idempotente / continua para proximos
      }
    }

    await this.clearGuestFavoritesSnapshot();
    return { routesPreserved, actorsPreserved };
  }

  async signOut(): Promise<void> {
    this.invalidateSession();
    await this.clearGuestFavoritesSnapshot();
    const { error } = await this.client.auth.signOut({ scope: 'local' });
    if (error) throw error;
  }
}
