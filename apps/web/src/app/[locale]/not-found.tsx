import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

export default async function NotFound() {
  const t = await getTranslations("errors");

  return (
    <div className="mx-auto flex min-h-dvh max-w-2xl flex-col justify-center px-4 py-16 sm:px-6 lg:px-8">
      <p className="font-mono text-xs tracking-wide text-text-subtle uppercase">
        {t("notFoundEyebrow")}
      </p>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight text-text">{t("notFoundTitle")}</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">{t("notFoundDescription")}</p>
      <div className="mt-6">
        <Link
          href="/"
          className="inline-block rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors duration-fast hover:bg-accent-hover"
        >
          {t("backToWorkspace")}
        </Link>
      </div>
    </div>
  );
}
