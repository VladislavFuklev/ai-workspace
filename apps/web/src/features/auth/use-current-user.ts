"use client";

import { useQuery } from "@tanstack/react-query";

import { ApiError } from "@/lib/api";
import { queryKeys } from "@/lib/query";

import { fetchCurrentUser } from "./api";

/**
 * Who is signed in, or `null`.
 *
 * A 401 is not an error here — it is the answer "nobody". Letting it through as
 * an error would put a red banner on every signed-out page.
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.auth.currentUser(),
    queryFn: async () => {
      try {
        return await fetchCurrentUser();
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    // The session outlives a navigation; refetching on every mount would put a
    // request on the critical path of every page.
    staleTime: 5 * 60_000,
  });
}
