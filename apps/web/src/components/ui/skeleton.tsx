/**
 * A placeholder shaped like the content it stands in for, so nothing moves when
 * the real thing arrives. A centred spinner on a blank page is not a loading
 * state — it tells the user nothing about what is coming.
 *
 * Hidden from assistive technology: the surrounding region announces "busy", and
 * a screen reader gains nothing from a description of grey rectangles.
 */
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden="true" className={`animate-pulse rounded-md bg-surface-muted ${className}`} />
  );
}

/** Several lines of placeholder text, the last one short like real prose. */
export function SkeletonText({
  lines = 3,
  className = "",
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {Array.from({ length: lines }, (_, index) => (
        <Skeleton key={index} className={index === lines - 1 ? "h-4 w-2/3" : "h-4 w-full"} />
      ))}
    </div>
  );
}
