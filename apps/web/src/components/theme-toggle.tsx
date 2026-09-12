"use client";

import { useTranslations } from "next-intl";
import { useEffect, useSyncExternalStore } from "react";

import {
  applyTheme,
  readServerTheme,
  readTheme,
  subscribeToTheme,
  writeTheme,
  type Theme,
} from "@/lib/theme";

const OPTIONS: { value: Theme; labelKey: string; icon: string }[] = [
  {
    value: "light",
    labelKey: "light",
    icon: "M10 2a.75.75 0 0 1 .75.75v1a.75.75 0 0 1-1.5 0v-1A.75.75 0 0 1 10 2m5.66 2.34a.75.75 0 0 1 0 1.06l-.7.71a.75.75 0 1 1-1.07-1.06l.71-.71a.75.75 0 0 1 1.06 0M18 10a.75.75 0 0 1-.75.75h-1a.75.75 0 0 1 0-1.5h1A.75.75 0 0 1 18 10m-2.34 5.66a.75.75 0 0 1-1.06 0l-.71-.7a.75.75 0 1 1 1.06-1.07l.71.71a.75.75 0 0 1 0 1.06M10 16.25a.75.75 0 0 1 .75.75v1a.75.75 0 0 1-1.5 0v-1a.75.75 0 0 1 .75-.75m-5.66-.59a.75.75 0 0 1 0-1.06l.7-.71a.75.75 0 0 1 1.07 1.06l-.71.71a.75.75 0 0 1-1.06 0M3.75 10.75h-1a.75.75 0 0 1 0-1.5h1a.75.75 0 0 1 0 1.5m1.29-5.4a.75.75 0 0 1 1.06-1.07l.71.71A.75.75 0 0 1 5.75 6.1zM10 6a4 4 0 1 0 0 8 4 4 0 0 0 0-8",
  },
  {
    value: "dark",
    labelKey: "dark",
    icon: "M9.35 2.19a.75.75 0 0 1 .27.82 6.5 6.5 0 0 0 7.37 8.24.75.75 0 0 1 .8 1.13A8 8 0 1 1 8.53 2.05a.75.75 0 0 1 .82.14",
  },
  {
    value: "system",
    labelKey: "system",
    icon: "M3 5.25A2.25 2.25 0 0 1 5.25 3h9.5A2.25 2.25 0 0 1 17 5.25v6.5A2.25 2.25 0 0 1 14.75 14h-3.5v1.5h2a.75.75 0 0 1 0 1.5h-6.5a.75.75 0 0 1 0-1.5h2V14h-3.5A2.25 2.25 0 0 1 3 11.75zm2.25-.75a.75.75 0 0 0-.75.75v6.5c0 .41.34.75.75.75h9.5a.75.75 0 0 0 .75-.75v-6.5a.75.75 0 0 0-.75-.75z",
  },
];

/**
 * Three-way theme control.
 *
 * A radiogroup rather than a toggle button: "system" is a real third state, and a
 * two-state toggle cannot express "follow the device".
 *
 * The value comes from an external store, so hydration starts from the server's
 * "system" and swaps to the real preference without a mismatch. The DOM attribute
 * is written in an effect, which is where synchronising React with the outside
 * world belongs.
 */
export function ThemeToggle() {
  const t = useTranslations("theme");
  const theme = useSyncExternalStore(subscribeToTheme, readTheme, readServerTheme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  return (
    <div
      role="radiogroup"
      aria-label={t("label")}
      className="flex items-center gap-0.5 rounded-md border border-border p-0.5"
    >
      {OPTIONS.map((option) => {
        const selected = theme === option.value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={t(option.labelKey)}
            title={t(option.labelKey)}
            onClick={() => writeTheme(option.value)}
            className={[
              "rounded-sm p-1.5 transition-colors duration-fast",
              selected
                ? "bg-surface-muted text-text"
                : "text-text-subtle hover:bg-surface-muted hover:text-text-muted",
            ].join(" ")}
          >
            <svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor" className="size-4">
              <path d={option.icon} />
            </svg>
          </button>
        );
      })}
    </div>
  );
}
