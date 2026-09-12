import { env } from "@/lib/env";

import { createApiClient } from "./client";

/**
 * The configured client. Everything in the app uses this; `createApiClient` is
 * for exercising the transport against a stub.
 */
export const api = createApiClient({ baseUrl: env.NEXT_PUBLIC_API_URL });

export { createApiClient, type ApiClient, type RequestOptions } from "./client";
export { ApiError, errorFromResponse, type ApiErrorKind } from "./errors";
