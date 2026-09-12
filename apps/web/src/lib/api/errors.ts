import { z } from "zod";

/**
 * Every failure the client can produce, as one type.
 *
 * A caller should never have to distinguish "fetch threw", "the server returned
 * 500" and "the body did not match the schema" by inspecting shapes. `kind` is
 * the discriminator, and `message` is safe to show a user.
 */
export type ApiErrorKind =
  | "network" // the request never completed
  | "timeout" // it took longer than the budget
  | "http" // the server answered with a failure status
  | "parse" // the body did not match what the caller expected
  | "unknown";

/** The error envelope the API is expected to return. Mirrors the backend's
 *  contract from task 2.8; unknown shapes fall back to the status text. */
const apiErrorBody = z.object({
  code: z.string().optional(),
  message: z.string().optional(),
  detail: z.unknown().optional(),
});

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  /** Machine-readable code from the server, for branching in a caller. */
  readonly code?: string;
  readonly requestId?: string;

  constructor(init: {
    kind: ApiErrorKind;
    message: string;
    status?: number;
    code?: string;
    requestId?: string;
    cause?: unknown;
  }) {
    super(init.message, { cause: init.cause });
    this.name = "ApiError";
    this.kind = init.kind;
    this.status = init.status;
    this.code = init.code;
    this.requestId = init.requestId;
  }

  /** Retrying a 4xx just fails again; a timeout or a 5xx might not. */
  get isRetryable(): boolean {
    if (this.kind === "network" || this.kind === "timeout") return true;
    return this.status !== undefined && this.status >= 500;
  }
}

/** Turns a failure response into an ApiError without trusting its body. */
export async function errorFromResponse(response: Response): Promise<ApiError> {
  let code: string | undefined;
  let message: string | undefined;
  try {
    const parsed = apiErrorBody.safeParse(await response.json());
    if (parsed.success) {
      code = parsed.data.code;
      message = parsed.data.message;
    }
  } catch {
    // A failure response with no JSON body is normal — a proxy timeout, an
    // HTML error page. The status is still meaningful.
  }
  return new ApiError({
    kind: "http",
    status: response.status,
    code,
    message: message ?? `Request failed with status ${response.status}`,
    requestId: response.headers.get("x-request-id") ?? undefined,
  });
}
