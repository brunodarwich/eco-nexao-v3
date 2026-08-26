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
        gcTime: process.env.NODE_ENV === 'test' ? Infinity : 30 * 60_000,
        retry: shouldRetry,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: false,
        gcTime: process.env.NODE_ENV === 'test' ? Infinity : 30 * 60_000,
        // Execute the mutationFn so ApiClient can reject immediately with an
        // explicit offline error instead of silently queueing a write.
        networkMode: 'always',
      },
    },
  });
}

export function removeAuthenticatedQueries(client: QueryClient): void {
  client.removeQueries({ predicate: (query) => query.meta?.authenticated === true });
}

export const queryClient = createQueryClient();
