import type { Metadata, Viewport } from "next";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Inter, JetBrains_Mono } from "next/font/google";
import { notFound } from "next/navigation";

import { routing } from "@/i18n/routing";
import { THEME_INIT_SCRIPT } from "@/lib/theme";

import "../globals.css";

// Cyrillic is not optional here: without the subset, Ukrainian falls back to a
// system font part-way down the page while Latin text keeps Inter.
const sans = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin", "cyrillic"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export function generateStaticParams(): { locale: string }[] {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: LayoutProps<"/[locale]">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "landing" });

  return {
    title: { default: "AI Workspace", template: "%s · AI Workspace" },
    description: t("description"),
  };
}

export const viewport: Viewport = {
  // Matches --color-bg in each theme, so the browser chrome does not flash a
  // different colour than the page behind it.
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0d1116" },
  ],
};

export default async function LocaleLayout({ children, params }: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  // An unknown segment is a 404, not a fallback: /fr/workspace should not
  // silently serve English at a URL that claims otherwise.
  if (!hasLocale(routing.locales, locale)) notFound();

  // Required for the static rendering of this segment.
  setRequestLocale(locale);

  return (
    // suppressHydrationWarning: the theme script sets data-theme on this element
    // before hydration, which the server render cannot know about.
    <html lang={locale} className={`${sans.variable} ${mono.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <NextIntlClientProvider>{children}</NextIntlClientProvider>
      </body>
    </html>
  );
}
