import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { AppState, Platform } from 'react-native';
import type { Session, User } from '@supabase/supabase-js';

import { apiClient } from '../api/client';
import { AuthSessionManager } from './sessionManager';
import { supabase } from './supabase';

export type AuthStatus = 'initializing' | 'authenticated' | 'signed_out' | 'error';

export interface AuthContextValue {
  status: AuthStatus;
  session: Session | null;
  user: User | null;
  error: Error | null;
  retry: () => void;
  signOut: () => Promise<void>;
  linkEmail: (email: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const manager = new AuthSessionManager(supabase);

apiClient.configureAuth(
  () => manager.getAccessToken(),
  async () => (await manager.refresh())?.access_token ?? null,
  () => manager.invalidateSession()
);

export function AuthProvider({ children }: React.PropsWithChildren) {
  const [status, setStatus] = useState<AuthStatus>('initializing');
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(
    () =>
      manager.subscribe((nextSession) => {
        setSession(nextSession);
        if (nextSession) setStatus('authenticated');
        else setStatus((current) => (current === 'initializing' ? current : 'signed_out'));
      }),
    []
  );

  useEffect(() => {
    let active = true;
    setStatus('initializing');
    setError(null);
    manager.initialize().then(
      () => active && setStatus('authenticated'),
      (reason: unknown) => {
        if (!active) return;
        setError(reason instanceof Error ? reason : new Error('Falha ao iniciar sessão.'));
        setStatus('error');
      }
    );
    return () => {
      active = false;
    };
  }, [attempt]);

  useEffect(() => {
    const { data } = supabase.auth.onAuthStateChange((event, nextSession) => {
      manager.handleAuthEvent(event, nextSession);
    });
    if (Platform.OS === 'web') return () => data.subscription.unsubscribe();
    const appState = AppState.addEventListener('change', (nextState) => {
      if (nextState === 'active') void supabase.auth.startAutoRefresh();
      else void supabase.auth.stopAutoRefresh();
    });
    if (AppState.currentState === 'active') void supabase.auth.startAutoRefresh();
    return () => {
      appState.remove();
      data.subscription.unsubscribe();
      void supabase.auth.stopAutoRefresh();
    };
  }, []);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);
  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      session,
      user: session?.user ?? null,
      error,
      retry,
      signOut: () => manager.signOut(),
      linkEmail: (email) => manager.linkEmail(email),
    }),
    [error, retry, session, status]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
