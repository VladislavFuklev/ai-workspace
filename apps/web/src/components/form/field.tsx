"use client";

import { useId, type ReactNode } from "react";

/**
 * The wiring every field needs and every field gets wrong when written by hand:
 * a label bound to the control, a description and an error message that the
 * control actually points at, and `aria-invalid` so the state is not carried by
 * colour alone.
 *
 * The control is a render prop rather than a wrapped `<input>`, so selects,
 * textareas and comboboxes get the same treatment without a component each.
 */
export function Field({
  label,
  description,
  error,
  required,
  children,
}: {
  label: string;
  description?: string;
  error?: string;
  required?: boolean;
  children: (props: {
    id: string;
    "aria-describedby": string | undefined;
    "aria-invalid": boolean | undefined;
    "aria-required": boolean | undefined;
  }) => ReactNode;
}) {
  const id = useId();
  const descriptionId = description ? `${id}-description` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  // Both, in reading order: the hint first, then what went wrong.
  const describedBy = [descriptionId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-text">
        {label}
        {required ? (
          <span className="ml-1 text-danger" aria-hidden="true">
            *
          </span>
        ) : null}
      </label>

      {description ? (
        <p id={descriptionId} className="text-xs text-text-muted">
          {description}
        </p>
      ) : null}

      {children({
        id,
        "aria-describedby": describedBy,
        "aria-invalid": error ? true : undefined,
        "aria-required": required || undefined,
      })}

      {error ? (
        // Announced when it appears, rather than silently turning the border red.
        <p id={errorId} role="alert" className="text-xs font-medium text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}
