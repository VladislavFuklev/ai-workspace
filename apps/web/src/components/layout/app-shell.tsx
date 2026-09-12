"use client";

import { useEffect, useRef, useState } from "react";

import { Navigation } from "./navigation";

/**
 * The authenticated frame: sidebar beside the content on large screens, a modal
 * drawer below that.
 *
 * The drawer is a native <dialog>. The browser then owns focus trapping, Escape,
 * and making the background inert — three things a hand-written implementation
 * gets subtly wrong. Only opening, closing and returning focus are ours.
 */
export function AppShell({
  header,
  children,
}: {
  header: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  // Escape and backdrop dismissal both fire the dialog's own close event, so this
  // is the single place state and focus are restored.
  const handleClose = () => {
    setOpen(false);
    toggleRef.current?.focus();
  };

  return (
    <div className="min-h-dvh bg-bg">
      <a
        href="#main"
        className="sr-only rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-fg focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-skip-link"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-header h-header border-b border-border bg-surface">
        <div className="flex h-full items-center gap-3 px-4 sm:px-6">
          <button
            ref={toggleRef}
            type="button"
            onClick={() => setOpen(true)}
            aria-expanded={open}
            aria-controls="navigation-drawer"
            className="-ml-1 rounded-md p-2 text-text-muted transition-colors duration-fast hover:bg-surface-muted hover:text-text lg:hidden"
          >
            <span className="sr-only">Open navigation</span>
            <svg aria-hidden="true" viewBox="0 0 20 20" className="size-5" fill="currentColor">
              <path d="M3 5.5h14v1.5H3zM3 9.25h14v1.5H3zM3 13h14v1.5H3z" />
            </svg>
          </button>
          {header}
        </div>
      </header>

      <div className="flex">
        {/* Rendered inline only at lg and up; below that the drawer holds it. */}
        <div className="sticky top-header hidden h-[calc(100dvh-var(--spacing-header))] w-sidebar shrink-0 border-r border-border bg-surface lg:block">
          <Navigation label="Main" />
        </div>

        <main id="main" tabIndex={-1} className="min-w-0 flex-1 focus:outline-none">
          {children}
        </main>
      </div>

      <dialog
        ref={dialogRef}
        id="navigation-drawer"
        onClose={handleClose}
        // A native dialog's click target covers the backdrop, so compare against
        // the element itself to tell a backdrop click from a click inside.
        onClick={(event) => {
          if (event.target === dialogRef.current) dialogRef.current?.close();
        }}
        aria-label="Navigation"
        className="z-drawer m-0 h-dvh max-h-dvh w-drawer max-w-[85vw] border-r border-border bg-surface p-0 text-text backdrop:bg-neutral-950/40 lg:hidden"
      >
        <div className="flex h-header items-center justify-between border-b border-border px-4">
          <span className="text-sm font-semibold tracking-tight text-text">AI Workspace</span>
          <button
            type="button"
            onClick={() => dialogRef.current?.close()}
            className="-mr-1 rounded-md p-2 text-text-muted transition-colors duration-fast hover:bg-surface-muted hover:text-text"
          >
            <span className="sr-only">Close navigation</span>
            <svg aria-hidden="true" viewBox="0 0 20 20" className="size-5" fill="currentColor">
              <path d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L8.94 10l-4.72 4.72a.75.75 0 1 0 1.06 1.06L10 11.06l4.72 4.72a.75.75 0 1 0 1.06-1.06L11.06 10l4.72-4.72a.75.75 0 0 0-1.06-1.06L10 8.94z" />
            </svg>
          </button>
        </div>
        {/* No label here: the dialog already names this region, and a second
            landmark called "Main" would be a duplicate in the accessibility tree. */}
        <Navigation onNavigate={() => dialogRef.current?.close()} />
      </dialog>
    </div>
  );
}
