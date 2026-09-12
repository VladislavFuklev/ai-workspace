import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api";

/**
 * Cache policy for the whole app.
 *
 * Two decisions worth stating, because the defaults are wrong for this product:
 *
 * - **Retries respect `ApiError.isRetryable`.** The default retries everything
 *   three times, which turns a 403 into four 403s and a slow failure into a very
 *   slow one. Only a timeout, a network fault or a 5xx is worth repeating.
 * - **`staleTime` is 30s, not 0.** Documents and conversations do not change
 *   between a user's own actions, and a refetch on every mount makes the UI
 *   flicker for no new information. Mutations invalidate explicitly.
 */
const MAX_RETRIES = 2;

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        retry: (failureCount, error) => {
          if (error instanceof ApiError) return error.isRetryable && failureCount < MAX_RETRIES;
          return failureCount < MAX_RETRIES;
        },
        retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 8000),
        // Refetching whenever the window regains focus is right for a dashboard
        // and wrong while someone is reading a document. Opt in per query.
        refetchOnWindowFocus: false,
      },
      mutations: {
        // A mutation is a side effect. Repeating one that may already have
        // succeeded is worse than surfacing the error.
        retry: false,
      },
    },
  });
}
