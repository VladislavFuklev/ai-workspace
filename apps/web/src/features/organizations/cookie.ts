/**
 * The last organisation this browser looked at.
 *
 * Not authority over anything: the URL says which organisation is being shown,
 * and the API decides whether the caller may see it. This only answers "where
 * should signing in land me", so a stale or forged value costs a redirect to a
 * not-found page and nothing else.
 *
 * Written by the middleware, which already sees every path, rather than by a
 * server action — no round trip, and no client JavaScript to get it wrong.
 */
export const ORGANIZATION_COOKIE = "ai_workspace_org";
