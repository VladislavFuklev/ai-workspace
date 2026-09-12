import { getTranslations } from "next-intl/server";

import { Skeleton, SkeletonText } from "@/components/ui";

/** Shown while any route under (app) streams. */
export default async function Loading() {
  const t = await getTranslations("states");

  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8" aria-busy="true">
      <span className="sr-only">{t("loading")}</span>
      <Skeleton className="h-8 w-48" />
      <SkeletonText className="mt-4" lines={2} />
    </div>
  );
}
