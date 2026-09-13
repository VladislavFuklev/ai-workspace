import { cookies } from "next/headers";
import type { z } from "zod";

import { env } from "@/lib/env";

/**
 * Reading the API from a Server Component.
 *
 * The browser client in `./client.ts` cannot be used here: it relies on the
 * browser attaching cookies, and on the server there is no browser. The session
 * cookie is `HttpOnly`, so forwarding the incoming one is the only way for a
 * Server Component to ask a question as the person who made the request.
 *
 * The result is a discriminated union rather than `T | null` because the layouts
 * need to tell "you may not see this" (404 → not-found) from "the API is down"
 * (→ an error boundary). Collapsing both into `null` renders an empty page for
 * an outage, which looks like an answer.
 */
export type ServerResult<T> =
  | { ok: true; data: T }
  /** `status` is null when the request never produced a response at all. */
  | { ok: false; status: number | null };

export async function serverGet<TSchema extends z.ZodType>(
  path: string,
  schema: TSchema,
): Promise<ServerResult<z.infer<TSchema>>> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) return { ok: false, status: 401 };

  let response: Response;
  try {
    response = await fetch(`${env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")}${path}`, {
      headers: { cookie: cookieHeader, accept: "application/json" },
      // Never cached: every answer here is per-user, and a cached one would be
      // served to the wrong person.
      cache: "no-store",
    });
  } catch {
    return { ok: false, status: null };
  }

  if (!response.ok) return { ok: false, status: response.status };

  const parsed = schema.safeParse(await response.json().catch(() => null));
  if (!parsed.success) {
    if (process.env.NODE_ENV !== "production") {
      console.error(`Response from GET ${path} did not match its schema`, parsed.error.issues);
    }
    return { ok: false, status: null };
  }
  return { ok: true, data: parsed.data };
}
