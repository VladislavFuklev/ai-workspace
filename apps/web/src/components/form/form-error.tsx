"use client";

import { ApiError } from "@/lib/api";

/**
 * A failure that belongs to the form as a whole rather than to one field.
 *
 * Field-level problems from the server are mapped onto their fields by
 * `applyServerErrors`; this is what is left — a conflict, a rate limit, an
 * outage.
 */
export function FormError({ error }: { error: unknown }) {
  if (!error) return null;
  const message =
    error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
  const reference = error instanceof ApiError ? error.requestId : undefined;

  return (
    <div role="alert" className="rounded-md border border-danger-subtle bg-danger-subtle p-3">
      <p className="text-sm font-medium text-danger">{message}</p>
      {reference ? (
        <p className="mt-1 font-mono text-xs text-text-subtle">Reference: {reference}</p>
      ) : null}
    </div>
  );
}
