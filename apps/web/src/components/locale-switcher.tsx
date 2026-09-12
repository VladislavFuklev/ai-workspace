"use client";

import { useLocale } from "next-intl";
import { useTranslations } from "next-intl";
import { useTransition } from "react";

import { usePathname, useRouter } from "@/i18n/navigation";
import { LOCALE_LABELS, routing, type Locale } from "@/i18n/routing";

/**
 * Switches locale without leaving the page.
 *
 * `usePathname` from the locale-aware navigation returns the path *without* the
 * prefix, so replacing it with a different locale lands on the same page rather
 * than sending the reader back to the start.
 */
export function LocaleSwitcher() {
  const t = useTranslations("locale");
  const active = useLocale() as Locale;
  const pathname = usePathname();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  return (
    <div
      role="radiogroup"
      aria-label={t("label")}
      className="flex items-center gap-0.5 rounded-md border border-border p-0.5"
    >
      {routing.locales.map((locale) => {
        const selected = locale === active;
        return (
          <button
            key={locale}
            type="button"
            role="radio"
            aria-checked={selected}
            // The label is in its own language: "Ukrainian" is no help to
            // someone who cannot read the English interface they are stuck in.
            aria-label={LOCALE_LABELS[locale]}
            title={LOCALE_LABELS[locale]}
            disabled={isPending}
            onClick={() =>
              startTransition(() => {
                // `pathname` is already resolved and prefix-free, so it works
                // for dynamic routes too — no params to re-supply.
                router.replace(pathname, { locale });
              })
            }
            className={[
              "rounded-sm px-2 py-1 text-xs font-medium uppercase transition-colors duration-fast",
              selected
                ? "bg-surface-muted text-text"
                : "text-text-subtle hover:bg-surface-muted hover:text-text-muted",
            ].join(" ")}
          >
            {locale}
          </button>
        );
      })}
    </div>
  );
}
