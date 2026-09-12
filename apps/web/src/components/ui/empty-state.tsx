import type { ReactNode } from "react";

/**
 * What a surface shows when it has nothing yet.
 *
 * The bar: say what this place is, why it is empty, and offer the one action that
 * fills it. "No data" tells the user they have found a dead end.
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-dashed border-border px-6 py-12 text-center">
      {icon ? <div className="mb-3 text-text-subtle">{icon}</div> : null}
      <h2 className="text-sm font-semibold text-text">{title}</h2>
      <p className="mt-1 max-w-sm text-sm text-balance text-text-muted">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
