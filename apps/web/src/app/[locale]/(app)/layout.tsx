import { getTranslations } from "next-intl/server";

import { AppShell } from "@/components/layout/app-shell";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { SignOutButton } from "@/features/auth/sign-out-button";
import { getServerUser } from "@/features/auth/server";
import { Link } from "@/i18n/navigation";
import { QueryProvider } from "@/lib/query";
import { redirect } from "next/navigation";

/**
 * The guard for everything under (app).
 *
 * Asked on the server, before anything renders: a client-side check would flash
 * the page first and, more to the point, could be skipped entirely. The
 * middleware also redirects when there is no cookie at all, but that is only a
 * fast path — a cookie's presence proves nothing, and this is what verifies it.
 */
export default async function AppLayout({ children, params }: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  const [t, user] = await Promise.all([getTranslations("common"), getServerUser()]);

  if (!user) {
    // Next's own redirect, not the locale-aware one: it is typed as returning
    // `never`, so the compiler knows nothing below runs. The locale is already
    // in hand, so building the path costs nothing.
    redirect(`/${locale}/sign-in`);
  }

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
              <span className="hidden text-sm text-text-muted sm:inline">{user.display_name}</span>
              <LocaleSwitcher />
              <ThemeToggle />
              <SignOutButton />
            </div>
          </>
        }
      >
        {children}
      </AppShell>
    </QueryProvider>
  );
}
