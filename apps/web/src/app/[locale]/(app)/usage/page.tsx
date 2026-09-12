import { getTranslations } from "next-intl/server";

import { EmptyState } from "@/components/ui";

export async function generateMetadata() {
  const t = await getTranslations("usage");
  return { title: t("title") };
}

export default async function UsagePage() {
  const t = await getTranslations("usage");

  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">{t("title")}</h1>
      <div className="mt-6">
        <EmptyState title={t("emptyTitle")} description={t("emptyDescription")} />
      </div>
    </div>
  );
}
