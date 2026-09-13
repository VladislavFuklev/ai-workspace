"use client";

import { useTranslations } from "next-intl";
import { useSelectedLayoutSegment } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";

import { Link } from "@/i18n/navigation";

import type { Organization } from "./schemas";

/**
 * Which organisation is being shown, and how to change it.
 *
 * Switching keeps the section: someone looking at documents in one organisation
 * wants documents in the other, not a dashboard. `useSelectedLayoutSegment`
 * gives the section under this layout, so no path parsing is involved.
 *
 * A plain button and list rather than a `<dialog>` or the popover API: this has
 * to sit visually next to its trigger, and CSS anchor positioning is not yet
 * available everywhere. Escape and an outside press are handled here because
 * that is what the browser would otherwise have done.
 */
export function OrganizationSwitcher({
  current,
  organizations,
}: {
  current: Organization;
  organizations: Organization[];
}) {
  const t = useTranslations("organizations");
  const section = useSelectedLayoutSegment() ?? "workspace";
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    const onPointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };

    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((wasOpen) => !wasOpen)}
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={t("switcherLabel", { name: current.name })}
        className="flex max-w-48 items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-sm text-text transition-colors duration-fast hover:bg-surface-muted"
      >
        <span className="truncate font-medium">{current.name}</span>
        <svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor" className="size-4 shrink-0">
          <path d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06" />
        </svg>
      </button>

      {open ? (
        <div
          id={menuId}
          className="absolute top-full left-0 z-header mt-1 w-64 rounded-lg border border-border bg-surface p-1 shadow-lg"
        >
          <ul className="flex flex-col">
            {organizations.map((organization) => {
              const isCurrent = organization.slug === current.slug;
              return (
                <li key={organization.id}>
                  <Link
                    href={`/${organization.slug}/${section}`}
                    onClick={() => setOpen(false)}
                    aria-current={isCurrent ? "true" : undefined}
                    className={[
                      "flex items-center justify-between gap-2 rounded-md px-2.5 py-2 text-sm transition-colors duration-fast",
                      isCurrent
                        ? "bg-accent-subtle font-medium text-accent"
                        : "text-text hover:bg-surface-muted",
                    ].join(" ")}
                  >
                    <span className="truncate">{organization.name}</span>
                    <span className="shrink-0 text-xs text-text-muted">
                      {t(`roles.${organization.role}`)}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
          <div className="mt-1 border-t border-border pt-1">
            <Link
              href="/organizations"
              onClick={() => setOpen(false)}
              className="block rounded-md px-2.5 py-2 text-sm text-text-muted transition-colors duration-fast hover:bg-surface-muted hover:text-text"
            >
              {t("manage")}
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
