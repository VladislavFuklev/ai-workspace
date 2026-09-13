import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

/**
 * Placeholder for the public landing page (task 14.1). It owns `/` so the
 * authenticated product, which lives under concrete routes, never collides
 * with it at the root.
 */
export default async function LandingPage() {
  const t = await getTranslations("landing");

  return (
    <main className="mx-auto flex min-h-dvh max-w-3xl flex-col justify-center px-4 py-16 sm:px-6 lg:px-8">
      <p className="font-mono text-xs tracking-wide text-text-subtle uppercase">{t("eyebrow")}</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-text">{t("title")}</h1>
      <p className="mt-3 max-w-prose text-sm text-text-muted">{t("description")}</p>
      <div className="mt-7 flex flex-wrap gap-3">
        <Link
          href="/enter"
          className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors duration-fast hover:bg-accent-hover"
        >
          {t("openWorkspace")}
        </Link>
        <Link
          href="/design"
          className="rounded-md border border-border-strong px-3 py-1.5 text-sm font-medium text-text transition-colors duration-fast hover:bg-surface-muted"
        >
          {t("designTokens")}
        </Link>
      </div>
    </main>
  );
}
