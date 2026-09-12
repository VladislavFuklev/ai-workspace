import { getTranslations } from "next-intl/server";

import { AppShell } from "@/components/layout/app-shell";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { Link } from "@/i18n/navigation";
import { QueryProvider } from "@/lib/query";

/**
 * Server Component: it composes the shell but holds no state.
 *
 * LayoutProps<"/[locale]"> — route groups create no URL segment, so this layout
 * sits at the locale segment even though it wraps /workspace and its siblings.
 */
export default async function AppLayout({ children }: LayoutProps<"/[locale]">) {
  const t = await getTranslations("common");

  return (
    <QueryProvider>
      <AppShell
        header={
          <>
            <Link
              href="/"
              className="rounded-sm text-sm font-semibold tracking-tight text-text hover:text-accent"
            >
              {t("appName")}
            </Link>
            <div className="ml-auto flex items-center gap-2">
              <LocaleSwitcher />
              <ThemeToggle />
            </div>
          </>
        }
      >
        {children}
      </AppShell>
    </QueryProvider>
  );
}
