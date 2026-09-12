"use client";

import { useTranslations } from "next-intl";
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
  const t = useTranslations("errors");
  const ts = useTranslations("states");

  useEffect(() => {
    // Replaced by the error-tracking boundary in task 11.7.
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6 lg:px-8">
      <ErrorState
        title={t("pageTitle")}
        description={t("pageDescription")}
        reference={error.digest}
        referenceLabel={ts("reference")}
        retryLabel={ts("retry")}
        onRetry={retry}
      />
    </div>
  );
}
