import { QueryClientProvider, focusManager, onlineManager, useQueryClient } from '@tanstack/react-query';
import { useNetworkState } from 'expo-network';
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
  const networkState = useNetworkState();

  useEffect(() => {
    if (Platform.OS === 'web') return;
    const subscription = AppState.addEventListener('change', (state) => {
      focusManager.setFocused(state === 'active');
    });
    return () => subscription.remove();
  }, []);

  useEffect(() => {
    const isOnline =
      networkState.isConnected !== false && networkState.isInternetReachable !== false;
    onlineManager.setOnline(isOnline);
  }, [networkState.isConnected, networkState.isInternetReachable]);

  return (
    <QueryClientProvider client={queryClient}>
      <SessionCacheBoundary>{children}</SessionCacheBoundary>
    </QueryClientProvider>
  );
}
