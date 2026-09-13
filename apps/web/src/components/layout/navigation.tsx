"use client";

import { useTranslations } from "next-intl";
import { useParams, useSelectedLayoutSegment } from "next/navigation";

import { Link } from "@/i18n/navigation";

import { NAVIGATION_ITEMS } from "./navigation-items";

/**
 * Primary navigation, rendered in both the sidebar and the drawer.
 *
 * `useSelectedLayoutSegment` rather than `usePathname`: only the first segment
 * under (app) decides which destination is current, so a nested route such as
 * /documents/abc keeps Documents highlighted without any prefix matching.
 *
 * The current item is marked with `aria-current="page"`; the colour and the left
 * rule are secondary, because colour alone is not a state.
 *
 * Every destination is inside an organisation, so the slug from the route is
 * prefixed here rather than repeated in `NAVIGATION_ITEMS`.
 */
export function Navigation({
  label,
  onNavigate,
}: {
  /** Omitted inside the drawer: the <dialog> already names that region. */
  label?: string;
  /** Closes the drawer, so following a link does not leave it open over the page. */
  onNavigate?: () => void;
}) {
  const t = useTranslations("navigation");
  const segment = useSelectedLayoutSegment();
  const { organization } = useParams<{ organization: string }>();

  return (
    <nav aria-label={label} className="flex h-full flex-col gap-0.5 p-3">
      {NAVIGATION_ITEMS.map((item) => {
        const current = item.segment === segment;
        return (
          <Link
            key={item.segment}
            href={`/${organization}${item.href}`}
            aria-current={current ? "page" : undefined}
            onClick={onNavigate}
            className={[
              "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors duration-fast",
              current
                ? "bg-accent-subtle font-medium text-accent"
                : "text-text-muted hover:bg-surface-muted hover:text-text",
            ].join(" ")}
          >
            <svg
              aria-hidden="true"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="size-5 shrink-0"
            >
              <path d={item.icon} />
            </svg>
            <span className="truncate">{t(item.labelKey)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
