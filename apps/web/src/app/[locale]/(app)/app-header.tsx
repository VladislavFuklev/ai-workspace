import { getTranslations } from "next-intl/server";

import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { SignOutButton } from "@/features/auth/sign-out-button";
import { Link } from "@/i18n/navigation";

/**
 * The header for every signed-in page, whether or not one is inside an
 * organisation.
 *
 * `/organizations` has no shell to sit in — there is no organisation to
 * navigate — but it still needs the same way out: language, theme, sign out.
 * Two copies of that drift apart.
 *
 * It lives beside the routes rather than in `components/`: it composes a feature
 * (signing out), and the layering rule keeps that dependency out of the shared
 * component layer.
 */
export async function AppHeader({
  userName,
  children,
}: {
  userName: string;
  /** The organisation switcher, where there is one to switch. */
  children?: React.ReactNode;
}) {
  const t = await getTranslations("common");

  return (
    <>
      <Link
        href="/enter"
        className="rounded-sm text-sm font-semibold tracking-tight text-text hover:text-accent"
      >
        {t("appName")}
      </Link>
      {children}
      <div className="ml-auto flex items-center gap-2">
        <span className="hidden text-sm text-text-muted sm:inline">{userName}</span>
        <LocaleSwitcher />
        <ThemeToggle />
        <SignOutButton />
      </div>
    </>
  );
}
