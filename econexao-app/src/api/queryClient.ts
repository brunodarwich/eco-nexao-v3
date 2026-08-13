import { QueryClient } from '@tanstack/react-query';

import { ApiClientError } from './client';

export function shouldRetry(failureCount: number, error: Error): boolean {
  if (failureCount >= 2) return false;
  if (error instanceof ApiClientError) {
    return error.status === 0 || error.status >= 500;
  }
  return true;
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        gcTime: 30 * 60_000,
        retry: shouldRetry,
        refetchOnReconnect: true,
      },
      mutations: { retry: false },
    },
  });
}

export function removeAuthenticatedQueries(client: QueryClient): void {
  client.removeQueries({ predicate: (query) => query.meta?.authenticated === true });
}

export const queryClient = createQueryClient();
