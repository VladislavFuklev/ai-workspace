"use client";

import { useEffect } from "react";

import { ErrorState } from "@/components/ui";

/**
 * Route-level error boundary. Next.js 16 passes `retry`, not `reset`.
 *
 * The copy is deliberately generic: `error.message` from a server component is
 * redacted in production anyway, and echoing raw error text is how internal
 * detail reaches a screenshot.
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
      <ErrorState
        title="This page could not be loaded"
        description="The problem has been recorded. Trying again is often enough."
        reference={error.digest}
        onRetry={retry}
      />
    </div>
  );
}
