import { QueryClientProvider, focusManager, useQueryClient } from '@tanstack/react-query';
import React, { useContext, useEffect, useRef } from 'react';
import { AppState, Platform } from 'react-native';

import { AuthContext } from '../auth/AuthProvider';
import { queryClient, removeAuthenticatedQueries } from './queryClient';

function SessionCacheBoundary({ children }: React.PropsWithChildren) {
  const auth = useContext(AuthContext);
  const client = useQueryClient();
  const previousUserId = useRef<string | null>(null);
  const userId = auth?.user?.id ?? null;

  useEffect(() => {
    if (previousUserId.current && previousUserId.current !== userId) {
      removeAuthenticatedQueries(client);
    }
    previousUserId.current = userId;
  }, [client, userId]);

  return <>{children}</>;
}

export function ServerStateProvider({ children }: React.PropsWithChildren) {
  useEffect(() => {
    if (Platform.OS === 'web') return;
    const subscription = AppState.addEventListener('change', (state) => {
      focusManager.setFocused(state === 'active');
    });
    return () => subscription.remove();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <SessionCacheBoundary>{children}</SessionCacheBoundary>
    </QueryClientProvider>
  );
}
