import { getTranslations } from "next-intl/server";

import { EmptyState } from "@/components/ui";

export async function generateMetadata() {
  const t = await getTranslations("assistant");
  return { title: t("title") };
}

export default async function AssistantPage() {
  const t = await getTranslations("assistant");
  const tc = await getTranslations();

  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">{t("title")}</h1>
      <div className="mt-6">
        <EmptyState
          title={t("emptyTitle")}
          description={t("emptyDescription")}
          action={
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-md border border-border px-3 py-1.5 text-sm font-medium text-text-subtle"
            >
              {tc("comingSoon", { feature: t("emptyAction"), phase: 7 })}
            </button>
          }
        />
      </div>
    </div>
  );
}
