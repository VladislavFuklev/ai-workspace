"use client";

import { Spinner } from "@/components/ui";

/**
 * Disabled while pending, with the reason visible and announced. A submit that
 * looks idle while a request is in flight gets clicked again.
 */
export function SubmitButton({
  children,
  pending,
  pendingLabel,
}: {
  children: React.ReactNode;
  pending?: boolean;
  pendingLabel: string;
}) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex items-center gap-2 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors duration-fast hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? <Spinner label={pendingLabel} /> : null}
      {pending ? pendingLabel : children}
    </button>
  );
}
