import type { AuthChangeEvent, Session, SupabaseClient } from '@supabase/supabase-js';

export type SessionListener = (session: Session | null) => void;

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
    const restored = await this.client.auth.getSession();
    if (restored.error) throw restored.error;
    let session = restored.data.session;
    if (!session) {
      const signedIn = await this.client.auth.signInAnonymously();
      if (signedIn.error) throw signedIn.error;
      session = signedIn.data.session;
    }
    if (!session) throw new Error('O Supabase não retornou uma sessão válida.');
    if (generation !== this.generation) throw new Error('Inicialização de sessão cancelada.');
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
    if (!data.session) throw new Error('Não foi possível obter uma sessão após o login.');
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

  async signOut(): Promise<void> {
    this.invalidateSession();
    const { error } = await this.client.auth.signOut({ scope: 'local' });
    if (error) throw error;
  }
}

