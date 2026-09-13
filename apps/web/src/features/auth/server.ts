import { cache } from "react";

import { serverGet } from "@/lib/api/server";

import { userProfileSchema, type UserProfile } from "./schemas";

/**
 * Who is signed in, asked from a Server Component.
 *
 * This is the *real* guard. The middleware check is a cheap redirect that only
 * looks at whether a cookie is present; a present cookie proves nothing.
 *
 * Every failure collapses to `null` here: an unreachable API is not "signed
 * out", but there is nothing useful to render either, and the layout has only
 * one thing to do about it. Callers that must distinguish the two use
 * `serverGet` directly.
 *
 * Wrapped in React's `cache`, so the guard layout and the header below it ask
 * once per request rather than once per component. `no-store` fetches are not
 * deduplicated on their own.
 */
export const getServerUser = cache(async (): Promise<UserProfile | null> => {
  const result = await serverGet("/api/v1/auth/me", userProfileSchema);
  return result.ok ? result.data : null;
});
