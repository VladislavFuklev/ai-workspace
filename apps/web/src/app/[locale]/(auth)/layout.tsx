import { getTranslations } from "next-intl/server";

import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { Link } from "@/i18n/navigation";
import { QueryProvider } from "@/lib/query";

/**
 * The signed-out surface: sign in, sign up, reset.
 *
 * Its own group rather than part of `(app)`, which has a sidebar for navigation
 * that means nothing to someone who is not signed in yet.
 */
export default async function AuthLayout({ children }: LayoutProps<"/[locale]">) {
  const t = await getTranslations("common");

  return (
    <QueryProvider>
      <div className="flex min-h-dvh flex-col bg-bg">
        <header className="border-b border-border bg-surface">
          <div className="mx-auto flex h-header max-w-5xl items-center gap-3 px-4 sm:px-6">
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
          </div>
        </header>
        <main id="main" className="flex flex-1 items-start justify-center px-4 py-12 sm:py-16">
          <div className="w-full max-w-sm">{children}</div>
        </main>
      </div>
    </QueryProvider>
  );
}
