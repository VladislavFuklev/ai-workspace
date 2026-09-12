import type { z } from "zod";

import { ApiError, errorFromResponse } from "./errors";

/**
 * The single way the web app talks to the API.
 *
 * Nothing else calls `fetch` against the API: base URL, timeout, credentials,
 * error normalisation and response validation belong in one place, or each call
 * site invents its own subtly different version.
 *
 * Responses are parsed with a Zod schema at the boundary (ADR-005: the two sides
 * share no types, so the contract has to be checked rather than asserted).
 *
 * A factory rather than a module-level singleton, so the base URL is an argument.
 * That keeps this file free of configuration imports and makes it exercisable
 * against a stub server without mocking a module. The configured instance lives
 * in `./index.ts`.
 */
const DEFAULT_TIMEOUT_MS = 15_000;

export type RequestOptions<TSchema extends z.ZodType> = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  /** Serialised as JSON. Use `formData` for uploads. */
  body?: unknown;
  formData?: FormData;
  searchParams?: Record<string, string | number | boolean | undefined>;
  /** Validates the response body. Omit for endpoints that return nothing. */
  schema?: TSchema;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeoutMs?: number;
};

function buildUrl(
  baseUrl: string,
  path: string,
  searchParams?: RequestOptions<z.ZodType>["searchParams"],
): string {
  const url = new URL(path.replace(/^\//, ""), `${baseUrl.replace(/\/$/, "")}/`);
  for (const [key, value] of Object.entries(searchParams ?? {})) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }
  return url.toString();
}

export type ApiClient = <TSchema extends z.ZodType>(
  path: string,
  options?: RequestOptions<TSchema>,
) => Promise<TSchema extends z.ZodType<infer TOut> ? TOut : undefined>;

export function createApiClient({ baseUrl }: { baseUrl: string }): ApiClient {
  return async function apiRequest<TSchema extends z.ZodType>(
    path: string,
    options: RequestOptions<TSchema> = {},
  ): Promise<TSchema extends z.ZodType<infer TOut> ? TOut : undefined> {
    const {
      method = "GET",
      body,
      formData,
      searchParams,
      schema,
      headers = {},
      signal,
      timeoutMs = DEFAULT_TIMEOUT_MS,
    } = options;

    // Every request is bounded. An unbounded fetch is a hung UI with no error to
    // show. The caller's own signal still wins if it aborts first.
    const timeout = AbortSignal.timeout(timeoutMs);
    const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;

    let response: Response;
    try {
      response = await fetch(buildUrl(baseUrl, path, searchParams), {
        method,
        signal: combined,
        // Session cookies are the auth mechanism from phase 3.
        credentials: "include",
        headers: {
          Accept: "application/json",
          ...(formData ? {} : body !== undefined ? { "Content-Type": "application/json" } : {}),
          ...headers,
        },
        body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
      });
    } catch (cause) {
      if (timeout.aborted) {
        throw new ApiError({ kind: "timeout", message: "The request took too long.", cause });
      }
      if (signal?.aborted) throw cause; // the caller cancelled; not our error
      throw new ApiError({
        kind: "network",
        message: "Could not reach the server. Check your connection.",
        cause,
      });
    }

    if (!response.ok) throw await errorFromResponse(response);

    if (!schema) return undefined as never;

    let payload: unknown;
    try {
      payload = await response.json();
    } catch (cause) {
      throw new ApiError({
        kind: "parse",
        message: "The server sent an unreadable response.",
        cause,
      });
    }

    const parsed = schema.safeParse(payload);
    if (!parsed.success) {
      // The contract broke. Loud in development, generic to the user — a Zod issue
      // list describes internal shapes.
      if (process.env.NODE_ENV !== "production") {
        console.error(
          `Response from ${method} ${path} did not match its schema`,
          parsed.error.issues,
        );
      }
      throw new ApiError({
        kind: "parse",
        message: "The server sent an unexpected response.",
        cause: parsed.error,
      });
    }
    return parsed.data as never;
  };
}
