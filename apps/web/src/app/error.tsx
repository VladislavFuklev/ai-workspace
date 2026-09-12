"use client";

import { useEffect } from "react";

/**
 * Route-level error boundary. Next.js 16 passes `retry`, not `reset`.
 *
 * The message shown is deliberately generic: `error.message` from a server
 * component is redacted in production anyway, and echoing raw error text is how
 * internal detail leaks into a UI.
 */
export default function RouteError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    // Replaced by the error-tracking boundary in task 11.7.
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="rounded-lg border border-border bg-surface p-6">
        <h1 className="text-xl font-semibold tracking-tight text-text">Something went wrong</h1>
        <p className="mt-2 text-sm text-text-muted">
          This page could not be loaded. The problem has been recorded — trying again is often
          enough.
        </p>
        {error.digest ? (
          <p className="mt-4 font-mono text-xs text-text-subtle">
            Reference: <span className="text-text-muted">{error.digest}</span>
          </p>
        ) : null}
        <button
          type="button"
          onClick={retry}
          className="mt-5 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors hover:bg-accent-hover"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
