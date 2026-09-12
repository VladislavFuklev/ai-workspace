import { Skeleton, SkeletonText } from "@/components/ui";

/** Shown while any route under (app) streams. */
export default function Loading() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8" aria-busy="true">
      <span className="sr-only">Loading</span>
      <Skeleton className="h-8 w-48" />
      <SkeletonText className="mt-4" lines={2} />
    </div>
  );
}
