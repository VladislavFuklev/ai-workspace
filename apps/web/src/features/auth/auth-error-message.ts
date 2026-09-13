import { ApiError } from "@/lib/api";

/**
 * Turns an `ApiError` into a key in the `auth` namespace.
 *
 * The API sends a stable `code` and never a translated message (ADR-015), so
 * this is where a failure becomes words — in the reader's language, and matching
 * the tone of the screen it appears on.
 */
export function authErrorKey(error: unknown): "failed" | "unavailable" | "unexpected" {
  if (!(error instanceof ApiError)) return "unexpected";

  switch (error.kind) {
    case "network":
    case "timeout":
      return "unavailable";
    case "http":
      // 401 is the deliberately generic sign-in failure (task 3.3).
      return error.status === 401 ? "failed" : "unexpected";
    default:
      return "unexpected";
  }
}
