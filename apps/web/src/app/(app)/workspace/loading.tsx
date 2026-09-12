/**
 * Shown while a route segment streams. A skeleton shaped like the content it
 * replaces, so nothing jumps when the real thing arrives — not a centred spinner.
 */
export default function Loading() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8" aria-busy="true">
      <span className="sr-only">Loading</span>
      <div className="h-8 w-48 animate-pulse rounded-md bg-surface-muted" />
      <div className="mt-3 h-4 w-full max-w-prose animate-pulse rounded-md bg-surface-muted" />
      <div className="mt-2 h-4 w-2/3 max-w-prose animate-pulse rounded-md bg-surface-muted" />
    </div>
  );
}
