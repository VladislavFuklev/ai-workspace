import type { ComponentPropsWithoutRef } from "react";

const base =
  "w-full rounded-md border bg-surface px-2.5 py-1.5 text-sm text-text transition-colors duration-fast placeholder:text-text-subtle disabled:cursor-not-allowed disabled:bg-surface-muted disabled:text-text-subtle";

/** Styling only — the accessibility wiring comes from Field. */
export function Input({ className = "", ...props }: ComponentPropsWithoutRef<"input">) {
  return (
    <input
      {...props}
      className={`${base} ${props["aria-invalid"] ? "border-danger" : "border-border-strong"} ${className}`}
    />
  );
}

export function Textarea({ className = "", ...props }: ComponentPropsWithoutRef<"textarea">) {
  return (
    <textarea
      {...props}
      className={`${base} min-h-24 ${props["aria-invalid"] ? "border-danger" : "border-border-strong"} ${className}`}
    />
  );
}
