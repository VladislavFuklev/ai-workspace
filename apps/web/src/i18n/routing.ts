import { defineRouting } from "next-intl/routing";

/**
 * Locale routing.
 *
 * The locale is always in the path (`/en/workspace`, `/uk/workspace`) rather
 * than only in a cookie. A URL then names exactly one page in one language,
 * which matters for sharing a link, for a CDN cache key, and for a bug report
 * that says "this page" — none of which work when the language is invisible.
 */
export const routing = defineRouting({
  locales: ["en", "uk"],
  defaultLocale: "en",
  localePrefix: "always",
  // The chosen locale is remembered, so a return visit does not re-negotiate.
  localeCookie: {
    name: "ai-workspace-locale",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  },
});

export type Locale = (typeof routing.locales)[number];

/** Written in their own language: a switcher that says "Ukrainian" to someone
 *  who does not read English is not a way out. */
export const LOCALE_LABELS: Record<Locale, string> = {
  en: "English",
  uk: "Українська",
};
