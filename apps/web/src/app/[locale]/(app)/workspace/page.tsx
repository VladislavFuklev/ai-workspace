import { getTranslations } from "next-intl/server";

export async function generateMetadata() {
  const t = await getTranslations("workspace");
  return { title: t("title") };
}

export default async function WorkspacePage() {
  const t = await getTranslations("workspace");

  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">{t("title")}</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">{t("description")}</p>
    </div>
  );
}
