"use client";

import type { ReactNode } from "react";

/**
 * An inline failure: one region could not load, but the page around it still works.
 *
 * The message is written for the person reading it, and never carries raw error
 * text — that is how internal detail reaches a screenshot. `reference` is for a
 * digest or request id, which is what support actually needs.
 *
 * role="alert" so the failure is announced rather than silently replacing content.
 */
export function ErrorState({
  title = "Something went wrong",
  description = "This could not be loaded. Trying again is often enough.",
  reference,
  onRetry,
  action,
}: {
  title?: string;
  description?: string;
  reference?: string;
  onRetry?: () => void;
  action?: ReactNode;
}) {
  return (
    <div role="alert" className="rounded-lg border border-danger-subtle bg-danger-subtle p-4">
      <h2 className="text-sm font-semibold text-danger">{title}</h2>
      <p className="mt-1 max-w-prose text-sm text-text-muted">{description}</p>
      {reference ? (
        <p className="mt-2 font-mono text-xs text-text-subtle">Reference: {reference}</p>
      ) : null}
      {onRetry || action ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors duration-fast hover:bg-accent-hover"
            >
              Try again
            </button>
          ) : null}
          {action}
        </div>
      ) : null}
    </div>
  );
}
