import { cookies } from "next/headers";

import { env } from "@/lib/env";

import { userProfileSchema, type UserProfile } from "./schemas";

/**
 * Who is signed in, asked from a Server Component.
 *
 * The session cookie is `HttpOnly`, so the server can read it but no script
 * can. Forwarding it to the API is the only way to know who the caller is —
 * the web app has no signing key and must not have one.
 *
 * This is the *real* guard. The middleware check is a cheap redirect that only
 * looks at whether a cookie is present; a present cookie proves nothing.
 */
export async function getServerUser(): Promise<UserProfile | null> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) return null;

  let response: Response;
  try {
    response = await fetch(`${env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")}/api/v1/auth/me`, {
      headers: { cookie: cookieHeader, accept: "application/json" },
      // Never cached: the answer is per-user, and a cached one would be served
      // to the wrong person.
      cache: "no-store",
    });
  } catch {
    // The API being unreachable is not "signed out", but there is nothing
    // useful to render either. The layout treats it as unauthenticated.
    return null;
  }

  if (!response.ok) return null;

  const parsed = userProfileSchema.safeParse(await response.json());
  return parsed.success ? parsed.data : null;
}
