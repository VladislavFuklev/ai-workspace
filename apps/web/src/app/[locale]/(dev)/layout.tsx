import { getTranslations } from "next-intl/server";

import { LocaleSwitcher } from "@/components/locale-switcher";
import { Link } from "@/i18n/navigation";

import { DevNav } from "./dev-nav";

/**
 * Internal reference surfaces — design tokens, component states, forms. Not part
 * of the product: grouped so it is never mistaken for one, and so a single place
 * can gate it when that matters.
 */
export default async function DevLayout({ children }: LayoutProps<"/[locale]">) {
  const t = await getTranslations("common");

  return (
    <div className="min-h-dvh bg-bg">
      <header className="sticky top-0 z-header border-b border-border bg-surface">
        <div className="mx-auto flex h-header max-w-5xl items-center gap-4 px-4 sm:px-6 lg:px-8">
          <Link
            href="/"
            className="rounded-sm text-sm font-semibold tracking-tight text-text hover:text-accent"
          >
            {t("appName")}
          </Link>
          <span
            className="rounded-sm bg-warning-subtle px-1.5 py-0.5 font-mono text-xs text-warning"
            title="Not part of the product"
          >
            {t("internal")}
          </span>
          <DevNav />
          <LocaleSwitcher />
        </div>
      </header>
      {children}
    </div>
  );
}
