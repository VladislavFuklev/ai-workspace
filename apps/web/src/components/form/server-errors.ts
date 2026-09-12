import type { FieldValues, Path, UseFormSetError } from "react-hook-form";
import { z } from "zod";

import { ApiError } from "@/lib/api";

/**
 * The API's field-error envelope. Mirrors FastAPI's validation shape closely
 * enough to be mapped without the backend having to invent a second one.
 */
const fieldErrors = z.array(z.object({ field: z.string(), message: z.string() }));

/**
 * Puts server-side validation errors back on the fields that caused them.
 *
 * Without this a 422 becomes a banner saying "invalid input" above a form the
 * user then has to re-read. Anything that does not name a known field is left to
 * the caller to show as a form-level error.
 *
 * Returns true when at least one error was placed on a field.
 */
export function applyServerErrors<TValues extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<TValues>,
  knownFields: readonly Path<TValues>[],
): boolean {
  if (!(error instanceof ApiError) || error.status !== 422) return false;

  const parsed = fieldErrors.safeParse(error.detail);
  if (!parsed.success || parsed.data.length === 0) return false;

  let placed = false;
  for (const item of parsed.data) {
    const field = item.field as Path<TValues>;
    if (!knownFields.includes(field)) continue;
    setError(field, { type: "server", message: item.message });
    placed = true;
  }
  return placed;
}
