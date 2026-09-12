"use client";

import Link from "next/link";
import { useSelectedLayoutSegment } from "next/navigation";

const PAGES = [
  { segment: "design", href: "/design", label: "Tokens" },
  { segment: "components", href: "/components", label: "Components" },
  { segment: "forms", href: "/forms", label: "Forms" },
];

export function DevNav() {
  const segment = useSelectedLayoutSegment();
  return (
    <nav aria-label="Reference pages" className="ml-auto flex items-center gap-1">
      {PAGES.map((page) => {
        const current = page.segment === segment;
        return (
          <Link
            key={page.segment}
            href={page.href}
            aria-current={current ? "page" : undefined}
            className={[
              "rounded-md px-2.5 py-1.5 text-sm transition-colors duration-fast",
              current
                ? "bg-accent-subtle font-medium text-accent"
                : "text-text-muted hover:bg-surface-muted hover:text-text",
            ].join(" ")}
          >
            {page.label}
          </Link>
        );
      })}
    </nav>
  );
}
